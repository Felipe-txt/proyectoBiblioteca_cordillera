"""
========================================================================================
MÓDULO: sistema_biblioteca.py
ROL EN EL PROYECTO:
    Controlador Principal y Fachada del Sistema (Design Pattern Façade / Controller).
    
    Orquesta todos los flujos de trabajo de la Biblioteca Cordillera integrando:
    - Dominio POO (model)
    - Acceso a Datos Relacional (dao) y Persistencia JSON (JsonDao)
    - Integración de Servicios Externos (api)
========================================================================================
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any
try:
    from model.socio import Socio
    from model.usuario import Usuario
    from model.bibliotecaria_atencion import BibliotecariaAtencion
    from model.administradora import Administradora
    from model.material import Material
    from model.libro import Libro
    from model.revista import Revista
    from model.material_multimedia import MaterialMultimedia
    from model.material_extranjero import MaterialExtranjero
    from model.prestamo import Prestamo
    from model.detalle_prestamo import DetallePrestamo
    from model.boleta import Boleta, LineaDetalleBoleta
    from model.excepciones import (
        BibliotecaError,
        SocioConMultaPendienteError,
        MaterialYaPrestadoError,
        MaterialNoEncontradoError,
        SocioNoEncontradoError,
        PrestamoNoEncontradoError,
        PermisoInsuficienteError
    )
    from dao.json_dao import JsonDao
    from dao.material_dao import MaterialDao
    from dao.socio_dao import SocioDao
    from dao.usuario_dao import UsuarioDao
    from dao.libro_dao import LibroDao
    from dao.revista_dao import RevistaDao
    from dao.multimedia_dao import MultimediaDao
    from dao.extranjero_dao import ExtranjeroDao
    from dao.prestamo_dao import PrestamoDao
    from dao.boleta_dao import BoletaDao
    from api.servicio_dolar import ServicioDolarAPI
    import conectar
except ImportError:
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
    from boleta import Boleta, LineaDetalleBoleta
    from excepciones import (
        BibliotecaError,
        SocioConMultaPendienteError,
        MaterialYaPrestadoError,
        MaterialNoEncontradoError,
        SocioNoEncontradoError,
        PrestamoNoEncontradoError,
        PermisoInsuficienteError
    )
    from json_dao import JsonDao
    from material_dao import MaterialDao
    from socio_dao import SocioDao
    from usuario_dao import UsuarioDao
    from libro_dao import LibroDao
    from revista_dao import RevistaDao
    from multimedia_dao import MultimediaDao
    from extranjero_dao import ExtranjeroDao
    from prestamo_dao import PrestamoDao
    from boleta_dao import BoletaDao
    from servicio_dolar import ServicioDolarAPI
    import conectar


class SistemaBiblioteca:
    """
    Fachada integral para la gestión y orquestación de la Biblioteca Municipal Cordillera.
    """

    def __init__(
        self,
        nombre_biblioteca: str = "Biblioteca Municipal Cordillera",
        repo_bd: Optional[Any] = None,
        servicio_dolar: Optional[ServicioDolarAPI] = None,
        archivo_json: str = "biblioteca_db.json"
    ):
        self._nombre_biblioteca: str = nombre_biblioteca
        # Almacenamiento en memoria (caché operativa del controlador)
        self._catalogo_materiales: Dict[str, Material] = {}
        self._registro_socios: Dict[str, Socio] = {}
        self._registro_prestamos: List[Prestamo] = []
        self._registro_boletas: List[Boleta] = []
        self._usuarios_sistema: Dict[str, Usuario] = {}
        
        # Servicios auxiliares de persistencia y API
        if repo_bd is not None:
            self._repositorio_bd = repo_bd
            self._conn = getattr(repo_bd, "_persistent_conn", None) or getattr(repo_bd, "_get_connection", lambda: None)()
        else:
            try:
                from repositorio_bd import RepositorioBibliotecaBD
                self._repositorio_bd = RepositorioBibliotecaBD()
                self._conn = self._repositorio_bd._get_connection()
            except Exception:
                self._conn = conectar.crear_conexion()
                self._repositorio_bd = None
                
        self._servicio_dolar: ServicioDolarAPI = servicio_dolar or ServicioDolarAPI()
        self._json_dao: JsonDao = JsonDao(archivo_json)
        
        # Contadores correlativos
        self._contador_prestamos: int = 1
        self._contador_socios: int = 1
        self._contador_boletas: int = 1

        # DAOs dedicados
        if self._conn:
            self._material_dao = MaterialDao(self._conn)
            self._socio_dao = SocioDao(self._conn)
            self._usuario_dao = UsuarioDao(self._conn)
            self._libro_dao = LibroDao(self._conn)
            self._revista_dao = RevistaDao(self._conn)
            self._multimedia_dao = MultimediaDao(self._conn)
            self._extranjero_dao = ExtranjeroDao(self._conn)
            self._prestamo_dao = PrestamoDao(self._conn)
            self._boleta_dao = BoletaDao(self._conn)

            # Inicializar tablas y cargar datos existentes desde SQLite
            conectar.inicializar_base_datos(self._conn)
            self.cargar_datos_desde_bd()

        # Si no hay materiales cargados y no es una prueba temporal en memoria, sembramos datos
        es_memoria = getattr(self._repositorio_bd, "_is_memory", False)
        if len(self._catalogo_materiales) == 0 and len(self._registro_socios) == 0 and not es_memoria:
            self.sembrar_datos_iniciales()

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
    def registro_boletas(self) -> List[Boleta]:
        return list(self._registro_boletas)

    @property
    def usuarios_sistema(self) -> Dict[str, Usuario]:
        return self._usuarios_sistema

    @property
    def servicio_dolar(self) -> ServicioDolarAPI:
        return self._servicio_dolar

    @property
    def repositorio_bd(self) -> Any:
        return self._repositorio_bd

    @property
    def json_dao(self) -> JsonDao:
        return self._json_dao

    # ==================== CASOS DE USO: GESTIÓN DE SOCIOS ====================
    def inscribir_socio(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str = "",
        email: str = "",
        fecha_inscripcion: Optional[date] = None
    ) -> Socio:
        """
        Inscribe a un nuevo socio en el sistema.
        Valida RUT con Módulo 11, persiste en SQLite y actualiza la caché en memoria.
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
        
        if hasattr(self, "_socio_dao"):
            self._socio_dao.guardar(socio)
            
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_socio"):
            self._repositorio_bd.guardar_socio(socio)
            if hasattr(self._repositorio_bd, "registrar_auditoria"):
                self._repositorio_bd.registrar_auditoria(
                    "SISTEMA",
                    f"Inscripción de Socio N°{num_socio:04d}: {socio.get_nombre()} ({socio.get_rut()})"
                )
            
        return socio

    def buscar_socio_por_rut(self, rut: str) -> Socio:
        """Consulta un socio en el registro activo. Lanza SocioNoEncontradoError si no existe."""
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        for s in self._registro_socios.values():
            if s.get_rut().replace(".", "").replace("-", "").strip().upper() == rut_limpio:
                return s
        # Búsqueda de rescate en la BD mediante DAO
        if hasattr(self, "_socio_dao"):
            s_db = self._socio_dao.obtener_por_rut(rut)
            if s_db:
                self._registro_socios[s_db.get_rut().replace(".", "").replace("-", "").strip().upper()] = s_db
                return s_db
        raise SocioNoEncontradoError(rut)

    def registrar_multa_socio(self, rut_socio: str, monto: float) -> float:
        """Registra una multa impaga al socio y actualiza en SQLite inmediatamente (P14)."""
        socio = self.buscar_socio_por_rut(rut_socio)
        socio.registrar_multa(monto)
        if hasattr(self, "_socio_dao"):
            self._socio_dao.guardar(socio)
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_socio"):
            self._repositorio_bd.guardar_socio(socio)
        return socio.monto_multa_acumulada

    def pagar_multa_socio(self, rut_socio: str, monto: float) -> float:
        """Procesa el pago de multas acumuladas."""
        socio = self.buscar_socio_por_rut(rut_socio)
        vuelto = socio.pagar_multa(monto)
        if hasattr(self, "_socio_dao"):
            self._socio_dao.guardar(socio)
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_socio"):
            self._repositorio_bd.guardar_socio(socio)
        return vuelto

    def eliminar_socio(self, rut_socio: str) -> None:
        """Elimina un socio del sistema y de la base de datos (CRUD Completo)."""
        socio = self.buscar_socio_por_rut(rut_socio)
        rut_limpio = socio.get_rut().replace(".", "").replace("-", "").strip().upper()
        self._registro_socios.pop(rut_limpio, None)
        if hasattr(self, "_socio_dao"):
            self._socio_dao.eliminar_por_rut(rut_socio)

    # ==================== CASOS DE USO: USUARIOS Y AUTENTICACIÓN ====================
    def registrar_usuario(self, usuario: Usuario) -> Usuario:
        """Registra un funcionario en el sistema y persiste en base de datos."""
        self._usuarios_sistema[usuario.username.lower()] = usuario
        if hasattr(self, "_usuario_dao"):
            self._usuario_dao.guardar(usuario)
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_usuario"):
            self._repositorio_bd.guardar_usuario(usuario)
            if hasattr(self._repositorio_bd, "registrar_auditoria"):
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
        Regla Infranqueable N°4: Solo Administradora puede dar de alta nuevos ejemplares.
        Persiste en SQLite usando el DAO correspondiente (Table-per-type).
        """
        if not isinstance(usuario_admin, Administradora) and not usuario_admin.tiene_permiso("dar_alta_material"):
            raise PermisoInsuficienteError(usuario_admin.username, "dar_alta_material")

        cod = material.codigo
        self._catalogo_materiales[cod] = material
        
        # Persistencia en BD mediante DAO
        if hasattr(self, "_libro_dao"):
            if isinstance(material, Libro):
                self._libro_dao.guardar(material)
            elif isinstance(material, Revista):
                self._revista_dao.guardar(material)
            elif isinstance(material, MaterialMultimedia):
                self._multimedia_dao.guardar(material)
            elif isinstance(material, MaterialExtranjero):
                self._extranjero_dao.guardar(material)
            elif hasattr(self, "_material_dao"):
                self._material_dao.guardar_base(material, "GENERAL")

        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_material"):
            self._repositorio_bd.guardar_material(material)
            if hasattr(self._repositorio_bd, "registrar_auditoria"):
                self._repositorio_bd.registrar_auditoria(
                    usuario_admin.username,
                    f"Alta de material {cod} - '{material.titulo}' ({material.__class__.__name__})"
                )

    def modificar_material(
        self,
        usuario_admin: Usuario,
        cod_mat: str,
        nuevo_titulo: Optional[str] = None,
        nuevo_precio: Optional[float] = None
    ) -> Material:
        """
        Modifica los datos de un material existente y actualiza la BD SQLite (P04).
        """
        if not isinstance(usuario_admin, Administradora) and not usuario_admin.tiene_permiso("modificar_material"):
            raise PermisoInsuficienteError(usuario_admin.username, "modificar_material")

        cod = cod_mat.strip().upper()
        if cod not in self._catalogo_materiales:
            raise MaterialNoEncontradoError(cod)

        mat = self._catalogo_materiales[cod]
        if nuevo_titulo:
            mat.titulo = nuevo_titulo
        if nuevo_precio is not None:
            mat.precio_base_reposicion = nuevo_precio

        # Actualizar en BD mediante el DAO correspondiente
        if isinstance(mat, Libro) and hasattr(self, "_libro_dao"):
            self._libro_dao.guardar(mat)
        elif isinstance(mat, Revista) and hasattr(self, "_revista_dao"):
            self._revista_dao.guardar(mat)
        elif isinstance(mat, MaterialMultimedia) and hasattr(self, "_multimedia_dao"):
            self._multimedia_dao.guardar(mat)
        elif isinstance(mat, MaterialExtranjero) and hasattr(self, "_extranjero_dao"):
            self._extranjero_dao.guardar(mat)
        elif hasattr(self, "_material_dao"):
            self._material_dao.modificar_titulo(cod, mat.titulo)

        if self._repositorio_bd and hasattr(self._repositorio_bd, "registrar_auditoria"):
            self._repositorio_bd.registrar_auditoria(
                usuario_admin.username,
                f"Modificación de material {cod} - Nuevo título: '{mat.titulo}'"
            )

        return mat

    def baja_material(self, usuario_admin: Usuario, cod_mat: str) -> None:
        """
        Regla N°4: Solo Administradora puede retirar ejemplares (P06).
        Elimina el registro de la memoria y de la base de datos SQLite en cascada.
        """
        if not isinstance(usuario_admin, Administradora) and not usuario_admin.tiene_permiso("eliminar_material"):
            raise PermisoInsuficienteError(usuario_admin.username, "eliminar_material")

        cod = cod_mat.strip().upper()
        if cod not in self._catalogo_materiales:
            raise MaterialNoEncontradoError(cod)

        mat = self._catalogo_materiales.pop(cod)
        if hasattr(self, "_material_dao"):
            self._material_dao.eliminar_por_codigo(cod)
        elif hasattr(self, "_libro_dao"):
            self._libro_dao.eliminar_por_codigo(cod)

        if self._repositorio_bd and hasattr(self._repositorio_bd, "eliminar_material"):
            self._repositorio_bd.eliminar_material(cod)
        if self._repositorio_bd and hasattr(self._repositorio_bd, "registrar_auditoria"):
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

    # ==================== CASOS DE USO: PRÉSTAMOS Y PEDIDOS ====================
    def crear_prestamo(
        self,
        rut_socio: str,
        cods_materiales: List[str],
        usuario_atencion: Usuario,
        fecha_prestamo: Optional[datetime] = None
    ) -> Prestamo:
        """
        Crea un préstamo de uno o varios materiales para un socio habilitado.
        """
        if not usuario_atencion.tiene_permiso("registrar_prestamo"):
            raise PermisoInsuficienteError(usuario_atencion.username, "registrar_prestamo")

        socio = self.buscar_socio_por_rut(rut_socio)
        if not socio.puede_solicitar_prestamo():
            raise SocioConMultaPendienteError(socio.get_rut(), socio.monto_multa_acumulada)

        if not cods_materiales:
            raise BibliotecaError("Debe incluir al menos un material para generar un préstamo.")

        materiales_a_prestar: List[Material] = []
        for cod in cods_materiales:
            mat = self.buscar_material(cod)
            if mat.esta_prestado():
                raise MaterialYaPrestadoError(mat.codigo, mat.titulo)
            materiales_a_prestar.append(mat)

        id_p = self._contador_prestamos
        self._contador_prestamos += 1

        bibliotecaria = (
            usuario_atencion if isinstance(usuario_atencion, (BibliotecariaAtencion, Administradora))
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
        
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_prestamo"):
            self._repositorio_bd.guardar_prestamo(prestamo)
            if hasattr(self._repositorio_bd, "registrar_auditoria"):
                self._repositorio_bd.registrar_auditoria(
                    usuario_atencion.username,
                    f"Préstamo N°{id_p:04d} otorgado a {socio.get_rut()} ({len(materiales_a_prestar)} materiales)"
                )
        elif hasattr(self, "_prestamo_dao"):
            self._prestamo_dao.guardar(prestamo)
            
        return prestamo

    def crear_prestamo_multiple(
        self,
        rut_socio: str,
        username_bibliotecaria: str,
        codigos_materiales: List[str]
    ) -> Prestamo:
        """Alias amigable para crear un préstamo o pedido de libros."""
        user = self._usuarios_sistema.get(username_bibliotecaria.strip().lower())
        if not user:
            raise BibliotecaError(f"Usuario '{username_bibliotecaria}' no encontrado.")
        return self.crear_prestamo(rut_socio, codigos_materiales, user)

    def procesar_devolucion(
        self,
        id_prestamo: int,
        cod_mat: str,
        usuario_atencion: Usuario,
        fecha_devolucion: Optional[date] = None
    ) -> None:
        """Recepciona un ítem devuelto por el socio y calcula multas por mora si las hubiera."""
        if not usuario_atencion.tiene_permiso("registrar_devolucion"):
            raise PermisoInsuficienteError(usuario_atencion.username, "registrar_devolucion")

        prestamo = self._buscar_prestamo(id_prestamo)
        prestamo.registrar_devolucion_item(cod_mat, fecha_devolucion)
        
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_prestamo"):
            self._repositorio_bd.guardar_prestamo(prestamo)
        elif hasattr(self, "_prestamo_dao"):
            self._prestamo_dao.guardar(prestamo)

    def renovar_material_prestamo(
        self,
        id_prestamo: int,
        cod_mat: str,
        usuario_atencion: Optional[Usuario] = None
    ) -> bool:
        """Aplica una renovación sobre el ítem solicitado siguiendo las reglas de negocio."""
        if usuario_atencion and not usuario_atencion.tiene_permiso("renovar_material"):
            raise PermisoInsuficienteError(usuario_atencion.username, "renovar_material")

        prestamo = self._buscar_prestamo(id_prestamo)
        exito = prestamo.renovar_item(cod_mat)
        if exito:
            if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_prestamo"):
                self._repositorio_bd.guardar_prestamo(prestamo)
            elif hasattr(self, "_prestamo_dao"):
                self._prestamo_dao.guardar(prestamo)
        return exito

    def condonar_multa_socio(
        self,
        usuario_admin: Usuario,
        rut_socio: str,
        motivo: str = "Condonación administrativa autorizada"
    ) -> None:
        """Regla N°4: Solo Administradora puede condonar multas."""
        if not isinstance(usuario_admin, Administradora) and not usuario_admin.tiene_permiso("condonar_multa"):
            raise PermisoInsuficienteError(usuario_admin.username, "condonar_multa")

        socio = self.buscar_socio_por_rut(rut_socio)
        monto_exonerado = socio.monto_multa_acumulada
        socio.condonar_multa()
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_socio"):
            self._repositorio_bd.guardar_socio(socio)
        elif hasattr(self, "_socio_dao"):
            self._socio_dao.guardar(socio)

    def registrar_perdida_material(self, rut_socio: str, cod_mat: str) -> float:
        """Reporta extravío de material aplicando cotización Dólar API si es extranjero."""
        socio = self.buscar_socio_por_rut(rut_socio)
        material = self.buscar_material(cod_mat)

        if isinstance(material, MaterialExtranjero):
            valor_dolar = self._servicio_dolar.obtener_valor_dolar()
            costo_reposicion = material.calcular_costo_reposicion(valor_dolar)
        else:
            costo_reposicion = material.calcular_costo_reposicion()

        socio.registrar_multa(costo_reposicion)
        if self._repositorio_bd and hasattr(self._repositorio_bd, "guardar_socio"):
            self._repositorio_bd.guardar_socio(socio)
            if hasattr(self._repositorio_bd, "actualizar_estado_material"):
                self._repositorio_bd.actualizar_estado_material(cod_mat, prestado=False)
        elif hasattr(self, "_socio_dao"):
            self._socio_dao.guardar(socio)
            if hasattr(self, "_libro_dao"):
                self._libro_dao.actualizar_estado_prestado(cod_mat, False)
                
        return costo_reposicion

    # ==================== CASOS DE USO: BOLETAS Y ÓRDENES DE TRABAJO ====================
    def generar_boleta_cobro(
        self,
        rut_socio: str,
        username_usuario: str,
        tipo: str = "BOLETA_PRESTAMO",
        descripcion: str = "Comprobante de atención bibliotecaria",
        prestamo_id: Optional[int] = None,
        iva_pct: float = 0.0,
        descuento: float = 0.0
    ) -> Boleta:
        """Genera una nueva boleta u orden de cobro/servicio en el sistema."""
        socio = self.buscar_socio_por_rut(rut_socio)
        user = self._usuarios_sistema.get(username_usuario.strip().lower())
        if not user:
            raise BibliotecaError(f"Usuario operador '{username_usuario}' no encontrado.")

        num_b = self._contador_boletas
        self._contador_boletas += 1

        boleta = Boleta(
            numero=num_b,
            socio=socio,
            usuario=user,
            tipo=tipo,
            descripcion=descripcion,
            prestamo_id=prestamo_id,
            iva_pct=iva_pct,
            descuento=descuento
        )
        self._registro_boletas.append(boleta)
        return boleta

    def guardar_boleta(self, boleta: Boleta) -> None:
        """Guarda la boleta en la base de datos."""
        if hasattr(self, "_boleta_dao"):
            self._boleta_dao.guardar(boleta)

    # ==================== CASOS DE USO: PERSISTENCIA Y EXPORTACIÓN JSON ====================
    def exportar_a_json(self, ruta_archivo: Optional[str] = None) -> str:
        """Exporta la totalidad del estado de la biblioteca a un archivo .json."""
        dao = JsonDao(ruta_archivo) if ruta_archivo else self._json_dao
        return dao.exportar_desde_sistema(self)

    def guardar_en_json(self, ruta_archivo: Optional[str] = None) -> str:
        """Alias para guardar en JSON."""
        return self.exportar_a_json(ruta_archivo)

    def hidratar_desde_json(self, datos: Dict[str, Any]) -> None:
        """Recarga todas las colecciones en memoria a partir de una estructura JSON."""
        # 1. Cargar Socios
        for s in datos.get("socios", []):
            fecha_ins = date.fromisoformat(s["fecha_inscripcion"]) if s.get("fecha_inscripcion") else date.today()
            socio = Socio(
                rut=s["rut"],
                nombre_completo=s["nombre_completo"],
                telefono=s.get("telefono", ""),
                email=s.get("email", ""),
                numero_socio=s.get("numero_socio", 1),
                fecha_inscripcion=fecha_ins,
                tiene_multa_pendiente=s.get("tiene_multa_pendiente", False),
                monto_multa_acumulada=float(s.get("monto_multa_acumulada", 0.0)),
                activo=s.get("activo", True)
            )
            self._registro_socios[socio.get_rut()] = socio
            if socio.numero_socio and socio.numero_socio >= self._contador_socios:
                self._contador_socios = socio.numero_socio + 1

        # 2. Cargar Usuarios
        for u in datos.get("usuarios", []):
            rol_str = u.get("rol", "").upper()
            if "ADMINISTRADORA" in rol_str:
                user = Administradora(
                    rut=u["rut"],
                    nombre_completo=u["nombre_completo"],
                    telefono=u.get("telefono", ""),
                    email=u.get("email", ""),
                    username=u["username"],
                    password="",
                    nivel_acceso=u.get("nivel_acceso", "SUPERADMIN")
                )
            else:
                user = BibliotecariaAtencion(
                    rut=u["rut"],
                    nombre_completo=u["nombre_completo"],
                    telefono=u.get("telefono", ""),
                    email=u.get("email", ""),
                    username=u["username"],
                    password="",
                    turno=u.get("turno", "Manana")
                )
            user._password_hash = u.get("password_hash", "")
            self._usuarios_sistema[user.username] = user

        # 3. Cargar Catálogo
        for m in datos.get("catalogo", []):
            tipo = m.get("tipo_material", "").upper()
            if "LIBRO" in tipo:
                mat = Libro(
                    codigo=m["codigo"],
                    titulo=m["titulo"],
                    autor_o_creador=m["autor_o_creador"],
                    anio_publicacion=m["anio_publicacion"],
                    precio_base_reposicion=m["precio_base_reposicion"],
                    isbn=m.get("isbn", "S/N"),
                    editorial=m.get("editorial", "Desconocida"),
                    numero_paginas=m.get("numero_paginas", 100),
                    prestado=m.get("prestado", False)
                )
            elif "REVISTA" in tipo:
                mat = Revista(
                    codigo=m["codigo"],
                    titulo=m["titulo"],
                    autor_o_creador=m["autor_o_creador"],
                    anio_publicacion=m["anio_publicacion"],
                    precio_base_reposicion=m["precio_base_reposicion"],
                    issn=m.get("issn", "S/N"),
                    numero_edicion=m.get("numero_edicion", 1),
                    mes_publicacion=m.get("mes_publicacion", "Enero"),
                    prestado=m.get("prestado", False)
                )
            elif "MULTIMEDIA" in tipo:
                mat = MaterialMultimedia(
                    codigo=m["codigo"],
                    titulo=m["titulo"],
                    autor_o_creador=m["autor_o_creador"],
                    anio_publicacion=m["anio_publicacion"],
                    precio_base_reposicion=m["precio_base_reposicion"],
                    formato=m.get("formato", "DVD"),
                    duracion_minutos=m.get("duracion_minutos", 90),
                    clasificacion_edad=m.get("clasificacion_edad", "TE"),
                    prestado=m.get("prestado", False)
                )
            elif "EXTRANJERO" in tipo:
                mat = MaterialExtranjero(
                    codigo=m["codigo"],
                    titulo=m["titulo"],
                    autor_o_creador=m["autor_o_creador"],
                    anio_publicacion=m["anio_publicacion"],
                    precio_usd=m.get("precio_usd", 50.0),
                    pais_origen=m.get("pais_origen", "EE.UU."),
                    recargo_aduanero_pct=m.get("recargo_aduanero_pct", 0.06),
                    prestado=m.get("prestado", False)
                )
            else:
                mat = Libro(
                    codigo=m["codigo"],
                    titulo=m["titulo"],
                    autor_o_creador=m["autor_o_creador"],
                    anio_publicacion=m["anio_publicacion"],
                    precio_base_reposicion=m.get("precio_base_reposicion", 20000.0),
                    isbn="S/N",
                    editorial="General",
                    numero_paginas=100,
                    prestado=m.get("prestado", False)
                )
            self._catalogo_materiales[mat.codigo] = mat

        # 4. Cargar Préstamos
        for p in datos.get("prestamos", []):
            socio = self.buscar_socio_por_rut(p["socio_rut"])
            biblio = self._usuarios_sistema.get(p["bibliotecaria_username"]) or list(self._usuarios_sistema.values())[0]
            fecha_p = datetime.fromisoformat(p["fecha_prestamo"])
            prestamo = Prestamo(
                id_prestamo=p["id_prestamo"],
                socio=socio,
                bibliotecaria=biblio,
                fecha_prestamo=fecha_p,
                estado=p.get("estado", "ACTIVO")
            )
            for d in p.get("detalles", []):
                mat_cod = d["material_codigo"]
                if mat_cod in self._catalogo_materiales:
                    mat_obj = self._catalogo_materiales[mat_cod]
                    det = DetallePrestamo(
                        id_detalle=d["id_detalle"],
                        material=mat_obj,
                        fecha_inicio=date.fromisoformat(d["fecha_inicio"]) if d.get("fecha_inicio") else fecha_p.date(),
                        dias_prestamo=d.get("dias_prestamo_otorgados"),
                        devuelto=d.get("devuelto", False),
                        cantidad_renovaciones=d.get("cantidad_renovaciones", 0),
                        fecha_devolucion_real=date.fromisoformat(d["fecha_devolucion_real"]) if d.get("fecha_devolucion_real") else None,
                        fecha_devolucion_esperada=date.fromisoformat(d["fecha_devolucion_esperada"]) if d.get("fecha_devolucion_esperada") else None
                    )
                    prestamo.agregar_detalle_existente(det)
                    
            self._registro_prestamos.append(prestamo)
            if prestamo.id_prestamo >= self._contador_prestamos:
                self._contador_prestamos = prestamo.id_prestamo + 1

    def _buscar_prestamo(self, id_prestamo: int) -> Prestamo:
        """Busca una transacción de préstamo por ID."""
        for p in self._registro_prestamos:
            if p.id_prestamo == id_prestamo:
                return p
        raise PrestamoNoEncontradoError(id_prestamo)

    def cargar_datos_desde_bd(self) -> None:
        """
        Carga y sincroniza el estado de la biblioteca desde las tablas relacionales de SQLite
        utilizando los Data Access Objects (DAOs). Garantiza persistencia real entre cierres y
        reaperturas del software (Caso de prueba P05).
        """
        if not self._conn:
            return

        # 1. Cargar Usuarios
        try:
            if hasattr(self, "_usuario_dao"):
                for u in self._usuario_dao.listar_todos():
                    self._usuarios_sistema[u.username.lower()] = u
        except Exception:
            pass

        # 2. Cargar Socios
        try:
            if hasattr(self, "_socio_dao"):
                for s in self._socio_dao.listar_todos():
                    rut_clean = s.get_rut().replace(".", "").replace("-", "").strip().upper()
                    self._registro_socios[rut_clean] = s
                    if s.numero_socio and s.numero_socio >= self._contador_socios:
                        self._contador_socios = s.numero_socio + 1
        except Exception:
            pass

        # 3. Cargar Materiales mediante DAOs polimórficos
        try:
            if hasattr(self, "_libro_dao"):
                for lib in self._libro_dao.listar_todos():
                    self._catalogo_materiales[lib.codigo] = lib
            if hasattr(self, "_revista_dao"):
                for rev in self._revista_dao.listar_todos():
                    self._catalogo_materiales[rev.codigo] = rev
            if hasattr(self, "_multimedia_dao"):
                for mm in self._multimedia_dao.listar_todos():
                    self._catalogo_materiales[mm.codigo] = mm
            if hasattr(self, "_extranjero_dao"):
                for ext in self._extranjero_dao.listar_todos():
                    self._catalogo_materiales[ext.codigo] = ext
        except Exception:
            pass

        # 4. Cargar Préstamos reconstruyendo objetos completos
        try:
            if hasattr(self, "_prestamo_dao"):
                prestamos_cargados = self._prestamo_dao.listar_todos_objetos(
                    self._catalogo_materiales,
                    self._registro_socios,
                    self._usuarios_sistema
                )
                self._registro_prestamos = prestamos_cargados
                for p in self._registro_prestamos:
                    if p.id_prestamo >= self._contador_prestamos:
                        self._contador_prestamos = p.id_prestamo + 1
        except Exception:
            pass

    def sembrar_datos_iniciales(self) -> None:
        """
        Carga datos semilla esenciales para la operatividad inmediata del negocio
        y los persiste en la base de datos SQLite mediante sus respectivos DAOs.
        """
        # 1. Personal del Sistema
        admin = Administradora(
            rut="19.876.543-0",
            nombre_completo="Camila Valenzuela Pavez",
            telefono="+56911223344",
            email="cvalenzuela@cordillera.cl",
            username="admin",
            password="AdminSuper2026*",
            nivel_acceso="SUPERADMIN"
        )
        biblio1 = BibliotecariaAtencion(
            rut="17.654.321-3",
            nombre_completo="Valentina Rojas Morales",
            telefono="+56922334455",
            email="vrojas@cordillera.cl",
            username="vrojas",
            password="PasswordBiblio123!",
            turno="Mañana"
        )
        biblio2 = BibliotecariaAtencion(
            rut="16.543.210-K",
            nombre_completo="Ignacio Soto Silva",
            telefono="+56933445566",
            email="isoto@cordillera.cl",
            username="isoto",
            password="PasswordBiblio456!",
            turno="Tarde"
        )
        self.registrar_usuario(admin)
        self.registrar_usuario(biblio1)
        self.registrar_usuario(biblio2)

        # 2. Socios iniciales
        self.inscribir_socio(
            rut="18.234.567-9",
            nombre_completo="Andrés Castro Morán",
            telefono="+56988776655",
            email="andres.castro@inacap.cl"
        )
        self.inscribir_socio(
            rut="15.432.109-8",
            nombre_completo="Beatriz Fuentes Lara",
            telefono="+56977665544",
            email="beatriz.fuentes@gmail.com"
        )
        socio3 = self.inscribir_socio(
            rut="12.345.678-5",
            nombre_completo="Diego Morales Peña",
            telefono="+56966554433",
            email="diego.morales@empresa.cl"
        )
        self.registrar_multa_socio(socio3.get_rut(), 2500.0)

        # 3. Materiales de los diferentes tipos
        libro1 = Libro(
            codigo="LIB-001",
            titulo="Cien Años de Soledad",
            autor_o_creador="Gabriel García Márquez",
            anio_publicacion=1967,
            precio_base_reposicion=28000.0,
            isbn="978-0307474728",
            editorial="Sudamericana",
            numero_paginas=471
        )
        libro2 = Libro(
            codigo="LIB-002",
            titulo="El Quijote de la Mancha",
            autor_o_creador="Miguel de Cervantes",
            anio_publicacion=1605,
            precio_base_reposicion=32000.0,
            isbn="978-8420412146",
            editorial="Alfaguara",
            numero_paginas=863
        )
        revista1 = Revista(
            codigo="REV-001",
            titulo="National Geographic en Español",
            autor_o_creador="Varios Autores",
            anio_publicacion=2024,
            precio_base_reposicion=12000.0,
            issn="0027-9358",
            numero_edicion=145,
            mes_publicacion="Agosto 2024"
        )
        dvd1 = MaterialMultimedia(
            codigo="DVD-001",
            titulo="Interstellar (Edición Especial 4K)",
            autor_o_creador="Christopher Nolan",
            anio_publicacion=2014,
            precio_base_reposicion=35000.0,
            formato="DVD",
            duracion_minutos=169,
            clasificacion_edad="+14"
        )
        extranjero1 = MaterialExtranjero(
            codigo="EXT-001",
            titulo="Artificial Intelligence: A Modern Approach (4th Ed)",
            autor_o_creador="Stuart Russell & Peter Norvig",
            anio_publicacion=2020,
            precio_usd=120.00,
            pais_origen="Estados Unidos",
            recargo_aduanero_pct=0.06
        )

        self.alta_nuevo_material(admin, libro1)
        self.alta_nuevo_material(admin, libro2)
        self.alta_nuevo_material(admin, revista1)
        self.alta_nuevo_material(admin, dvd1)
        self.alta_nuevo_material(admin, extranjero1)
