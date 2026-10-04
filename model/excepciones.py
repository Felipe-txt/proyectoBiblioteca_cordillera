"""
========================================================================================
PAQUETE: model
MÓDULO: excepciones.py
ROL EN EL PROYECTO:
    Jerarquía de excepciones personalizadas para el dominio de la Biblioteca.
========================================================================================
"""


class BibliotecaError(Exception):
    """Excepción base para todos los errores de la biblioteca."""
    pass


class RutInvalidoError(BibliotecaError):
    """Lanzada cuando un RUT no cumple con el algoritmo Módulo 11."""
    def __init__(self, rut: str):
        super().__init__(f"El RUT ingresado '{rut}' no es válido según el algoritmo Módulo 11.")
        self.rut = rut


class SocioConMultaPendienteError(BibliotecaError):
    """Lanzada cuando un socio moroso intenta solicitar un nuevo préstamo."""
    def __init__(self, rut: str, monto: float):
        super().__init__(f"El socio con RUT {rut} registra multas pendientes por ${monto:,.0f} CLP. Operación bloqueada.")
        self.rut = rut
        self.monto = monto


class MaterialYaPrestadoError(BibliotecaError):
    """Lanzada cuando se intenta solicitar un material que no está disponible."""
    def __init__(self, codigo: str, titulo: str):
        super().__init__(f"El material '{codigo}' ({titulo}) se encuentra actualmente prestado.")
        self.codigo = codigo
        self.titulo = titulo


class MaterialNoEncontradoError(BibliotecaError):
    """Lanzada cuando un código de material no existe en el catálogo."""
    def __init__(self, codigo: str):
        super().__init__(f"No se encontró ningún material con el código '{codigo}'.")
        self.codigo = codigo


class SocioNoEncontradoError(BibliotecaError):
    """Lanzada cuando un socio no existe en el registro."""
    def __init__(self, rut: str):
        super().__init__(f"No se encontró ningún socio registrado con el RUT '{rut}'.")
        self.rut = rut


class PrestamoNoEncontradoError(BibliotecaError):
    """Lanzada cuando un identificador de préstamo no existe."""
    def __init__(self, id_prestamo: int):
        super().__init__(f"No se encontró el préstamo con ID #{id_prestamo}.")
        self.id_prestamo = id_prestamo


class RenovacionNoPermitidaError(BibliotecaError):
    """Lanzada cuando un material no admite más renovaciones o su política no lo permite."""
    def __init__(self, codigo: str, motivo: str):
        super().__init__(f"No es posible renovar el material '{codigo}': {motivo}.")
        self.codigo = codigo
        self.motivo = motivo


class PermisoInsuficienteError(BibliotecaError):
    """Lanzada cuando un usuario intenta ejecutar una acción reservada para un rol superior."""
    def __init__(self, usuario: str, accion: str):
        super().__init__(f"El usuario '{usuario}' no posee los privilegios necesarios para ejecutar: '{accion}'.")
        self.usuario = usuario
        self.accion = accion
