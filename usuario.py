"""
Módulo Usuario
Clase base abstracta para el personal de la biblioteca.
Implementa autenticación segura mediante hash SHA-256 y control de permisos por roles.
"""

from abc import ABC
import hashlib
from persona import Persona


class Usuario(Persona, ABC):
    """Clase base abstracta para los empleados con acceso al sistema de la biblioteca."""

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        username: str,
        password: str,
        rol: str,
        activo: bool = True
    ):
        super().__init__(rut, nombre_completo, telefono, email)
        self._username: str = username.strip().lower()
        self._password_hash: str = self._hash_password(password)
        self._rol: str = rol.strip().upper()
        self._activo: bool = bool(activo)

    @staticmethod
    def _hash_password(raw_pwd: str) -> str:
        """Genera un hash SHA-256 seguro a partir de la contraseña plana."""
        return hashlib.sha256(raw_pwd.encode("utf-8")).hexdigest()

    def autenticar(self, password: str) -> bool:
        """Verifica si la contraseña ingresada coincide con el hash almacenado."""
        if not self._activo:
            return False
        return self._hash_password(password) == self._password_hash

    def cambiar_password(self, password_actual: str, password_nueva: str) -> bool:
        """Permite actualizar la contraseña si la actual es válida."""
        if self.autenticar(password_actual):
            self._password_hash = self._hash_password(password_nueva)
            return True
        return False

    def tiene_permiso(self, accion: str) -> bool:
        """
        Valida si el rol asignado al usuario cuenta con privilegios para la acción.
        ADMIN / SUPERADMIN posee comodín '*', Bibliotecaria posee acciones de préstamo/atención.
        """
        if not self._activo:
            return False

        permisos_por_rol = {
            "ADMINISTRADORA": ["*"],
            "SUPERADMIN": ["*"],
            "BIBLIOTECARIA": [
                "registrar_prestamo",
                "registrar_devolucion",
                "renovar_material",
                "consultar_socio",
                "consultar_material",
                "consultar_prestamo",
                "inscribir_socio"
            ]
        }
        permisos = permisos_por_rol.get(self._rol, [])
        return "*" in permisos or accion.strip().lower() in [p.lower() for p in permisos]

    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def rol(self) -> str:
        return self._rol

    @property
    def activo(self) -> bool:
        return self._activo

    def desactivar(self) -> None:
        self._activo = False

    def activar(self) -> None:
        self._activo = True

    def __str__(self) -> str:
        estado = "Activo" if self._activo else "Inactivo"
        return f"Usuario @{self._username} ({self._nombre_completo}) | Rol: {self._rol} | Estado: {estado}"
