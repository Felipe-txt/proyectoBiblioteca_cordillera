"""
========================================================================================
PAQUETE: model
MÓDULO: bibliotecaria_atencion.py
ROL EN EL PROYECTO:
    Subclase concreta de Usuario encargada de la atención en mesón y gestión de préstamos.
========================================================================================
"""

try:
    from model.usuario import Usuario
except ImportError:
    from usuario import Usuario


class BibliotecariaAtencion(Usuario):
    """
    Representa a las bibliotecarias de mesón responsables del flujo de préstamos y devoluciones.
    """

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        username: str,
        password: str,
        turno: str = "Manana"
    ):
        super().__init__(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email,
            username=username,
            password=password
        )
        self._turno: str = turno.strip()

    @property
    def turno(self) -> str:
        return self._turno

    @turno.setter
    def turno(self, nuevo_turno: str) -> None:
        self._turno = nuevo_turno.strip()

    def obtener_rol(self) -> str:
        return f"BIBLIOTECARIA_ATENCION (Turno {self._turno})"

    def puede_condonar_multas(self) -> bool:
        return False

    def puede_gestionar_catalogo(self) -> bool:
        return False

    def puede_eliminar_registros(self) -> bool:
        return False

    def tiene_permiso(self, accion: str) -> bool:
        accion = accion.strip().lower()
        if accion in ["registrar_prestamo", "registrar_devolucion", "renovar_material", "consultar"]:
            return True
        return False
