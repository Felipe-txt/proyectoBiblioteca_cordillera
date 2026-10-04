"""
========================================================================================
PAQUETE: model
MÓDULO: usuario.py
ROL EN EL PROYECTO:
    Subclase abstracta de Persona que modela a los operadores y administradores del sistema.
========================================================================================
"""

import hashlib
from abc import abstractmethod
try:
    from model.persona import Persona
except ImportError:
    from persona import Persona


class Usuario(Persona):
    """
    Clase base para todos los funcionarios del sistema que requieren autenticación.
    """

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        username: str,
        password: str,
        activo: bool = True
    ):
        super().__init__(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email
        )
        self._username: str = username.strip().lower()
        self._password_hash: str = self._hashear_password(password)
        self._activo: bool = bool(activo)

    @staticmethod
    def _hashear_password(password_plano: str) -> str:
        if not password_plano:
            password_plano = ""
        if len(password_plano) == 64 and all(c in "0123456789abcdefABCDEF" for c in password_plano):
            return password_plano.lower()
        return hashlib.sha256(password_plano.encode("utf-8")).hexdigest()

    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def activo(self) -> bool:
        return self._activo

    @activo.setter
    def activo(self, valor: bool) -> None:
        self._activo = bool(valor)

    @property
    def rol(self) -> str:
        return self.obtener_rol()

    def cambiar_password(self, password_actual: str, nueva_password: str) -> bool:
        if self.autenticar(password_actual):
            self._password_hash = self._hashear_password(nueva_password)
            return True
        return False

    def autenticar(self, password_ingresada: str) -> bool:
        hash_ingresado = hashlib.sha256(password_ingresada.encode("utf-8")).hexdigest()
        return hash_ingresado == self._password_hash

    @abstractmethod
    def obtener_rol(self) -> str:
        pass

    def tiene_permiso(self, accion: str) -> bool:
        """Verifica si el usuario tiene permiso para ejecutar una acción dada."""
        accion = accion.strip().lower()
        if accion in ["registrar_prestamo", "registrar_devolucion", "renovar_material", "consultar"]:
            return True
        return False

    def __str__(self) -> str:
        base = super().__str__()
        return f"[{self.obtener_rol()}] @{self._username} - {base}"
