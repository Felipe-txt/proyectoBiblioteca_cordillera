"""
========================================================================================
MÓDULO: excepciones.py
ROL EN EL PROYECTO:
    Define la jerarquía completa de excepciones personalizadas del dominio de la
    Biblioteca Municipal Cordillera.
    
    En la arquitectura POO del proyecto, estas excepciones representan el mecanismo
    formal para proteger las "Reglas Infranqueables del Negocio" (Business Rules)
    modeladas en el diagrama UML:
    
    1. Regla Bloqueante de Morosidad:
       - No se puede prestar material a un socio con multas impagas.
       -> SocioConMultaPendienteError
       
    2. Regla Bloqueante de Disponibilidad:
       - No se puede prestar un ejemplar que ya se encuentra en préstamo.
       -> MaterialYaPrestadoError
       
    3. Regla de Políticas de Duración y Renovación:
       - Solo los Libros admiten hasta 1 renovación. Las Revistas y Material
         Multimedia tienen 0 renovaciones por política bibliotecaria.
       -> RenovacionNoPermitidaError
       
    4. Regla de Integridad de Identidad Chilena:
       - Todo RUT debe ser válido matemáticamente bajo el algoritmo Módulo 11.
       -> RutInvalidoError
       
    5. Regla de Segregación de Roles:
       - Ciertas acciones son de atribución exclusiva (ej. solo Administradora
         puede dar altas/bajas de catálogo o condonar multas).
       -> PermisoInsuficienteError
       
    6. Reglas de Búsqueda e Integridad Referencial:
       - Manejo de entidades inexistentes al consultar por identificador único.
       -> MaterialNoEncontradoError, SocioNoEncontradoError, PrestamoNoEncontradoError
========================================================================================
"""


