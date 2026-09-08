"""
Módulo SistemaBiblioteca
Fachada principal (Façade) y controlador del sistema de la Biblioteca Municipal Cordillera.
Centraliza y orquesta todas las reglas de negocio, transacciones, políticas de préstamo y persistencia.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any
from socio import Socio
from usuario import Usuario
from bibliotecaria_atencion import BibliotecariaAtencion
from administradora import Administradora
from material import Material
from libro import Libro
from revista import Revista
from material_multimedia import MaterialMultimedia
from material_extranjero import MaterialExtranjero
from prestamo import Prestamo
from detalle_prestamo import DetallePrestamo
from repositorio_bd import RepositorioBibliotecaBD
from servicio_dolar import ServicioDolarAPI
from excepciones import (
    BibliotecaError,
    SocioConMultaPendienteError,
    MaterialYaPrestadoError,
    MaterialNoEncontradoError,
    SocioNoEncontradoError,
    PrestamoNoEncontradoError,
    PermisoInsuficienteError
)


class SistemaBiblioteca:
    """Fachada integral para la gestión y orquestación de la Biblioteca Municipal Cordillera."""

    def __init__(
        self,
        nombre_biblioteca: str = "Biblioteca Municipal Cordillera",
        repo_bd: Optional[RepositorioBibliotecaBD] = None,
        servicio_dolar: Optional[ServicioDolarAPI] = None
    ):
        self._nombre_biblioteca: str = nombre_biblioteca
        self._catalogo_materiales: Dict[str, Material] = {}
        self._registro_socios: Dict[str, Socio] = {}
        self._registro_prestamos: List[Prestamo] = []
        self._usuarios_sistema: Dict[str, Usuario] = {}
        self._repositorio_bd: RepositorioBibliotecaBD = repo_bd or RepositorioBibliotecaBD()
        self._servicio_dolar: ServicioDolarAPI = servicio_dolar or ServicioDolarAPI()
        self._contador_prestamos: int = 1
        self._contador_socios: int = 1

    @property
    def nombre_biblioteca(self) -> str:
        return self._nombre_biblioteca

    @property
    def catalogo_materiales(self) -> Dict[str, Material]:
        return self._catalogo_materiales

    @property
    def registro_socios(self) -> Dict[str, Socio]:
        return self._registro_socios

    @property
    def registro_prestamos(self) -> List[Prestamo]:
        return list(self._registro_prestamos)

    @property
    def usuarios_sistema(self) -> Dict[str, Usuario]:
        return self._usuarios_sistema

    @property
    def servicio_dolar(self) -> ServicioDolarAPI:
        return self._servicio_dolar

    @property
    def repositorio_bd(self) -> RepositorioBibliotecaBD:
        return self._repositorio_bd

    # ==================== GESTIÓN DE SOCIOS ====================
    def inscribir_socio(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        fecha_inscripcion: Optional[date] = None
    ) -> Socio:
        """
        Inscribe a un nuevo socio en el sistema tras validar su RUT chileno.
        Si ya existía, lo retorna. Persiste la información en BD y bitácora.
        """
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        for s in self._registro_socios.values():
            if s.get_rut().replace(".", "").replace("-", "").strip().upper() == rut_limpio:
                return s

        num_socio = self._contador_socios
        self._contador_socios += 1

        socio = Socio(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email,
            numero_socio=num_socio,
            fecha_inscripcion=fecha_inscripcion
        )
        self._registro_socios[socio.get_rut()] = socio
        self._repositorio_bd.guardar_socio(socio)
        self._repositorio_bd.registrar_auditoria(
            "SISTEMA",
            f"Inscripción de Socio N°{num_socio:04d}: {socio.get_nombre()} ({socio.get_rut()})"
        )
        return socio

    def buscar_socio_por_rut(self, rut: str) -> Socio:
        """Busca un socio registrado por su RUT (soporta diversos formatos)."""
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        for s in self._registro_socios.values():
            if s.get_rut().replace(".", "").replace("-", "").strip().upper() == rut_limpio:
                return s
        raise SocioNoEncontradoError(rut)

    def pagar_multa_socio(self, rut_socio: str, monto: float) -> float:
        """Procesa el pago de multas de un socio."""
        socio = self.buscar_socio_por_rut(rut_socio)
        vuelto = socio.pagar_multa(monto)
        self._repositorio_bd.guardar_socio(socio)
        self._repositorio_bd.registrar_auditoria(
            "CAJA",
            f"Pago de multa para socio {socio.get_rut()} por ${monto:,.0f} CLP (Vuelto: ${vuelto:,.0f})"
        )
        return vuelto

    # ==================== GESTIÓN DE USUARIOS ====================
    def registrar_usuario(self, usuario: Usuario) -> Usuario:
        """Registra un empleado en el sistema y sincroniza con BD."""
        self._usuarios_sistema[usuario.username] = usuario
        self._repositorio_bd.guardar_usuario(usuario)
        self._repositorio_bd.registrar_auditoria(
            "SISTEMA",
            f"Registro de Usuario @{usuario.username} ({usuario.rol}) - {usuario.get_nombre()}"
        )
        return usuario

    def autenticar_usuario(self, username: str, password: str) -> Optional[Usuario]:
        """Valida credenciales de acceso para un usuario del personal."""
        user = self._usuarios_sistema.get(username.strip().lower())
        if user and user.autenticar(password):
            return user
        return None

    # ==================== GESTIÓN DE CATÁLOGO ====================
    def alta_nuevo_material(self, usuario_admin: Usuario, material: Material) -> None:
        """
        Segregación de funciones: Solo usuarios con rol Administradora pueden dar de alta ítems.
        """
        if not isinstance(usuario_admin, Administradora) and not usuario_admin.tiene_permiso("dar_alta_material"):
            raise PermisoInsuficienteError(usuario_admin.username, "dar_alta_material")

        cod = material.codigo
        self._catalogo_materiales[cod] = material
        self._repositorio_bd.guardar_material(material)
        self._repositorio_bd.registrar_auditoria(
            usuario_admin.username,
            f"Alta de material {cod} - '{material.titulo}' ({material.__class__.__name__})"
        )

    def baja_material(self, usuario_admin: Usuario, cod_mat: str) -> None:
        """
        Segregación de funciones: Solo Administradora puede retirar materiales del catálogo.
        """
        if not isinstance(usuario_admin, Administradora) and not usuario_admin.tiene_permiso("eliminar_material"):
            raise PermisoInsuficienteError(usuario_admin.username, "eliminar_material")

        cod = cod_mat.strip().upper()
        if cod not in self._catalogo_materiales:
            raise MaterialNoEncontradoError(cod)

        mat = self._catalogo_materiales.pop(cod)
        self._repositorio_bd.eliminar_material(cod)
        self._repositorio_bd.registrar_auditoria(
            usuario_admin.username,
            f"Baja de material {cod} - '{mat.titulo}'"
        )

    def buscar_material(self, cod_mat: str) -> Material:
        """Consulta un material en el catálogo."""
        cod = cod_mat.strip().upper()
        if cod not in self._catalogo_materiales:
            raise MaterialNoEncontradoError(cod)
        return self._catalogo_materiales[cod]

    # ==================== OPERACIONES DE PRÉSTAMOS ====================
    def crear_prestamo(
        self,
        rut_socio: str,
        cods_materiales: List[str],
        usuario_atencion: Usuario,
        fecha_prestamo: Optional[datetime] = None
    ) -> Prestamo:
        """
        Crea un nuevo préstamo múltiple:
        1. Valida permisos del usuario de atención.
        2. Verifica que el socio no tenga multas pendientes (Regla Infranqueable N°1).
        3. Verifica que todos los materiales existan y estén disponibles (Regla Infranqueable N°2).
        4. Construye la cabecera y detalles, marcando los materiales como prestados.
        5. Persiste en SQLite y genera auditoría.
        """
        if not usuario_atencion.tiene_permiso("registrar_prestamo"):
            raise PermisoInsuficienteError(usuario_atencion.username, "registrar_prestamo")

        socio = self.buscar_socio_por_rut(rut_socio)
        if not socio.puede_solicitar_prestamo():
            raise SocioConMultaPendienteError(socio.get_rut(), socio.monto_multa_acumulada)

        if not cods_materiales:
            raise BibliotecaError("Debe incluir al menos un material para generar un préstamo.")

        # Validar disponibilidad de cada material antes de comprometer el préstamo
        materiales_a_prestar: List[Material] = []
        for cod in cods_materiales:
            mat = self.buscar_material(cod)
            if mat.esta_prestado():
                raise MaterialYaPrestadoError(mat.codigo)
            materiales_a_prestar.append(mat)

        id_p = self._contador_prestamos
        self._contador_prestamos += 1

        bibliotecaria = (
            usuario_atencion if isinstance(usuario_atencion, BibliotecariaAtencion)
            else BibliotecariaAtencion(
                rut=usuario_atencion.get_rut(),
                nombre_completo=usuario_atencion.get_nombre(),
                telefono=usuario_atencion.telefono,
                email=usuario_atencion.email,
                username=usuario_atencion.username,
                password="TempPassword*",
                turno="General"
            )
        )

        prestamo = Prestamo(
            id_prestamo=id_p,
            socio=socio,
            bibliotecaria=bibliotecaria,
            fecha_prestamo=fecha_prestamo or datetime.now()
        )

        fecha_ini = prestamo.fecha_prestamo.date()
        for mat in materiales_a_prestar:
            prestamo.agregar_item(mat, fecha_inicio=fecha_ini)

        self._registro_prestamos.append(prestamo)
        self._repositorio_bd.guardar_prestamo(prestamo)
        self._repositorio_bd.registrar_auditoria(
            usuario_atencion.username,
            f"Préstamo N°{id_p:04d} otorgado a {socio.get_rut()} ({len(materiales_a_prestar)} materiales)"
        )
        return prestamo

    def procesar_devolucion(
        self,
        id_prestamo: int,
        cod_mat: str,
        usuario_atencion: Usuario,
        fecha_devolucion: Optional[date] = None
    ) -> None:
        """
        Procesa la recepción y devolución de un material particular de un préstamo.
        Calcula posibles multas por mora y actualiza BD.
        """
        if not usuario_atencion.tiene_permiso("registrar_devolucion"):
            raise PermisoInsuficienteError(usuario_atencion.username, "registrar_devolucion")

        prestamo = self._buscar_prestamo(id_prestamo)
        prestamo.registrar_devolucion_item(cod_mat, fecha_devolucion)
        
        self._repositorio_bd.guardar_prestamo(prestamo)
        self._repositorio_bd.registrar_auditoria(
            usuario_atencion.username,
            f"Devolución de ítem {cod_mat} en préstamo N°{id_prestamo:04d}"
        )

    def renovar_material_prestamo(
        self,
        id_prestamo: int,
        cod_mat: str,
        usuario_atencion: Optional[Usuario] = None
    ) -> bool:
        """
        Aplica una renovación a un ítem dentro de un préstamo, respetando las políticas
        específicas del tipo de material (Libros sí, Revistas y Multimedia no).
        """
        if usuario_atencion and not usuario_atencion.tiene_permiso("renovar_material"):
            raise PermisoInsuficienteError(usuario_atencion.username, "renovar_material")

        prestamo = self._buscar_prestamo(id_prestamo)
        exito = prestamo.renovar_item(cod_mat)
        if exito:
            self._repositorio_bd.guardar_prestamo(prestamo)
            usuario_log = usuario_atencion.username if usuario_atencion else "ATENCION"
            self._repositorio_bd.registrar_auditoria(
                usuario_log,
                f"Renovación autorizada de material {cod_mat} en préstamo N°{id_prestamo:04d}"
            )
        return exito

    def condonar_multa_socio(
        self,
        usuario_admin: Usuario,
        rut_socio: str,
        motivo: str = "Condonación administrativa autorizada"
    ) -> None:
        """
        Segregación de funciones: Solo Administradora puede condonar deudas/multas.
        """
        if not isinstance(usuario_admin, Administradora) and not usuario_admin.tiene_permiso("condonar_multa"):
            raise PermisoInsuficienteError(usuario_admin.username, "condonar_multa")

        socio = self.buscar_socio_por_rut(rut_socio)
        monto_exonerado = socio.monto_multa_acumulada
        socio.condonar_multa()
        self._repositorio_bd.guardar_socio(socio)
        self._repositorio_bd.registrar_auditoria(
            usuario_admin.username,
            f"Condonación de ${monto_exonerado:,.0f} CLP al socio {socio.get_rut()}. Motivo: {motivo}"
        )

    def registrar_perdida_material(self, rut_socio: str, cod_mat: str) -> float:
        """
        Calcula el valor de reposición del material extraviado (cotizado en USD con API Dólar si es extranjero),
        lo carga como multa al socio y retira el ejemplar del inventario activo.
        """
        socio = self.buscar_socio_por_rut(rut_socio)
        material = self.buscar_material(cod_mat)

        if isinstance(material, MaterialExtranjero):
            valor_dolar = self._servicio_dolar.obtener_valor_dolar()
            costo_reposicion = material.calcular_valor_reposicion(valor_dolar)
        else:
            costo_reposicion = material.calcular_valor_reposicion()

        socio.registrar_multa(costo_reposicion)
        self._repositorio_bd.guardar_socio(socio)
        self._repositorio_bd.actualizar_estado_material(cod_mat, prestado=False)
        self._repositorio_bd.registrar_auditoria(
            "SISTEMA",
            f"Pérdida de material {cod_mat} reportada para socio {socio.get_rut()}. "
            f"Cargo generado: ${costo_reposicion:,.0f} CLP"
        )
        return costo_reposicion

    def guardar_estado_bd(self) -> bool:
        """Sincroniza todos los socios, catálogo y préstamos en la base de datos."""
        exito = True
        for socio in self._registro_socios.values():
            if not self._repositorio_bd.guardar_socio(socio):
                exito = False
        for mat in self._catalogo_materiales.values():
            if not self._repositorio_bd.guardar_material(mat):
                exito = False
        for p in self._registro_prestamos:
            if not self._repositorio_bd.guardar_prestamo(p):
                exito = False
        return exito

    def _buscar_prestamo(self, id_prestamo: int) -> Prestamo:
        for p in self._registro_prestamos:
            if p.id_prestamo == id_prestamo:
                return p
        raise PrestamoNoEncontradoError(id_prestamo)
