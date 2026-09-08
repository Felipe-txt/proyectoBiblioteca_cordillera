"""
========================================================================================
MÓDULO: bibliotecaria_atencion.py
ROL EN EL PROYECTO:
    Representa al personal operativo que trabaja en el mesón de circulación y
    atención al público de la biblioteca. Hereda de Usuario.
    
    Responsabilidades Principales:
    - Registrar préstamos directos a los socios verificando que no tengan multas impagas.
    - Registrar devoluciones de ejemplares liberándolos en el inventario.
    - Aplicar renovaciones de plazo sobre materiales elegibles (ej: Libros).
    - Administrar el turno laboral (Mañana, Tarde, Vespertino).
    
    Excepciones Asociadas:
    - PermisoInsuficienteError: Si el usuario carece de la autorización para la acción.
    - SocioConMultaPendienteError: Si se intenta prestar a un socio bloqueado por morosidad.
========================================================================================
"""

from datetime import date
from typing import List, Optional, Any
from usuario import Usuario
from socio import Socio
from excepciones import SocioConMultaPendienteError, PermisoInsuficienteError


class BibliotecariaAtencion(Usuario):
    """
    Subclase de Usuario para el rol 'BIBLIOTECARIA', encargada de las operaciones
    cotidianas de mesón y préstamo bibliotecario.
    """

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        username: str,
        password: str,
        turno: str = "Mañana",
        activo: bool = True
    ):
        # Asignamos el rol formal 'BIBLIOTECARIA' a la clase base
        super().__init__(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email,
            username=username,
            password=password,
            rol="BIBLIOTECARIA",
            activo=activo
        )
        self._turno: str = turno.strip()

    @property
    def turno(self) -> str:
        """Turno asignado de atención (ej: 'Mañana', 'Tarde')."""
        return self._turno

    @turno.setter
    def turno(self, valor: str) -> None:
        self._turno = valor.strip()

    def registrar_prestamo(self, socio: Socio, materiales: List[Any], id_prestamo: int = 1) -> Any:
        """
        Inicia un nuevo préstamo múltiple para un socio.
        
        Flujo de control:
        1. Verifica permisos con 'tiene_permiso'.
        2. Verifica que el socio no tenga multas pendientes (Regla Infranqueable N°1).
           Si tiene multa, lanza SocioConMultaPendienteError.
        3. Genera la instancia transaccional de Prestamo y añade cada Material.
        """
        from prestamo import Prestamo

        if not self.tiene_permiso("registrar_prestamo"):
            raise PermisoInsuficienteError(self._username, "registrar_prestamo")

        if not socio.puede_solicitar_prestamo():
            raise SocioConMultaPendienteError(socio.get_rut(), socio.monto_multa_acumulada)

        prestamo = Prestamo(
            id_prestamo=id_prestamo,
            socio=socio,
            bibliotecaria=self
        )

        for mat in materiales:
            prestamo.agregar_item(mat)

        return prestamo

    def registrar_devolucion(
        self,
        prestamo: Any,
        codigo_material: str,
        fecha_devolucion: Optional[date] = None
    ) -> None:
        """
        Recepciona físicamente un material prestado.
        Invoca la devolución en la cabecera del préstamo, recalculando multas si hubo demora.
        """
        if not self.tiene_permiso("registrar_devolucion"):
            raise PermisoInsuficienteError(self._username, "registrar_devolucion")

        prestamo.registrar_devolucion_item(codigo_material, fecha_devolucion)

    def renovar_material(self, prestamo: Any, codigo_material: str) -> bool:
        """
        Procesa una solicitud de extensión de plazo sobre un ítem prestado.
        Delega la comprobación polimórfica de renovaciones al DetallePrestamo.
        """
        if not self.tiene_permiso("renovar_material"):
            raise PermisoInsuficienteError(self._username, "renovar_material")

        return prestamo.renovar_item(codigo_material)

    def __str__(self) -> str:
        return f"Bibliotecaria @{self._username} ({self._nombre_completo}) | Turno: {self._turno}"
