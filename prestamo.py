"""
========================================================================================
MÓDULO: prestamo.py
ROL EN EL PROYECTO:
    Representa la cabecera transaccional del préstamo (equivalente al encabezado de
    una boleta o contrato de préstamo).
    
    En el diseño UML:
    - Agrupa al Socio solicitante.
    - Agrupa a la BibliotecariaAtencion que atendió en el mesón.
    - Contiene una colección de instancias DetallePrestamo (1 a N materiales).
    
    Responsabilidades Principales:
    - Coordinar la incorporación de múltiples ítems en una única visita.
    - Asegurar que el socio cumpla la Regla N°1 antes de añadir cada ítem.
    - Procesar devoluciones individuales o masivas, cargando automáticamente multas
      al socio si hubo retraso en la entrega.
    - Supervisar el estado global de la transacción: ACTIVO, DEVUELTO, CERRADO.
    
    Excepciones Asociadas:
    - SocioConMultaPendienteError: Si el socio tiene multas pendientes al agregar ítems.
    - MaterialYaPrestadoError: Si alguno de los materiales pedidos ya está prestado.
    - MaterialNoEncontradoError: Si se busca un código que no pertenece a este préstamo.
========================================================================================
"""

from datetime import datetime, date
from typing import List, Optional
from socio import Socio
from bibliotecaria_atencion import BibliotecariaAtencion
from material import Material
from detalle_prestamo import DetallePrestamo
from excepciones import (
    MaterialYaPrestadoError,
    MaterialNoEncontradoError,
    SocioConMultaPendienteError
)


