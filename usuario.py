"""
========================================================================================
MÓDULO: usuario.py
ROL EN EL PROYECTO:
    Clase Base Abstracta (ABC) para todos los empleados de la biblioteca que interactúan
    con el sistema informático. Hereda de Persona.
    
    Responsabilidades Principales:
    - Gestión de credenciales de usuario (username y password).
    - Seguridad de la información: Almacenamiento seguro mediante hashing SHA-256
      (evitando guardar contraseñas en texto plano).
    - Matriz de Control de Acceso Basado en Roles (RBAC - Role-Based Access Control):
      Valida si el rol de un usuario tiene privilegios para ejecutar operaciones críticas.
    
    Regla Infranqueable Asociada:
    - Regla N°4 (Segregación de Roles): Si un usuario intenta realizar una operación
      no autorizada para su rol, se lanza PermisoInsuficienteError.
========================================================================================
"""

from abc import ABC
import hashlib
from persona import Persona


class Usuario(Persona, ABC):
    """
    Clase abstracta para el personal autorizado con acceso al software de la biblioteca.
    """

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
        # Seguridad: La contraseña se hashea de inmediato con SHA-256
        self._password_hash: str = self._hash_password(password)
        self._rol: str = rol.strip().upper()
        self._activo: bool = bool(activo)

    @staticmethod
    def _hash_password(raw_pwd: str) -> str:
        """
        Calcula el resumen criptográfico SHA-256 (64 caracteres hexadecimales)
        a partir de la contraseña suministrada en texto plano.
        """
        return hashlib.sha256(raw_pwd.encode("utf-8")).hexdigest()

    def autenticar(self, password: str) -> bool:
        """
        Verifica las credenciales en el inicio de sesión.
        Compara el hash del texto ingresado contra el hash almacenado en memoria/BD.
        """
        if not self._activo:
            return False
        return self._hash_password(password) == self._password_hash

    def cambiar_password(self, password_actual: str, password_nueva: str) -> bool:
        """
        Permite a un empleado actualizar su clave secreta, requiriendo previamente
        la verificación satisfactoria de su contraseña vigente.
        """
        if self.autenticar(password_actual):
            self._password_hash = self._hash_password(password_nueva)
            return True
        return False

    def tiene_permiso(self, accion: str) -> bool:
        """
        Mecanismo de autorización por roles (RBAC):
        - ADMINISTRADORA / SUPERADMIN: Tiene permiso universal (comodín '*').
        - BIBLIOTECARIA: Autorizada exclusivamente para operaciones de mesón y atención:
          registrar préstamos, devoluciones, renovaciones y consultas.
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

    # ==================== PROPIEDADES (GETTERS) ====================
    @property
    def username(self) -> str:
        """Nombre de usuario único para inicio de sesión."""
        return self._username

    @property
    def password_hash(self) -> str:
        """Hash SHA-256 para persistencia en base de datos."""
        return self._password_hash

    @property
    def rol(self) -> str:
        """Rol o cargo funcional en la organización."""
        return self._rol

    @property
    def activo(self) -> bool:
        """Estado de habilitación del usuario en la plataforma."""
        return self._activo

    def desactivar(self) -> None:
        """Inhabilita el acceso del empleado al sistema."""
        self._activo = False

    def activar(self) -> None:
        """Habilita el acceso del empleado al sistema."""
        self._activo = True

    def __str__(self) -> str:
        estado = "Activo" if self._activo else "Inactivo"
        return f"Usuario @{self._username} ({self._nombre_completo}) | Rol: {self._rol} | Estado: {estado}"