class BibliotecaError(Exception):
    """
    Excepción base para todos los errores de la biblioteca.
    
    Propósito:
        Hereda directamente de la clase estándar Exception de Python. Permite capturar
        cualquier falla específica del sistema de biblioteca mediante un único bloque:
        'except BibliotecaError as e:'
    """

    def __init__(self, mensaje: str = "Error general en el sistema de la biblioteca"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

    def __str__(self) -> str:
        # Formato estándar legible para logs de auditoría e interfaces de usuario
        return f"[BibliotecaError] {self.mensaje}"


class SocioConMultaPendienteError(BibliotecaError):
    """
    Excepción de Negocio: Socio Moroso con Multas Pendientes.
    
    ¿Cuándo se lanza?:
        Al intentar crear un nuevo préstamo (en SistemaBiblioteca o Prestamo)
        si el socio registra tiene_multa_pendiente=True o un monto acumulado > $0.
        
    Justificación en el Negocio:
        Garantiza que la biblioteca no aumente su riesgo patrimonial entregando más
        ejemplares a usuarios que registran cobros pendientes por atrasos o pérdidas.
    """

    def __init__(self, rut_socio: str, monto_deuda: float):
        self.rut_socio = rut_socio
        self.monto_deuda = monto_deuda
        super().__init__(
            f"El socio con RUT '{rut_socio}' posee multas pendientes por un total de "
            f"${monto_deuda:,.0f} CLP. No puede solicitar nuevos préstamos hasta regularizar su saldo."
        )


class MaterialYaPrestadoError(BibliotecaError):
    """
    Excepción de Negocio: Colisión de Préstamo de Material.
    
    ¿Cuándo se lanza?:
        Al invocar el método prestar() de Material o agregar un ítem a un préstamo,
        si el atributo _prestado ya se encuentra en True.
        
    Justificación en el Negocio:
        Evita inconsistencias físicas y lógicas en el inventario: un mismo libro físico
        no puede estar simultáneamente en posesión de dos socios distintos.
    """

    def __init__(self, codigo_material: str):
        self.codigo_material = codigo_material
        super().__init__(
            f"El material con código '{codigo_material}' ya se encuentra prestado a otro socio."
        )


class RenovacionNoPermitidaError(BibliotecaError):
    """
    Excepción de Negocio: Infracción a la Política de Renovación de Plazos.
    
    ¿Cuándo se lanza?:
        - Cuando se intenta renovar un material que no lo permite (Revistas y Multimedia).
        - Cuando un material elegible (Libros) ya agotó su cuota máxima de renovaciones (máx. 1).
        - Cuando el ítem ya fue entregado físicamente a la biblioteca.
        
    Justificación en el Negocio:
        Controla los tiempos de circulación bibliográfica según la demanda del catálogo:
        los libros permiten una extensión de 14 días adicionales, mientras que las
        revistas y discos audiovisuales son de alta rotación y no admiten extensiones.
    """

    def __init__(self, codigo_material: str, razon: str):
        self.codigo_material = codigo_material
        self.razon = razon
        super().__init__(
            f"No es posible renovar el material '{codigo_material}'. Motivo: {razon}"
        )


class RutInvalidoError(BibliotecaError):
    """
    Excepción de Validación: RUT Chileno Matemáticamente Inválido.
    
    ¿Cuándo se lanza?:
        Durante la instanciación de cualquier clase derivada de Persona (Socio, Usuario,
        Bibliotecaria, Administradora) si el RUT no cumple el algoritmo Módulo 11.
        
    Justificación en el Negocio:
        Asegura la calidad y veracidad de los datos personales ingresados, evitando
        registros duplicados, datos basura o identificadores adulterados.
    """

    def __init__(self, rut_ingresado: str):
        self.rut_ingresado = rut_ingresado
        super().__init__(
            f"El RUT '{rut_ingresado}' es inválido. Debe cumplir con el algoritmo Módulo 11 chileno."
        )


class PermisoInsuficienteError(BibliotecaError):
    """
    Excepción de Seguridad: Violación de Control de Acceso basado en Roles (RBAC).
    
    ¿Cuándo se lanza?:
        Cuando un usuario con rol 'BIBLIOTECARIA' intenta ejecutar métodos restringidos
        a 'ADMINISTRADORA' (ej: alta/baja de catálogo, condonación de multas).
        
    Justificación en el Negocio:
        Implementa el principio de mínimo privilegio y segregación de funciones,
        protegiendo las decisiones patrimoniales y administrativas del sistema.
    """

    def __init__(self, usuario: str, accion: str):
        self.usuario = usuario
        self.accion = accion
        super().__init__(
            f"El usuario '@{usuario}' no tiene permisos suficientes para ejecutar la acción '{accion}'."
        )


class MaterialNoEncontradoError(BibliotecaError):
    """
    Excepción de Consulta: Material No Localizado en el Catálogo.
    
    ¿Cuándo se lanza?:
        Al buscar un código de material en el catálogo de SistemaBiblioteca o en
        las líneas de detalle de un Préstamo y no encontrar coincidencia.
    """

    def __init__(self, codigo: str):
        self.codigo = codigo
        super().__init__(f"Material con código '{codigo}' no existe en el catálogo.")


class SocioNoEncontradoError(BibliotecaError):
    """
    Excepción de Consulta: Socio No Encontrado en el Registro.
    
    ¿Cuándo se lanza?:
        Al intentar procesar un préstamo, cobro o condonación para un RUT
        que no ha sido inscrito previamente en la biblioteca.
    """

    def __init__(self, rut: str):
        self.rut = rut
        super().__init__(f"Socio con RUT '{rut}' no está registrado en el sistema.")


class PrestamoNoEncontradoError(BibliotecaError):
    """
    Excepción de Consulta: Préstamo No Encontrado por Identificador.
    
    ¿Cuándo se lanza?:
        Al procesar una devolución o renovación sobre un número de transacción (id_prestamo)
        que no existe en el registro en memoria o base de datos.
    """

    def __init__(self, id_prestamo: int):
        self.id_prestamo = id_prestamo
        super().__init__(f"Préstamo con ID N°{id_prestamo} no fue encontrado.")
