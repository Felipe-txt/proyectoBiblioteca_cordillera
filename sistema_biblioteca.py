"""
========================================================================================
MÓDULO: sistema_biblioteca.py
ROL EN EL PROYECTO:
    Controlador Principal y Fachada del Sistema (Design Pattern Façade / Controller).
    
    En el diagrama UML, SistemaBiblioteca es el corazón operativo que centraliza
    y orquesta todos los flujos de trabajo de la institución:
    
            ┌──────────────────────────────────────────────────────────┐
            │                     SistemaBiblioteca                    │
            │                  (Fachada / Controlador)                 │
            └─────────┬──────────────┬──────────────┬──────────────┬───┘
                      │              │              │              │
                 Catálogo de      Registro       Registro      Seguridad
                  Materiales      de Socios    de Préstamos    y Usuarios
                      │              │              │              │
                      ▼              ▼              ▼              ▼
            ┌──────────────────────────────────────────────────────────┐
            │                 RepositorioBibliotecaBD                  │
            │                     (SQLite Database)                    │
            └──────────────────────────────────────────────────────────┘
            
    Responsabilidades Principales:
    - Centralizar las colecciones en memoria (catálogo, socios, préstamos, usuarios).
    - Orquestar los casos de uso: inscripción, alta/baja de catálogo, creación de préstamos,
      devoluciones, prórrogas, condonación de multas y reporte de extravíos en USD.
    - Garantizar el cumplimiento estricto de las 4 Reglas Infranqueables del Negocio.
    - Sincronizar automáticamente cada evento con la base de datos y la bitácora.
    
    Excepciones Disparadas y Orquestadas:
    - PermisoInsuficienteError: Si el usuario carece de rango para la acción.
    - SocioConMultaPendienteError: Si el socio registra sanciones monetarias pendientes.
    - MaterialYaPrestadoError: Si se intenta retirar un ejemplar no disponible.
    - SocioNoEncontradoError: Si el RUT no existe en la nómina.
    - MaterialNoEncontradoError: Si el código no está en el catálogo.
    - PrestamoNoEncontradoError: Si el ID de préstamo no existe.
    - RenovacionNoPermitidaError: Si el material no admite renovación o expiró el cupo.
========================================================================================
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
    """
    Fachada integral para la gestión y orquestación de la Biblioteca Municipal Cordillera.
    """

    def __init__(
        self,
        nombre_biblioteca: str = "Biblioteca Municipal Cordillera",
        repo_bd: Optional[RepositorioBibliotecaBD] = None,
        servicio_dolar: Optional[ServicioDolarAPI] = None
    ):
        self._nombre_biblioteca: str = nombre_biblioteca
        # Almacenamiento rápido en memoria (caché operativa del controlador)
        self._catalogo_materiales: Dict[str, Material] = {}
        self._registro_socios: Dict[str, Socio] = {}
        self._registro_prestamos: List[Prestamo] = []
        self._usuarios_sistema: Dict[str, Usuario] = {}
        # Servicios auxiliares de persistencia y tipo de cambio
        self._repositorio_bd: RepositorioBibliotecaBD = repo_bd or RepositorioBibliotecaBD()
        self._servicio_dolar: ServicioDolarAPI = servicio_dolar or ServicioDolarAPI()
        # Contadores correlativos para identificadores
        self._contador_prestamos: int = 1
        self._contador_socios: int = 1

    # ==================== PROPIEDADES (GETTERS) ====================
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

    # ==================== CASOS DE USO: GESTIÓN DE SOCIOS ====================
    def inscribir_socio(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        fecha_inscripcion: Optional[date] = None
    ) -> Socio:
        """
        Inscribe a un nuevo socio en el sistema.
        
        Validación:
        - Si el RUT no cumple Módulo 11, la clase Socio/Persona lanzará RutInvalidoError.
        - Si el socio ya existía, lo retorna evitando duplicados.
        - Persiste el registro en SQLite y asienta el evento en log_auditoria.
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
        """
        Consulta un socio en el registro activo.
        Si no se localiza, lanza SocioNoEncontradoError.
        """
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        for s in self._registro_socios.values():
            if s.get_rut().replace(".", "").replace("-", "").strip().upper() == rut_limpio:
                return s
        raise SocioNoEncontradoError(rut)

    def pagar_multa_socio(self, rut_socio: str, monto: float) -> float:
        """
        Procesa el pago de multas acumuladas. Si la deuda queda en $0, el socio
        queda automáticamente habilitado para volver a retirar libros.
        """
        socio = self.buscar_socio_por_rut(rut_socio)
        vuelto = socio.pagar_multa(monto)
        self._repositorio_bd.guardar_socio(socio)
        self._repositorio_bd.registrar_auditoria(
            "CAJA",
            f"Pago de multa para socio {socio.get_rut()} por ${monto:,.0f} CLP (Vuelto: ${vuelto:,.0f})"
        )
        return vuelto

    # ==================== CASOS DE USO: USUARIOS Y AUTENTICACIÓN ====================
    def registrar_usuario(self, usuario: Usuario) -> Usuario:
        """Registra un funcionario en el sistema y persiste en base de datos."""
        self._usuarios_sistema[usuario.username] = usuario
        self._repositorio_bd.guardar_usuario(usuario)
        self._repositorio_bd.registrar_auditoria(
            "SISTEMA",
            f"Registro de Usuario @{usuario.username} ({usuario.rol}) - {usuario.get_nombre()}"
        )
        return usuario

    def autenticar_usuario(self, username: str, password: str) -> Optional[Usuario]:
        """Comprueba credenciales comparando hashes SHA-256."""
        user = self._usuarios_sistema.get(username.strip().lower())
        if user and user.autenticar(password):
            return user
        return None

    # ==================== CASOS DE USO: CATÁLOGO DE MATERIALES ====================
    def alta_nuevo_material(self, usuario_admin: Usuario, material: Material) -> None:
        """
        Regla Infranqueable N°4 (Segregación de Roles):
        Solo un usuario con rol 'ADMINISTRADORA' puede dar de alta nuevos ejemplares.
        Si una bibliotecaria intenta hacerlo, lanza PermisoInsuficienteError.
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
        Regla Infranqueable N°4 (Segregación de Roles):
        Solo 'ADMINISTRADORA' puede retirar ejemplares de circulación.
        Si el material no existe, lanza MaterialNoEncontradoError.
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
        """Consulta un material en el catálogo institucional."""
        cod = cod_mat.strip().upper()
        if cod not in self._catalogo_materiales:
            raise MaterialNoEncontradoError(cod)
        return self._catalogo_materiales[cod]

    # ==================== CASOS DE USO: TRANSACCIÓN DE PRÉSTAMOS ====================
    def crear_prestamo(
        self,
        rut_socio: str,
        cods_materiales: List[str],
        usuario_atencion: Usuario,
        fecha_prestamo: Optional[datetime] = None
    ) -> Prestamo:
        """
        Orquesta la transacción completa de préstamo múltiple:
        
        Etapas de Control:
        1. Seguridad: Valida permiso 'registrar_prestamo'.
        2. Regla Infranqueable N°1: Verifica que el socio no mantenga multas pendientes.
           Si registra mora -> Lanza SocioConMultaPendienteError.
        3. Valida que la lista de códigos solicitados no esté vacía.
        4. Regla Infranqueable N°2: Verifica que cada material exista y esté disponible.
           Si alguno ya está prestado -> Lanza MaterialYaPrestadoError.
        5. Construye la cabecera Prestamo y agrega cada ítem DetallePrestamo.
        6. Persiste en SQLite y asienta en log_auditoria.
        """
        if not usuario_atencion.tiene_permiso("registrar_prestamo"):
            raise PermisoInsuficienteError(usuario_atencion.username, "registrar_prestamo")

        socio = self.buscar_socio_por_rut(rut_socio)
        if not socio.puede_solicitar_prestamo():
            raise SocioConMultaPendienteError(socio.get_rut(), socio.monto_multa_acumulada)

        if not cods_materiales:
            raise BibliotecaError("Debe incluir al menos un material para generar un préstamo.")

        # Verificación previa de disponibilidad de todos los materiales pedidos
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
        Recepciona un ítem devuelto por el socio.
        Si hubo atraso respecto a la fecha esperada, carga la multa automáticamente en BD.
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
        Aplica una renovación sobre el ítem solicitado.
        Aplica las reglas polimórficas (Libros hasta 1, Revistas y DVDs 0).
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
        Regla Infranqueable N°4 (Segregación de Roles):
        Solo Administradora puede perdonar o condonar multas a un socio.
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
        Procesa el reporte de extravío de un ejemplar.
        
        Cálculo del costo de reposición:
        - Si es MaterialExtranjero: Consulta la API del Dólar Observado y calcula:
          Costo = Precio USD * (1 + 0.06 Arancel Aduanero) * Cotización Dólar.
        - Si es Material nacional: Aplica el precio_base_reposicion en CLP.
        
        Aplica el cobro como multa al socio y lo suspende hasta que pague.
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
        """Sincroniza masivamente la totalidad de socios, catálogo y préstamos en SQLite."""
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
        """Busca una transacción de préstamo por ID o lanza PrestamoNoEncontradoError."""
        for p in self._registro_prestamos:
            if p.id_prestamo == id_prestamo:
                return p
        raise PrestamoNoEncontradoError(id_prestamo)
