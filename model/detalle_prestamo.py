"""
========================================================================================
PAQUETE: model
MÓDULO: detalle_prestamo.py
ROL EN EL PROYECTO:
    Modela cada renglón o ítem individual dentro de una transacción de préstamo.
========================================================================================
"""

from datetime import date, timedelta
from typing import Optional
try:
    from model.material import Material
    from model.excepciones import RenovacionNoPermitidaError
except ImportError:
    from material import Material
    from excepciones import RenovacionNoPermitidaError


class DetallePrestamo:
    """
    Línea de detalle individual que preserva la trazabilidad de un material prestado.
    """

    def __init__(
        self,
        id_detalle: int,
        material: Material,
        fecha_inicio: Optional[date] = None,
        dias_prestamo: Optional[int] = None,
        devuelto: bool = False,
        cantidad_renovaciones: int = 0,
        fecha_devolucion_real: Optional[date] = None,
        fecha_devolucion_esperada: Optional[date] = None
    ):
        self._id_detalle: int = int(id_detalle)
        self._material: Material = material
        self._fecha_inicio: date = fecha_inicio or date.today()
        self._dias_prestamo_otorgados: int = (
            dias_prestamo if dias_prestamo is not None else material.dias_prestamo()
        )
        
        if fecha_devolucion_esperada is not None:
            self._fecha_devolucion_esperada: date = fecha_devolucion_esperada
        else:
            self._fecha_devolucion_esperada: date = self._fecha_inicio + timedelta(days=self._dias_prestamo_otorgados)
            
        self._fecha_devolucion_real: Optional[date] = fecha_devolucion_real
        self._cantidad_renovaciones: int = int(cantidad_renovaciones)
        self._devuelto: bool = bool(devuelto)

        # Si se crea un detalle activo, el material físico pasa automáticamente a 'prestado'
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
        if not self._devuelto:
            self._devuelto = True
            self._fecha_devolucion_real = fecha or date.today()
            self._material.devolver()

    def calcular_dias_atraso(self, fecha_actual: Optional[date] = None) -> int:
        fecha_fin = self._fecha_devolucion_real if self._devuelto else (fecha_actual or date.today())
        if fecha_fin > self._fecha_devolucion_esperada:
            return (fecha_fin - self._fecha_devolucion_esperada).days
        return 0

    def esta_vencido(self, fecha_actual: Optional[date] = None) -> bool:
        return self.calcular_dias_atraso(fecha_actual) > 0

    def calcular_multa(self, fecha_actual: Optional[date] = None, tarifa_diaria: float = 500.0) -> float:
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
