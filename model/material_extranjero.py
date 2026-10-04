"""
========================================================================================
PAQUETE: model
MÓDULO: material_extranjero.py
ROL EN EL PROYECTO:
    Subclase concreta de Material para obras importadas cotizadas en dólares (USD).
========================================================================================
"""

try:
    from model.material import Material
except ImportError:
    from material import Material


class MaterialExtranjero(Material):
    """
    Subclase que modela material importado valorizado originalmente en USD.
    """

    def __init__(
        self,
        codigo: str,
        titulo: str,
        autor_o_creador: str,
        anio_publicacion: int,
        precio_usd: float = 0.0,
        pais_origen: str = "Estados Unidos",
        recargo_aduanero_pct: float = 0.06,
        prestado: bool = False
    ):
        super().__init__(
            codigo=codigo,
            titulo=titulo,
            autor_o_creador=autor_o_creador,
            anio_publicacion=anio_publicacion,
            precio_base_reposicion=0.0,
            prestado=prestado
        )
        self._precio_usd: float = max(0.0, float(precio_usd))
        self._pais_origen: str = pais_origen.strip() if pais_origen else "Estados Unidos"
        self._recargo_aduanero_pct: float = max(0.0, float(recargo_aduanero_pct))

    @property
    def precio_usd(self) -> float:
        return self._precio_usd

    @property
    def pais_origen(self) -> str:
        return self._pais_origen

    @property
    def recargo_aduanero_pct(self) -> float:
        return self._recargo_aduanero_pct

    def dias_prestamo(self) -> int:
        return 7

    def permite_renovacion(self) -> bool:
        return True

    def max_renovaciones(self) -> int:
        return 1

    def calcular_valor_reposicion(self, valor_dolar_actual: float = 950.0) -> float:
        """
        Cálculo: Costo = USD * (1 + Arancel Aduanero) * Valor Dólar.
        """
        if valor_dolar_actual <= 0:
            valor_dolar_actual = 950.0
        return self._precio_usd * (1.0 + self._recargo_aduanero_pct) * valor_dolar_actual

    def calcular_costo_reposicion(self, valor_dolar_actual: float = 950.0) -> float:
        return self.calcular_valor_reposicion(valor_dolar_actual)

    def __str__(self) -> str:
        base = super().__str__()
        recargo_pct = self._recargo_aduanero_pct * 100
        return f"{base} | Origen: {self._pais_origen} | Precio: ${self._precio_usd:.2f} USD (+{recargo_pct:.0f}% Aduana)"
