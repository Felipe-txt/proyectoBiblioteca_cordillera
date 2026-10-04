"""
========================================================================================
PAQUETE: model
MÓDULO: boleta.py
ROL EN EL PROYECTO:
    Modela las Boletas, Comprobantes de Cobro y Órdenes de Trabajo de la Biblioteca.
    Equivalente a la OrdenTrabajo del Taller Mecánico, pero adaptado al dominio bibliotecario
    (aranceles de préstamo, multas por mora, reposición de libros/extranjeros en USD y servicios de encuadernación).
========================================================================================
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
try:
    from model.socio import Socio
    from model.usuario import Usuario
    from model.material import Material
    from model.prestamo import Prestamo
except ImportError:
    from socio import Socio
    from usuario import Usuario
    from material import Material
    from prestamo import Prestamo


class LineaDetalleBoleta:
    """
    Representa una línea o ítem de cobro/servicio dentro de la boleta u orden de trabajo.
    """

    def __init__(
        self,
        concepto: str,
        cantidad: int,
        precio_unitario: float,
        codigo_referencia: str = "",
        tipo_item: str = "SERVICIO"
    ):
        self.concepto: str = concepto.strip()
        self.cantidad: int = max(1, int(cantidad))
        self.precio_unitario: float = max(0.0, float(precio_unitario))
        self.codigo_referencia: str = codigo_referencia.strip()
        self.tipo_item: str = tipo_item.strip().upper()  # "PRESTAMO", "MULTA", "REPOSICION", "TRABAJO"

    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario

    def a_diccionario(self) -> Dict[str, Any]:
        return {
            "concepto": self.concepto,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal(),
            "codigo_referencia": self.codigo_referencia,
            "tipo_item": self.tipo_item
        }

    def __str__(self) -> str:
        return f"{self.concepto} | Cant: {self.cantidad} x ${self.precio_unitario:,.0f} = ${self.subtotal():,.0f} CLP"


class Boleta:
    """
    Representa una Boleta de Atención, Orden de Trabajo o Comprobante de Pago en la Biblioteca.
    """

    def __init__(
        self,
        numero: int,
        socio: Socio,
        usuario: Usuario,
        tipo: str = "BOLETA_PRESTAMO",
        descripcion: str = "Comprobante de atención bibliotecaria",
        fecha: Optional[datetime] = None,
        estado: str = "EMITIDA",
        iva_pct: float = 0.0,  # Las bibliotecas municipales suelen estar exentas, configurable
        descuento: float = 0.0,
        prestamo_id: Optional[int] = None
    ):
        self._numero: int = int(numero)
        self._socio: Socio = socio
        self._usuario: Usuario = usuario
        self._tipo: str = tipo.strip().upper()
        self._descripcion: str = descripcion.strip()
        self._fecha: datetime = fecha or datetime.now()
        self._estado: str = estado.strip().upper()
        self._iva_pct: float = max(0.0, float(iva_pct))
        self._descuento: float = max(0.0, float(descuento))
        self._prestamo_id: Optional[int] = prestamo_id
        self._lineas: List[LineaDetalleBoleta] = []

    # ==================== PROPIEDADES ====================
    @property
    def numero(self) -> int:
        return self._numero

    @property
    def socio(self) -> Socio:
        return self._socio

    @property
    def usuario(self) -> Usuario:
        return self._usuario

    @property
    def tipo(self) -> str:
        return self._tipo

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def fecha(self) -> datetime:
        return self._fecha

    @property
    def estado(self) -> str:
        return self._estado

    @estado.setter
    def estado(self, nuevo_estado: str) -> None:
        self._estado = nuevo_estado.strip().upper()

    @property
    def prestamo_id(self) -> Optional[int]:
        return self._prestamo_id

    @property
    def lineas(self) -> List[LineaDetalleBoleta]:
        return list(self._lineas)

    # ==================== MÉTODOS DE GESTIÓN ====================
    def agregar_linea(
        self,
        concepto: str,
        cantidad: int,
        precio_unitario: float,
        codigo_referencia: str = "",
        tipo_item: str = "SERVICIO"
    ) -> LineaDetalleBoleta:
        """Agrega un ítem de cobro a la boleta."""
        linea = LineaDetalleBoleta(
            concepto=concepto,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            codigo_referencia=codigo_referencia,
            tipo_item=tipo_item
        )
        self._lineas.append(linea)
        return linea

    def agregar_cargo_prestamo(self, material: Material, tarifa_base: float = 0.0) -> LineaDetalleBoleta:
        """Registra el cargo administrativo o registro de préstamo del material."""
        concepto = f"Préstamo: [{material.codigo}] {material.titulo}"
        return self.agregar_linea(
            concepto=concepto,
            cantidad=1,
            precio_unitario=tarifa_base,
            codigo_referencia=material.codigo,
            tipo_item="PRESTAMO"
        )

    def agregar_cargo_multa(self, dias_atraso: int, tarifa_diaria: float = 500.0, codigo_material: str = "") -> LineaDetalleBoleta:
        """Registra cobro de multa por devolución tardía."""
        concepto = f"Multa por atraso ({dias_atraso} días mora) - Ref: {codigo_material}"
        return self.agregar_linea(
            concepto=concepto,
            cantidad=dias_atraso,
            precio_unitario=tarifa_diaria,
            codigo_referencia=codigo_material,
            tipo_item="MULTA"
        )

    def agregar_cargo_reposicion(self, material: Material, valor_calculado_clp: float) -> LineaDetalleBoleta:
        """Registra cobro por reposición de material extraviado o dañado."""
        concepto = f"Reposición por extravío/deterioro: [{material.codigo}] {material.titulo}"
        return self.agregar_linea(
            concepto=concepto,
            cantidad=1,
            precio_unitario=valor_calculado_clp,
            codigo_referencia=material.codigo,
            tipo_item="REPOSICION"
        )

    def agregar_orden_trabajo_taller(self, servicio: str, horas: int, tarifa_hora: float = 3500.0) -> LineaDetalleBoleta:
        """Registra servicios técnicos de la biblioteca (empastado, restauración, plastificado, digitalización)."""
        concepto = f"Servicio Técnico Taller: {servicio} ({horas} hrs)"
        return self.agregar_linea(
            concepto=concepto,
            cantidad=horas,
            precio_unitario=tarifa_hora,
            codigo_referencia="TALLER-REST",
            tipo_item="TRABAJO"
        )

    def subtotal(self) -> float:
        """Suma de subtotales de cada línea."""
        return sum(linea.subtotal() for linea in self._lineas)

    def monto_descuento(self) -> float:
        """Monto rebajado por convenios o beneficios."""
        return min(self.subtotal(), self._descuento)

    def monto_iva(self) -> float:
        """Monto correspondiente al IVA si aplica."""
        base_imponible = max(0.0, self.subtotal() - self.monto_descuento())
        return base_imponible * self._iva_pct

    def total(self) -> float:
        """Total final a pagar en CLP."""
        return max(0.0, (self.subtotal() - self.monto_descuento()) + self.monto_iva())

    def pagar(self) -> None:
        """Marca la boleta/orden como pagada."""
        self._estado = "PAGADA"
        # Si la boleta pagaba multas del socio, podemos rebajar la deuda
        multas_pagadas = sum(
            l.subtotal() for l in self._lineas if l.tipo_item == "MULTA"
        )
        if multas_pagadas > 0:
            self._socio.pagar_multa(multas_pagadas)

    def generar_recibo_texto(self) -> str:
        """Genera una boleta / comprobante formateado en texto para consola o impresión."""
        sep = "=" * 66
        sub_sep = "-" * 66
        fecha_str = self._fecha.strftime("%d/%m/%Y %H:%M:%S")
        prestamo_str = f"#{self._prestamo_id}" if self._prestamo_id else "N/A"
        
        lineas_str = []
        for i, l in enumerate(self._lineas, start=1):
            lineas_str.append(
                f"  {i:02d}. {l.concepto[:36]:<36} | {l.cantidad:>2} x ${l.precio_unitario:>8,.0f} = ${l.subtotal():>8,.0f}"
            )
            
        detalles_formateados = "\n".join(lineas_str) if lineas_str else "  (Sin ítems registrados)"
        
        recibo = f"""
{sep}
       BIBLIOTECA MUNICIPAL CORDILLERA - COMPROBANTE OFICIAL
{sep}
 Boleta / Orden N°: {self._numero:06d}          Tipo: {self._tipo}
 Fecha Emisión    : {fecha_str}     Estado: {self._estado}
 Socio Titular    : {self._socio.get_nombre()} ({self._socio.get_rut()})
 Atendido Por     : @{self._usuario.username} ({self._usuario.obtener_rol()})
 Préstamo Asociado: {prestamo_str}
 Descripción      : {self._descripcion}
{sub_sep}
 DETALLE DE COBROS Y SERVICIOS:
{detalles_formateados}
{sub_sep}
  SUBTOTAL          : ${self.subtotal():>12,.0f} CLP
  DESCUENTO         : -${self.monto_descuento():>11,.0f} CLP
  IVA ({self._iva_pct*100:.0f}%)        : ${self.monto_iva():>12,.0f} CLP
  TOTAL A PAGAR     : ${self.total():>12,.0f} CLP
{sep}
"""
        return recibo

    def a_diccionario(self) -> Dict[str, Any]:
        return {
            "numero": self._numero,
            "tipo": self._tipo,
            "descripcion": self._descripcion,
            "fecha": self._fecha.isoformat(),
            "estado": self._estado,
            "socio_rut": self._socio.get_rut(),
            "socio_nombre": self._socio.get_nombre(),
            "usuario_username": self._usuario.username,
            "prestamo_id": self._prestamo_id,
            "iva_pct": self._iva_pct,
            "descuento": self._descuento,
            "subtotal": self.subtotal(),
            "iva": self.monto_iva(),
            "total": self.total(),
            "lineas": [l.a_diccionario() for l in self._lineas]
        }

    def __str__(self) -> str:
        return f"Boleta N°{self._numero:06d} [{self._tipo}] - Socio: {self._socio.get_rut()} - Total: ${self.total():,.0f} CLP ({self._estado})"
