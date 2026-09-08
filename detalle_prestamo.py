"""
========================================================================================
MÓDULO: detalle_prestamo.py
ROL EN EL PROYECTO:
    Modela cada renglón o ítem individual dentro de una transacción de préstamo.
    
    En el diagrama UML, implementa el patrón de composición Cabecera-Detalle:
    Prestamo "1" *-- "1..*" DetallePrestamo : contiene líneas
    
    Responsabilidades Principales:
    - Asociar un Material concreto con sus fechas críticas: fecha_inicio,
      fecha_devolucion_esperada y fecha_devolucion_real.
    - Gestionar el contador de renovaciones utilizadas y aplicar prórrogas de plazo.
    - Calcular el atraso en días corridos y liquidar la multa correspondiente
      ($500 CLP por cada día de mora).
      
    Excepciones Asociadas:
    - RenovacionNoPermitidaError:
      * Si el material ya fue devuelto.
      * Si el material no admite renovación según su clase (Revista, Multimedia).
      * Si se superó el límite de renovaciones autorizadas (ej. más de 1 en Libros).
========================================================================================
"""

from datetime import date, timedelta
from typing import Optional
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
        fecha_devolucion_real: Optional[date] = None
    ):
        self._id_detalle: int = int(id_detalle)
        self._material: Material = material
        self._fecha_inicio: date = fecha_inicio or date.today()
        # Se asigna la duración base polimórfica definida por el tipo de material
        self._dias_prestamo_otorgados: int = (
            dias_prestamo if dias_prestamo is not None else material.dias_prestamo()
        )
        # La fecha esperada de entrega se calcula sumando los días otorgados
        self._fecha_devolucion_esperada: date = self._fecha_inicio + timedelta(days=self._dias_prestamo_otorgados)
        self._fecha_devolucion_real: Optional[date] = fecha_devolucion_real
        self._cantidad_renovaciones: int = int(cantidad_renovaciones)
        self._devuelto: bool = bool(devuelto)

        # Si se crea un detalle activo, el material físico pasa automáticamente a 'prestado'
        if not self._devuelto and not self._material.esta_prestado():
            self._material.prestar()

    # ==================== PROPIEDADES (GETTERS) ====================
    @property
    def id_detalle(self) -> int:
        """Número de línea dentro del préstamo."""
        return self._id_detalle

    @property
    def material(self) -> Material:
        """Instancia del recurso prestado."""
        return self._material

    @property
    def fecha_inicio(self) -> date:
        """Fecha en que se retiró el material."""
        return self._fecha_inicio

    @property
    def dias_prestamo_otorgados(self) -> int:
        """Plazo total acumulado en días (incluyendo posibles renovaciones)."""
        return self._dias_prestamo_otorgados

    @property
    def fecha_devolucion_esperada(self) -> date:
        """Fecha límite para devolver sin generar multas."""
        return self._fecha_devolucion_esperada

    @property
    def fecha_devolucion_real(self) -> Optional[date]:
        """Fecha efectiva en que el socio entregó el ítem en la biblioteca."""
        return self._fecha_devolucion_real

    @property
    def cantidad_renovaciones(self) -> int:
        """Contador de prórrogas aplicadas sobre este ejemplar."""
        return self._cantidad_renovaciones

    @property
    def devuelto(self) -> bool:
        """Indica si el ítem ya fue recibido físicamente de regreso."""
        return self._devuelto

    # ==================== LÓGICA DE RENOVACIÓN ====================
    def renovar(self) -> bool:
        """
        Aplica una renovación sobre el ítem evaluando las reglas del negocio.
        
        Validaciones y Excepciones:
        1. Si ya está devuelto -> Lanza RenovacionNoPermitidaError.
        2. Si el material no admite renovación (permite_renovacion() == False)
           -> Lanza RenovacionNoPermitidaError.
        3. Si alcanzó el tope máximo (max_renovaciones())
           -> Lanza RenovacionNoPermitidaError.
           
        Si aprueba:
        - Añade los días correspondientes a la fecha esperada.
        - Incrementa el contador de renovaciones.
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

    # ==================== DEVOLUCIÓN Y CÁLCULO DE MULTAS ====================
    def registrar_devolucion(self, fecha: Optional[date] = None) -> None:
        """
        Recepciona el ejemplar, sella la fecha real de entrega y libera el material en inventario.
        """
        if not self._devuelto:
            self._devuelto = True
            self._fecha_devolucion_real = fecha or date.today()
            # El material vuelve a estar disponible para otros lectores
            self._material.devolver()

    def calcular_dias_atraso(self, fecha_actual: Optional[date] = None) -> int:
        """
        Determina la cantidad de días de demora transcurridos respecto a la fecha esperada.
        Si la fecha de entrega o consulta es anterior o igual a la esperada, retorna 0.
        """
        fecha_fin = self._fecha_devolucion_real if self._devuelto else (fecha_actual or date.today())
        if fecha_fin > self._fecha_devolucion_esperada:
            return (fecha_fin - self._fecha_devolucion_esperada).days
        return 0

    def esta_vencido(self, fecha_actual: Optional[date] = None) -> bool:
        """Retorna True si el plazo de devolución se encuentra expirado."""
        return self.calcular_dias_atraso(fecha_actual) > 0

    def calcular_multa(self, fecha_actual: Optional[date] = None, tarifa_diaria: float = 500.0) -> float:
        """
        Aplica el arancel punitorio por retraso:
        Multa = Días de Atraso * Tarifa Diaria ($500 CLP/día).
        """
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