class Prestamo:
    """
    Cabecera transaccional que consolida el préstamo de uno o varios materiales.
    """

    def __init__(
        self,
        id_prestamo: int,
        socio: Socio,
        bibliotecaria: BibliotecariaAtencion,
        fecha_prestamo: Optional[datetime] = None,
        estado: str = "ACTIVO"
    ):
        self._id_prestamo: int = int(id_prestamo)
        self._socio: Socio = socio
        self._bibliotecaria: BibliotecariaAtencion = bibliotecaria
        self._fecha_prestamo: datetime = fecha_prestamo or datetime.now()
        self._estado: str = estado.strip().upper()
        # Lista de detalles (Composición UML)
        self._items_prestamo: List[DetallePrestamo] = []

    # ==================== PROPIEDADES (GETTERS) ====================
    @property
    def id_prestamo(self) -> int:
        """Identificador numérico único de la transacción de préstamo."""
        return self._id_prestamo

    @property
    def socio(self) -> Socio:
        """Socio que retiró el material."""
        return self._socio

    @property
    def bibliotecaria(self) -> BibliotecariaAtencion:
        """Funcionaria responsable de atender y autorizar la entrega."""
        return self._bibliotecaria

    @property
    def fecha_prestamo(self) -> datetime:
        """Fecha y hora exacta en que se concretó la operación."""
        return self._fecha_prestamo

    @property
    def estado(self) -> str:
        """Estado de la transacción ('ACTIVO', 'DEVUELTO', 'CERRADO')."""
        return self._estado

    @estado.setter
    def estado(self, valor: str) -> None:
        self._estado = valor.strip().upper()

    @property
    def items_prestamo(self) -> List[DetallePrestamo]:
        """Copia de la lista de detalles para salvaguardar el encapsulamiento."""
        return list(self._items_prestamo)

    # ==================== GESTIÓN DE ÍTEMS Y TRANSACCIONES ====================
    def agregar_item(self, material: Material, fecha_inicio: Optional[date] = None) -> DetallePrestamo:
        """
        Agrega un nuevo recurso a la orden de préstamo.
        
        Reglas Infranqueables Verificadas:
        - Regla 1: Valida que el socio no mantenga sanciones o multas impagas.
          Si no puede, lanza SocioConMultaPendienteError.
        - Regla 2: Valida que el material no esté prestado actualmente.
          Si ya está en uso, lanza MaterialYaPrestadoError.
        """
        if not self._socio.puede_solicitar_prestamo():
            raise SocioConMultaPendienteError(self._socio.get_rut(), self._socio.monto_multa_acumulada)

        if material.esta_prestado():
            raise MaterialYaPrestadoError(material.codigo)

        id_detalle = len(self._items_prestamo) + 1
        fecha_ini = fecha_inicio or self._fecha_prestamo.date()
        
        detalle = DetallePrestamo(
            id_detalle=id_detalle,
            material=material,
            fecha_inicio=fecha_ini
        )
        self._items_prestamo.append(detalle)
        return detalle

    def agregar_detalle_existente(self, detalle: DetallePrestamo) -> None:
        """Permite inyectar detalles ya instanciados (por ejemplo, al hidratar datos desde SQLite)."""
        self._items_prestamo.append(detalle)

    def buscar_detalle_por_codigo(self, codigo_material: str) -> DetallePrestamo:
        """
        Localiza la línea de detalle correspondiente a un código de material.
        Si el material no forma parte de este préstamo, lanza MaterialNoEncontradoError.
        """
        cod = codigo_material.strip().upper()
        for item in self._items_prestamo:
            if item.material.codigo == cod:
                return item
        raise MaterialNoEncontradoError(
            f"El material '{codigo_material}' no forma parte del préstamo N°{self._id_prestamo}."
        )

    def registrar_devolucion_item(self, codigo_material: str, fecha_devolucion: Optional[date] = None) -> None:
        """
        Procesa la recepción de un material particular del préstamo.
        
        Acciones automáticas:
        1. Marca el detalle como devuelto y libera el material en inventario.
        2. Calcula si se devengó multa por días de atraso.
        3. Si hubo atraso, carga la multa automáticamente a la cuenta del socio.
        4. Si todos los ítems fueron devueltos, actualiza el estado general a 'DEVUELTO'.
        """
        detalle = self.buscar_detalle_por_codigo(codigo_material)
        detalle.registrar_devolucion(fecha_devolucion)

        # Si generó mora, se aplica el cobro al socio
        multa_item = detalle.calcular_multa(fecha_devolucion)
        if multa_item > 0:
            self._socio.registrar_multa(multa_item)

        if self.esta_completamente_devuelto():
            self._estado = "DEVUELTO"

    def renovar_item(self, codigo_material: str) -> bool:
        """Aplica una renovación de plazo sobre el ítem solicitado."""
        detalle = self.buscar_detalle_por_codigo(codigo_material)
        return detalle.renovar()

    def esta_completamente_devuelto(self) -> bool:
        """Comprueba si todos los ítems asociados al préstamo ya fueron reintegrados."""
        if not self._items_prestamo:
            return False
        return all(item.devuelto for item in self._items_prestamo)

    def calcular_multa_total(self, fecha_consulta: Optional[date] = None, tarifa_diaria: float = 500.0) -> float:
        """Consolida la suma de multas pendientes de todos los ítems de esta transacción."""
        return sum(item.calcular_multa(fecha_consulta, tarifa_diaria) for item in self._items_prestamo)

    def cerrar_prestamo(self) -> None:
        """Cierra el ciclo administrativo de la transacción."""
        self._estado = "CERRADO" if self.esta_completamente_devuelto() else "DEVUELTO_PARCIAL"

    def __str__(self) -> str:
        fecha_str = self._fecha_prestamo.strftime("%d/%m/%Y %H:%M")
        cant_items = len(self._items_prestamo)
        return (
            f"Préstamo N°{self._id_prestamo:04d} [{self._estado}] | Fecha: {fecha_str} | "
            f"Socio: {self._socio.get_nombre()} ({self._socio.get_rut()}) | "
            f"Atendido por: @{self._bibliotecaria.username} | Ítems: {cant_items}"
        )
