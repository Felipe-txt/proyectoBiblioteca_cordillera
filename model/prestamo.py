"""
========================================================================================
PAQUETE: model
MÓDULO: prestamo.py
ROL EN EL PROYECTO:
    Representa la cabecera transaccional del préstamo (equivalente al pedido u orden).
========================================================================================
"""

from datetime import datetime, date
from typing import List, Optional
try:
    from model.socio import Socio
    from model.usuario import Usuario
    from model.bibliotecaria_atencion import BibliotecariaAtencion
    from model.material import Material
    from model.detalle_prestamo import DetallePrestamo
    from model.excepciones import (
        MaterialYaPrestadoError,
        MaterialNoEncontradoError,
        SocioConMultaPendienteError
    )
except ImportError:
    from socio import Socio
    from usuario import Usuario
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
        bibliotecaria: Usuario,
        fecha_prestamo: Optional[datetime] = None,
        estado: str = "ACTIVO"
    ):
        self._id_prestamo: int = int(id_prestamo)
        self._socio: Socio = socio
        self._bibliotecaria: Usuario = bibliotecaria
        self._fecha_prestamo: datetime = fecha_prestamo or datetime.now()
        self._estado: str = estado.strip().upper()
        self._items_prestamo: List[DetallePrestamo] = []

    @property
    def id_prestamo(self) -> int:
        return self._id_prestamo

    @property
    def socio(self) -> Socio:
        return self._socio

    @property
    def bibliotecaria(self) -> Usuario:
        return self._bibliotecaria

    @property
    def fecha_prestamo(self) -> datetime:
        return self._fecha_prestamo

    @property
    def estado(self) -> str:
        return self._estado

    @estado.setter
    def estado(self, valor: str) -> None:
        self._estado = valor.strip().upper()

    @property
    def items_prestamo(self) -> List[DetallePrestamo]:
        return list(self._items_prestamo)

    def agregar_item(self, material: Material, fecha_inicio: Optional[date] = None) -> DetallePrestamo:
        """
        Agrega un nuevo recurso a la orden de préstamo.
        Valida Regla 1 (Socio sin multas) y Regla 2 (Material disponible).
        """
        if not self._socio.puede_solicitar_prestamo():
            raise SocioConMultaPendienteError(self._socio.get_rut(), self._socio.monto_multa_acumulada)

        if material.esta_prestado():
            raise MaterialYaPrestadoError(material.codigo, material.titulo)

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
        self._items_prestamo.append(detalle)

    def buscar_detalle_por_codigo(self, codigo_material: str) -> DetallePrestamo:
        cod = codigo_material.strip().upper()
        for item in self._items_prestamo:
            if item.material.codigo == cod:
                return item
        raise MaterialNoEncontradoError(
            f"El material '{codigo_material}' no forma parte del préstamo N°{self._id_prestamo}."
        )

    def registrar_devolucion_item(self, codigo_material: str, fecha_devolucion: Optional[date] = None) -> None:
        detalle = self.buscar_detalle_por_codigo(codigo_material)
        detalle.registrar_devolucion(fecha_devolucion)

        multa_item = detalle.calcular_multa(fecha_devolucion)
        if multa_item > 0:
            self._socio.registrar_multa(multa_item)

        if self.esta_completamente_devuelto():
            self._estado = "DEVUELTO"

    def renovar_item(self, codigo_material: str) -> bool:
        detalle = self.buscar_detalle_por_codigo(codigo_material)
        return detalle.renovar()

    def esta_completamente_devuelto(self) -> bool:
        if not self._items_prestamo:
            return False
        return all(item.devuelto for item in self._items_prestamo)

    def calcular_multa_total(self, fecha_consulta: Optional[date] = None, tarifa_diaria: float = 500.0) -> float:
        return sum(item.calcular_multa(fecha_consulta, tarifa_diaria) for item in self._items_prestamo)

    def cerrar_prestamo(self) -> None:
        self._estado = "CERRADO" if self.esta_completamente_devuelto() else "DEVUELTO_PARCIAL"

    def __str__(self) -> str:
        fecha_str = self._fecha_prestamo.strftime("%d/%m/%Y %H:%M")
        cant_items = len(self._items_prestamo)
        return (
            f"Préstamo N°{self._id_prestamo:04d} [{self._estado}] | Fecha: {fecha_str} | "
            f"Socio: {self._socio.get_nombre()} ({self._socio.get_rut()}) | "
            f"Atendido por: @{self._bibliotecaria.username} | Ítems: {cant_items}"
        )
