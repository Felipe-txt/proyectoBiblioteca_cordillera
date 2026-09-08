"""
========================================================================================
MÓDULO: socio.py
ROL EN EL PROYECTO:
    Representa a los socios registrados (lectores y beneficiarios) en la Biblioteca
    Municipal Cordillera. Hereda de la clase base abstracta Persona.
    
    Responsabilidades Principales:
    - Controlar el número de socio y la fecha de inscripción.
    - Administrar el estado financiero de multas (acumulación, pago y condonación).
    - Evaluar la elegibilidad para solicitar nuevos préstamos de libros o material.
    
    Regla Infranqueable Asociada:
    - Regla N°1: Un socio con multas impagas (monto > 0 o tiene_multa_pendiente=True)
      queda inhabilitado de inmediato para solicitar nuevos préstamos.
      Si se intenta cursar uno en estas condiciones, se dispara SocioConMultaPendienteError.
========================================================================================
"""

from datetime import date
from typing import Optional
from persona import Persona


class Socio(Persona):
    """
    Subclase de Persona que modela al usuario o socio lector de la biblioteca.
    """

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
        # Invocamos el constructor padre para validar RUT y registrar datos de contacto
        super().__init__(rut, nombre_completo, telefono, email)
        
        # Atributos propios del socio
        self._numero_socio: int = int(numero_socio)
        self._fecha_inscripcion: date = fecha_inscripcion or date.today()
        self._monto_multa_acumulada: float = max(0.0, float(monto_multa_inicial))
        self._tiene_multa_pendiente: bool = self._monto_multa_acumulada > 0.0
        self._activo: bool = bool(activo)

    # ==================== PROPIEDADES (GETTERS) ====================
    @property
    def numero_socio(self) -> int:
        """Identificador numérico correlativo del socio en la biblioteca."""
        return self._numero_socio

    @property
    def fecha_inscripcion(self) -> date:
        """Fecha en que el socio se registró formalmente en la institución."""
        return self._fecha_inscripcion

    @property
    def tiene_multa_pendiente(self) -> bool:
        """Bandera booleana rápida para saber si el socio se encuentra sancionado o con deuda."""
        return self._tiene_multa_pendiente

    @property
    def monto_multa_acumulada(self) -> float:
        """Monto exacto en pesos chilenos (CLP) adeudado por el socio."""
        return self._monto_multa_acumulada

    @property
    def activo(self) -> bool:
        """Indica si la membresía del socio se encuentra vigente o suspendida."""
        return self._activo

    # ==================== LÓGICA DE NEGOCIO Y MULTAS ====================
    def puede_solicitar_prestamo(self) -> bool:
        """
        Regla Infranqueable N°1:
        Evalúa si el socio está en condiciones legales y financieras de retirar material.
        Condiciones:
        - Debe estar activo.
        - No debe tener marca de multa pendiente.
        - El saldo de multas acumuladas debe ser exactamente cero ($0 CLP).
        """
        return self._activo and (not self._tiene_multa_pendiente) and (self._monto_multa_acumulada == 0.0)

    def registrar_multa(self, monto: float) -> None:
        """
        Registra un cargo monetario al socio (por entrega tardía o reposición de material perdido).
        Automáticamente enciende la bandera _tiene_multa_pendiente para bloquear nuevos préstamos.
        """
        if monto > 0:
            self._monto_multa_acumulada += float(monto)
            self._tiene_multa_pendiente = True

    def pagar_multa(self, monto: float) -> float:
        """
        Procesa el abono o cancelación total de la deuda en mesón de caja.
        
        Retorna:
            float: El vuelto o cambio en dinero en caso de que el socio pague de más.
            
        Efecto secundario:
            Si el saldo llega a $0, se desbloquea al socio permitiéndole volver a pedir libros.
        """
        if monto <= 0:
            return 0.0

        if monto >= self._monto_multa_acumulada:
            vuelto = monto - self._monto_multa_acumulada
            self._monto_multa_acumulada = 0.0
            self._tiene_multa_pendiente = False  # Desbloqueado
            return vuelto
        else:
            # Abono parcial: Reduce el monto adeudado pero sigue manteniendo la deuda activa
            self._monto_multa_acumulada -= monto
            self._tiene_multa_pendiente = True
            return 0.0

    def condonar_multa(self) -> None:
        """
        Exonera administrativamente el total de la deuda acumulada.
        Nota: Esta acción solo debe ser orquestada por un usuario con rol 'ADMINISTRADORA'.
        """
        self._monto_multa_acumulada = 0.0
        self._tiene_multa_pendiente = False

    def suspender_socio(self) -> None:
        """Deshabilita temporalmente la cuenta del socio."""
        self._activo = False

    def reactivar_socio(self) -> None:
        """Reactiva al socio en la base de datos."""
        self._activo = True

    def __str__(self) -> str:
        estado_socio = "Activo" if self._activo else "Suspendido"
        estado_deuda = (
            f"Deuda: ${self._monto_multa_acumulada:,.0f} CLP (MULTADO)"
            if self._tiene_multa_pendiente
            else "Al día (Sin multas)"
        )
        return (
            f"Socio N°{self._numero_socio:04d} | {self._nombre_completo} (RUT: {self._rut}) | "
            f"Inscripción: {self._fecha_inscripcion.isoformat()} | {estado_deuda} | Estado: {estado_socio}"
        )
