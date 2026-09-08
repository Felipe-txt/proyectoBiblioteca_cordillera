"""
Módulo Administradora
Representa al usuario con máximo nivel de privilegios en el sistema bibliotecario.
Posee atribuciones exclusivas como dar de alta/baja catálogo y condonación de multas.
"""

from typing import Dict, Any
from usuario import Usuario
from socio import Socio
from excepciones import PermisoInsuficienteError


class Administradora(Usuario):
    """Rol de máxima autoridad administrativa de la Biblioteca Cordillera."""

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        username: str,
        password: str,
        nivel_acceso: str = "SUPERADMIN",
        activo: bool = True
    ):
        super().__init__(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email,
            username=username,
            password=password,
            rol="ADMINISTRADORA",
            activo=activo
        )
        self._nivel_acceso: str = nivel_acceso.strip().upper()

    @property
    def nivel_acceso(self) -> str:
        return self._nivel_acceso

    def dar_alta_material(self, material: Any, catalogo: Dict[str, Any]) -> None:
        """Incorpora un nuevo ejemplar al catálogo general de la biblioteca."""
        if not self.tiene_permiso("dar_alta_material"):
            raise PermisoInsuficienteError(self._username, "dar_alta_material")
        catalogo[material.codigo] = material

    def eliminar_material(self, codigo_material: str, catalogo: Dict[str, Any]) -> None:
        """Da de baja física o retira un material del catálogo."""
        if not self.tiene_permiso("eliminar_material"):
            raise PermisoInsuficienteError(self._username, "eliminar_material")
        cod = codigo_material.strip().upper()
        if cod in catalogo:
            del catalogo[cod]

    def condonar_multa(self, socio: Socio, motivo: str = "Condonación administrativa autorizada") -> None:
        """
        Atribución exclusiva: Exonera deudas y multas a un socio por causas justificadas.
        """
        if not self.tiene_permiso("condonar_multa"):
            raise PermisoInsuficienteError(self._username, "condonar_multa")
        socio.condonar_multa()

    def __str__(self) -> str:
        return f"Administradora @{self._username} ({self._nombre_completo}) | Nivel: {self._nivel_acceso}"
