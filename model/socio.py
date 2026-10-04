"""
========================================================================================
PAQUETE: model
MÓDULO: socio.py
ROL EN EL PROYECTO:
    Subclase concreta de Persona que representa a los usuarios habilitados para solicitar préstamos.
========================================================================================
"""

from datetime import date
from typing import Optional
try:
    from model.persona import Persona
except ImportError:
    from persona import Persona


class Socio(Persona):
    """
    Subclase que modela a un socio activo de la Biblioteca Municipal.
    """

    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        email: str,
        numero_socio: Optional[int] = 1,
        fecha_inscripcion: Optional[date] = None,
        monto_multa_inicial: float = 0.0,
        activo: bool = True,
        tiene_multa_pendiente: Optional[bool] = None,
        monto_multa_acumulada: Optional[float] = None
    ):
        super().__init__(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email
        )
        self._numero_socio: Optional[int] = int(numero_socio) if numero_socio is not None else None
        self._fecha_inscripcion: date = fecha_inscripcion or date.today()
        
        # Soportar tanto monto_multa_inicial como monto_multa_acumulada
        if monto_multa_acumulada is not None:
            self._monto_multa_acumulada: float = max(0.0, float(monto_multa_acumulada))
        else:
            self._monto_multa_acumulada: float = max(0.0, float(monto_multa_inicial))
            
        if tiene_multa_pendiente is not None:
            self._tiene_multa_pendiente: bool = bool(tiene_multa_pendiente)
        else:
            self._tiene_multa_pendiente: bool = self._monto_multa_acumulada > 0.0
            
        self._activo: bool = bool(activo)

    @property
    def numero_socio(self) -> Optional[int]:
        return self._numero_socio

    @numero_socio.setter
    def numero_socio(self, valor: int) -> None:
        self._numero_socio = int(valor)

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

    @activo.setter
    def activo(self, valor: bool) -> None:
        self._activo = bool(valor)

    def puede_solicitar_prestamo(self) -> bool:
        """Regla 1: Debe estar activo, sin multa y con saldo deudor 0."""
        return self._activo and (not self._tiene_multa_pendiente) and (self._monto_multa_acumulada == 0.0)

    def esta_habilitado_para_prestamo(self) -> bool:
        return self.puede_solicitar_prestamo()

    def registrar_multa(self, monto: float) -> None:
        if monto > 0:
            self._monto_multa_acumulada += float(monto)
            self._tiene_multa_pendiente = True

    def pagar_multa(self, monto: float) -> float:
        if monto <= 0:
            return self._monto_multa_acumulada
        
        if monto >= self._monto_multa_acumulada:
            saldo_restante = 0.0
            self._monto_multa_acumulada = 0.0
            self._tiene_multa_pendiente = False
        else:
            self._monto_multa_acumulada -= float(monto)
            saldo_restante = self._monto_multa_acumulada
            
        return saldo_restante

    def condonar_multa(self) -> None:
        self._monto_multa_acumulada = 0.0
        self._tiene_multa_pendiente = False

    def __str__(self) -> str:
        base = super().__str__()
        estado_multa = f"CON MULTA (${self._monto_multa_acumulada:,.0f} CLP)" if self._tiene_multa_pendiente else "SIN MULTAS"
        num = f"#{self._numero_socio}" if self._numero_socio else "Sin Asignar"
        return f"[SOCIO {num}] {base} | Estado: {estado_multa}"
