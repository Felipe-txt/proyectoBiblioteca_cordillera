"""
Módulo DetallePrestamo
Representa una línea/ítem individual de un préstamo general.
Controla los plazos individuales de devolución, extensiones (renovaciones) y cálculo de atraso.
"""

from datetime import date, timedelta
from typing import Optional
from material import Material
from excepciones import RenovacionNoPermitidaError


class DetallePrestamo:
    """Línea de detalle que asocia un material prestado a una fecha de vencimiento y trazabilidad."""

    def __init__(
        self,
        id_detalle: int,
        material: Material,
        fecha_inicio: Optional[date] = None,
        dias_prestamo: Optional[int] = None,
        devuelto: bool = False,
        cantidad_renovaciones: int = 0,
        fecha_devolucion_real: Optional[date] = None
    ):
        self._id_detalle: int = int(id_detalle)
        self._material: Material = material
        self._fecha_inicio: date = fecha_inicio or date.today()
        self._dias_prestamo_otorgados: int = dias_prestamo if dias_prestamo is not None else material.dias_prestamo()
        self._fecha_devolucion_esperada: date = self._fecha_inicio + timedelta(days=self._dias_prestamo_otorgados)
        self._fecha_devolucion_real: Optional[date] = fecha_devolucion_real
        self._cantidad_renovaciones: int = int(cantidad_renovaciones)
        self._devuelto: bool = bool(devuelto)

        # Si no estaba devuelto y el material aún no estaba marcado como prestado, se marca
        if not self._devuelto and not self._material.esta_prestado():
            self._material.prestar()

    @property
    def id_detalle(self) -> int:
        return self._id_detalle

    @property
    def material(self) -> Material:
        return self._material

    @property
    def fecha_inicio(self) -> date:
        return self._fecha_inicio

    @property
    def dias_prestamo_otorgados(self) -> int:
        return self._dias_prestamo_otorgados

    @property
    def fecha_devolucion_esperada(self) -> date:
        return self._fecha_devolucion_esperada

    @property
    def fecha_devolucion_real(self) -> Optional[date]:
        return self._fecha_devolucion_real

    @property
    def cantidad_renovaciones(self) -> int:
        return self._cantidad_renovaciones

    @property
    def devuelto(self) -> bool:
        return self._devuelto

    def renovar(self) -> bool:
        """
        Aplica una renovación sobre el ítem si las reglas polimórficas del material lo permiten.
        Extiende la fecha de devolución esperada.
        """
        if self._devuelto:
            raise RenovacionNoPermitidaError(
                self._material.codigo,
                "El material ya fue devuelto previamente a la biblioteca."
            )

        if not self._material.permite_renovacion():
            raise RenovacionNoPermitidaError(
                self._material.codigo,
                f"El tipo de material '{self._material.__class__.__name__}' no admite renovaciones bajo reglamento."
            )

        if self._cantidad_renovaciones >= self._material.max_renovaciones():
            raise RenovacionNoPermitidaError(
                self._material.codigo,
                f"Alcanzó el límite máximo de renovaciones permitidas ({self._material.max_renovaciones()})."
            )

        dias_extra = self._material.dias_prestamo()
        self._fecha_devolucion_esperada += timedelta(days=dias_extra)
        self._dias_prestamo_otorgados += dias_extra
        self._cantidad_renovaciones += 1
        return True

    def registrar_devolucion(self, fecha: Optional[date] = None) -> None:
        """Registra la devolución física del ítem y libera el material en inventario."""
        if not self._devuelto:
            self._devuelto = True
            self._fecha_devolucion_real = fecha or date.today()
            self._material.devolver()

    def calcular_dias_atraso(self, fecha_actual: Optional[date] = None) -> int:
        """Calcula cuántos días de atraso acumula el ítem según la fecha esperada."""
        fecha_fin = self._fecha_devolucion_real if self._devuelto else (fecha_actual or date.today())
        if fecha_fin > self._fecha_devolucion_esperada:
            return (fecha_fin - self._fecha_devolucion_esperada).days
        return 0

    def esta_vencido(self, fecha_actual: Optional[date] = None) -> bool:
        """Verifica si el plazo de entrega está vencido."""
        return self.calcular_dias_atraso(fecha_actual) > 0

    def calcular_multa(self, fecha_actual: Optional[date] = None, tarifa_diaria: float = 500.0) -> float:
        """Calcula el recargo por atraso ($500 CLP por cada día corrido de retraso)."""
        dias_atraso = self.calcular_dias_atraso(fecha_actual)
        return float(dias_atraso * tarifa_diaria)

    def __str__(self) -> str:
        estado = "DEVUELTO" if self._devuelto else "PENDIENTE"
        atraso = self.calcular_dias_atraso()
        info_atraso = f" [ATRASADO {atraso}d]" if (atraso > 0 and not self._devuelto) else ""
        return (
            f"Detalle N°{self._id_detalle} | Material: {self._material.codigo} ('{self._material.titulo}') | "
            f"Vence: {self._fecha_devolucion_esperada.isoformat()} | Renovaciones: {self._cantidad_renovaciones} | "
            f"Estado: {estado}{info_atraso}"
        )
