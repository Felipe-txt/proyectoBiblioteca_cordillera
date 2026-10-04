"""
========================================================================================
PAQUETE: model
MÓDULO: administradora.py
ROL EN EL PROYECTO:
    Subclase concreta de Usuario con permisos de SUPERADMIN (condonar multas, alta de catálogo).
========================================================================================
"""

try:
    from model.usuario import Usuario
except ImportError:
    from usuario import Usuario


class Administradora(Usuario):
    """
    Representa a la administradora jefa con máximos privilegios en el sistema.
    """

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        username: str,
        password: str,
        nivel_acceso: str = "SUPERADMIN"
    ):
        super().__init__(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email,
            username=username,
            password=password
        )
        self._nivel_acceso: str = nivel_acceso.strip().upper()

    @property
    def nivel_acceso(self) -> str:
        return self._nivel_acceso

    def obtener_rol(self) -> str:
        return f"ADMINISTRADORA ({self._nivel_acceso})"

    def puede_condonar_multas(self) -> bool:
        return True

    def puede_gestionar_catalogo(self) -> bool:
        return True

    def puede_eliminar_registros(self) -> bool:
        return True

    def tiene_permiso(self, accion: str) -> bool:
        """La administradora posee todos los permisos del sistema."""
        return True
