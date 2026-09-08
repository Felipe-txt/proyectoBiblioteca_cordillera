"""
Módulo BibliotecariaAtencion
Representa al personal de atención al público de la biblioteca.
Gestiona el ciclo de vida de los préstamos, devoluciones y renovaciones.
"""

from datetime import date
from typing import List, Optional, Any
from usuario import Usuario
from socio import Socio
from excepciones import SocioConMultaPendienteError, PermisoInsuficienteError


class BibliotecariaAtencion(Usuario):
    """Personal encargado del mesón de atención y circulación bibliográfica."""

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
        return self._turno

    @turno.setter
    def turno(self, valor: str) -> None:
        self._turno = valor.strip()

    def registrar_prestamo(self, socio: Socio, materiales: List[Any], id_prestamo: int = 1) -> Any:
        """
        Inicia un nuevo préstamo múltiple para un socio habilitado.
        Valida que el socio no tenga multas pendientes antes de despachar.
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
        """Registra la entrega física y devolución de un material prestado."""
        if not self.tiene_permiso("registrar_devolucion"):
            raise PermisoInsuficienteError(self._username, "registrar_devolucion")

        prestamo.registrar_devolucion_item(codigo_material, fecha_devolucion)

    def renovar_material(self, prestamo: Any, codigo_material: str) -> bool:
        """Procesa una solicitud de renovación sobre un ítem de préstamo vigente."""
        if not self.tiene_permiso("renovar_material"):
            raise PermisoInsuficienteError(self._username, "renovar_material")

        return prestamo.renovar_item(codigo_material)

    def __str__(self) -> str:
        return f"Bibliotecaria @{self._username} ({self._nombre_completo}) | Turno: {self._turno}"
