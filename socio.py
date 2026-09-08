"""
Módulo Socio
Representa a los socios registrados de la Biblioteca Municipal Cordillera.
Gestiona el estado de multas, elegibilidad de préstamos y membresía.
"""

from datetime import date
from typing import Optional
from persona import Persona


class Socio(Persona):
    """Clase que representa a un socio registrado de la biblioteca."""

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        numero_socio: int,
        fecha_inscripcion: Optional[date] = None,
        monto_multa_inicial: float = 0.0,
        activo: bool = True
    ):
        super().__init__(rut, nombre_completo, telefono, email)
        self._numero_socio: int = int(numero_socio)
        self._fecha_inscripcion: date = fecha_inscripcion or date.today()
        self._monto_multa_acumulada: float = max(0.0, float(monto_multa_inicial))
        self._tiene_multa_pendiente: bool = self._monto_multa_acumulada > 0.0
        self._activo: bool = bool(activo)

    @property
    def numero_socio(self) -> int:
        return self._numero_socio

    @property
    def fecha_inscripcion(self) -> date:
        return self._fecha_inscripcion

    @property
    def tiene_multa_pendiente(self) -> bool:
        return self._tiene_multa_pendiente

    @property
    def monto_multa_acumulada(self) -> float:
        return self._monto_multa_acumulada

    @property
    def activo(self) -> bool:
        return self._activo

    def puede_solicitar_prestamo(self) -> bool:
        """
        Regla Infranqueable N°1:
        Un socio solo puede solicitar préstamos si está activo, no tiene marca de multa
        y su deuda acumulada es estrictamente igual a $0.
        """
        return self._activo and (not self._tiene_multa_pendiente) and (self._monto_multa_acumulada == 0.0)

    def registrar_multa(self, monto: float) -> None:
        """Registra una nueva multa o recargo al saldo del socio."""
        if monto > 0:
            self._monto_multa_acumulada += float(monto)
            self._tiene_multa_pendiente = True

    def pagar_multa(self, monto: float) -> float:
        """
        Procesa el pago de una multa. Retorna el vuelto en caso de excedente.
        Si la deuda llega a 0, se desbloquea el estado del socio.
        """
        if monto <= 0:
            return 0.0

        if monto >= self._monto_multa_acumulada:
            vuelto = monto - self._monto_multa_acumulada
            self._monto_multa_acumulada = 0.0
            self._tiene_multa_pendiente = False
            return vuelto
        else:
            self._monto_multa_acumulada -= monto
            self._tiene_multa_pendiente = True
            return 0.0

    def condonar_multa(self) -> None:
        """Condonación autorizada de la totalidad de las multas pendientes."""
        self._monto_multa_acumulada = 0.0
        self._tiene_multa_pendiente = False

    def suspender_socio(self) -> None:
        """Suspende temporal o definitivamente al socio."""
        self._activo = False

    def reactivar_socio(self) -> None:
        """Reactiva al socio en la biblioteca."""
        self._activo = True

    def __str__(self) -> str:
        estado_socio = "Activo" if self._activo else "Suspendido"
        estado_deuda = f"Deuda: ${self._monto_multa_acumulada:,.0f} CLP (MULTADO)" if self._tiene_multa_pendiente else "Al día (Sin multas)"
        return (
            f"Socio N°{self._numero_socio:04d} | {self._nombre_completo} (RUT: {self._rut}) | "
            f"Inscripción: {self._fecha_inscripcion.isoformat()} | {estado_deuda} | Estado: {estado_socio}"
        )
