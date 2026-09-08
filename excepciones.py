"""
Módulo de Excepciones de Negocio para la Biblioteca Municipal Cordillera
Define la jerarquía de errores específicos del dominio y las reglas infranqueables.
"""


class BibliotecaError(Exception):
    """Excepción base para todos los errores de la biblioteca."""

    def __init__(self, mensaje: str = "Error en el sistema de la biblioteca"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

    def __str__(self) -> str:
        return f"[BibliotecaError] {self.mensaje}"


class SocioConMultaPendienteError(BibliotecaError):
    """Lanzada cuando un socio con multa pendiente intenta solicitar un préstamo."""

    def __init__(self, rut_socio: str, monto_deuda: float):
        self.rut_socio = rut_socio
        self.monto_deuda = monto_deuda
        super().__init__(
            f"El socio con RUT '{rut_socio}' posee multas pendientes por un total de "
            f"${monto_deuda:,.0f} CLP. No puede solicitar nuevos préstamos hasta regularizar su saldo."
        )


class MaterialYaPrestadoError(BibliotecaError):
    """Lanzada cuando se intenta prestar un material que ya se encuentra en préstamo."""

    def __init__(self, codigo_material: str):
        self.codigo_material = codigo_material
        super().__init__(
            f"El material con código '{codigo_material}' ya se encuentra prestado a otro socio."
        )


class RenovacionNoPermitidaError(BibliotecaError):
    """Lanzada cuando un material no admite renovaciones o alcanzó el límite máximo permitido."""

    def __init__(self, codigo_material: str, razon: str):
        self.codigo_material = codigo_material
        self.razon = razon
        super().__init__(
            f"No es posible renovar el material '{codigo_material}'. Motivo: {razon}"
        )


class RutInvalidoError(BibliotecaError):
    """Lanzada cuando el RUT ingresado no cumple con el algoritmo Módulo 11 chileno."""

    def __init__(self, rut_ingresado: str):
        self.rut_ingresado = rut_ingresado
        super().__init__(
            f"El RUT '{rut_ingresado}' es inválido. Debe cumplir con el algoritmo Módulo 11 chileno."
        )


class PermisoInsuficienteError(BibliotecaError):
    """Lanzada cuando un usuario intenta realizar una acción sin contar con los privilegios requeridos."""

    def __init__(self, usuario: str, accion: str):
        self.usuario = usuario
        self.accion = accion
        super().__init__(
            f"El usuario '@{usuario}' no tiene permisos suficientes para ejecutar la acción '{accion}'."
        )


class MaterialNoEncontradoError(BibliotecaError):
    """Lanzada cuando no se encuentra un material en el catálogo."""

    def __init__(self, codigo: str):
        self.codigo = codigo
        super().__init__(f"Material con código '{codigo}' no existe en el catálogo.")


class SocioNoEncontradoError(BibliotecaError):
    """Lanzada cuando un socio no se encuentra en el registro de la biblioteca."""

    def __init__(self, rut: str):
        self.rut = rut
        super().__init__(f"Socio con RUT '{rut}' no está registrado en el sistema.")


class PrestamoNoEncontradoError(BibliotecaError):
    """Lanzada cuando no se localiza un préstamo por su identificador."""

    def __init__(self, id_prestamo: int):
        self.id_prestamo = id_prestamo
        super().__init__(f"Préstamo con ID N°{id_prestamo} no fue encontrado.")
