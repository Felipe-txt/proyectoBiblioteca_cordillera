"""
========================================================================================
MÓDULO: material_extranjero.py
ROL EN EL PROYECTO:
    Subclase especializada de Material para ejemplares importados o de edición
    internacional cuyo costo de adquisición y reposición está denominado en USD.
    
    Implementación Polimórfica del Cálculo de Reposición:
    - Sobrescribe calcular_valor_reposicion(valor_dolar):
      Aplica la fórmula financiera de importación:
      Costo Total (CLP) = Precio USD * (1 + Recargo Aduanero 6%) * Valor Dólar del Día
      
    Integración con API Externa:
    - Se vincula con ServicioDolarAPI para cotizar en tiempo real el tipo de cambio
      oficial del Dólar Observado en Chile.
========================================================================================
"""

from typing import Optional
from material import Material


class MaterialExtranjero(Material):
    """
    Subclase que modela recursos importados con liquidación en moneda extranjera (USD).
    """

    def __init__(
        self,
        codigo: str,
        titulo: str,
        autor_o_creador: str,
        anio_publicacion: int,
        precio_usd: float,
        pais_origen: str = "Estados Unidos",
        recargo_aduanero_pct: float = 0.06,  # 6% de arancel aduanero chileno estándar
        dias_prestamo_base: int = 14,
        permite_renovar: bool = True,
        max_renov: int = 1,
        prestado: bool = False
    ):
        # Valor de contingencia referencial en CLP (calculado a un dólar base de $950)
        precio_clp_referencial = precio_usd * (1.0 + recargo_aduanero_pct) * 950.0
        super().__init__(
            codigo=codigo,
            titulo=titulo,
            autor_o_creador=autor_o_creador,
            anio_publicacion=anio_publicacion,
            precio_base_reposicion=precio_clp_referencial,
            prestado=prestado
        )
        self._precio_usd: float = float(precio_usd)
        self._recargo_aduanero_pct: float = float(recargo_aduanero_pct)
        self._pais_origen: str = pais_origen.strip()
        self._dias_prestamo_base: int = int(dias_prestamo_base)
        self._permite_renovar: bool = bool(permite_renovar)
        self._max_renov: int = int(max_renov)

    # ==================== PROPIEDADES ESPECÍFICAS ====================
    @property
    def precio_usd(self) -> float:
        """Precio original de catálogo en dólares estadounidenses."""
        return self._precio_usd

    @property
    def recargo_aduanero_pct(self) -> float:
        """Porcentaje adicional por internación aduanera (ej: 0.06 = 6%)."""
        return self._recargo_aduanero_pct

    @property
    def pais_origen(self) -> str:
        """Nación donde fue editado o adquirido el material."""
        return self._pais_origen

    def get_precio_usd(self) -> float:
        """Retorna el monto neto en USD."""
        return self._precio_usd

    # ==================== POLIMORFISMO DE VALOR DE REPOSICIÓN ====================
    def calcular_valor_reposicion(self, valor_dolar: Optional[float] = None) -> float:
        """
        Sobrescritura polimórfica:
        Convierte el valor en USD a moneda chilena (CLP) en tiempo de ejecución,
        incorporando el arancel de aduana y el tipo de cambio oficial del día.
        """
        tipo_cambio = float(valor_dolar) if valor_dolar and valor_dolar > 0 else 950.0
        costo_total = self._precio_usd * (1.0 + self._recargo_aduanero_pct) * tipo_cambio
        self._precio_base_reposicion = costo_total
        return round(costo_total, 2)

    # ==================== POLÍTICAS DE PRÉSTAMO ====================
    def dias_prestamo(self) -> int:
        return self._dias_prestamo_base

    def permite_renovacion(self) -> bool:
        return self._permite_renovar

    def max_renovaciones(self) -> int:
        return self._max_renov

    def __str__(self) -> str:
        base = super().__str__()
        return (
            f"{base} | Origen: {self._pais_origen} | USD: ${self._precio_usd:,.2f} "
            f"(Arancel Aduanero: {self._recargo_aduanero_pct * 100:.1f}%)"
        )
