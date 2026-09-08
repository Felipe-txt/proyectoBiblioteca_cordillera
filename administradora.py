"""
========================================================================================
MÓDULO: administradora.py
ROL EN EL PROYECTO:
    Representa al usuario con máximo nivel de privilegios y responsabilidad de
    gestión en la Biblioteca Cordillera (nivel SUPERADMIN). Hereda de Usuario.
    
    Responsabilidades Principales y Atribuciones Exclusivas:
    - Alta de nuevos materiales en el catálogo (Libros, Revistas, DVDs, Extranjeros).
    - Baja o desincorporación de materiales del inventario de la biblioteca.
    - Condonación administrativa de multas y deudas de socios (por ejemplo, por
      licencias médicas, pérdidas justificadas o acuerdos institucionales).
    
    Regla Infranqueable Asociada:
    - Regla N°4 (Segregación de Roles): Estas acciones están estrictamente prohibidas
      para usuarios con rol Bibliotecaria. Si alguien no autorizado intenta ejecutarlas,
      se dispara PermisoInsuficienteError.
========================================================================================
"""

from typing import Dict, Any
from usuario import Usuario
from socio import Socio
from excepciones import PermisoInsuficienteError


class Administradora(Usuario):
    """
    Subclase de Usuario con nivel de acceso 'SUPERADMIN' y facultades ejecutivas plenas.
    """

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
        # Asignamos el rol 'ADMINISTRADORA' en la clase base
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
        """Nivel jerárquico de autorización en la infraestructura (ej: 'SUPERADMIN')."""
        return self._nivel_acceso

    def dar_alta_material(self, material: Any, catalogo: Dict[str, Any]) -> None:
        """
        Incorpora un nuevo ejemplar al catálogo general de la biblioteca.
        Valida que el usuario posea la atribución 'dar_alta_material'.
        """
        if not self.tiene_permiso("dar_alta_material"):
            raise PermisoInsuficienteError(self._username, "dar_alta_material")
        catalogo[material.codigo] = material

    def eliminar_material(self, codigo_material: str, catalogo: Dict[str, Any]) -> None:
        """
        Da de baja física o retira un material del catálogo institucional.
        Valida que el usuario posea la atribución 'eliminar_material'.
        """
        if not self.tiene_permiso("eliminar_material"):
            raise PermisoInsuficienteError(self._username, "eliminar_material")
        cod = codigo_material.strip().upper()
        if cod in catalogo:
            del catalogo[cod]

    def condonar_multa(self, socio: Socio, motivo: str = "Condonación administrativa autorizada") -> None:
        """
        Facultad exclusiva: Exonera deudas y multas a un socio por causas justificadas.
        Permite que un socio sancionado vuelva a solicitar préstamos.
        """
        if not self.tiene_permiso("condonar_multa"):
            raise PermisoInsuficienteError(self._username, "condonar_multa")
        socio.condonar_multa()

    def __str__(self) -> str:
        return f"Administradora @{self._username} ({self._nombre_completo}) | Nivel: {self._nivel_acceso}"
