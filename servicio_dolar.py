"""
Módulo ServicioDolarAPI
Permite consultar el tipo de cambio oficial (Dólar Observado) en tiempo real
a través de APIs públicas, incorporando caché y fallback seguro.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional


class ServicioDolarAPI:
    """Cliente de integración con APIs de indicadores económicos para cotización USD."""

    def __init__(self, endpoint_url: str = "https://mindicador.cl/api/dolar", timeout: int = 5):
        self._endpoint_url: str = endpoint_url
        self._timeout: int = timeout
        self._cache_valor: float = 950.0
        self._ultima_act: Optional[datetime] = None

    @property
    def endpoint_url(self) -> str:
        return self._endpoint_url

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def cache_valor(self) -> float:
        return self._cache_valor

    @property
    def ultima_act(self) -> Optional[datetime]:
        return self._ultima_act

    def _consumir_api_mindicador(self) -> float:
        """Efectúa la petición HTTP GET a la API REST de indicadores chilenos."""
        req = urllib.request.Request(
            self._endpoint_url,
            headers={"User-Agent": "Antigravity-BibliotecaCordillera/1.0"}
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as response:
            if response.status == 200:
                contenido = response.read().decode("utf-8")
                data = json.loads(contenido)

                if "serie" in data and len(data["serie"]) > 0:
                    return float(data["serie"][0]["valor"])
                elif "dolar" in data and "valor" in data["dolar"]:
                    return float(data["dolar"]["valor"])
                elif "valor" in data:
                    return float(data["valor"])

        raise ValueError("Respuesta JSON de la API no contiene el formato esperado del dólar.")

    def obtener_valor_dolar(self) -> float:
        """
        Retorna la cotización del dólar en CLP.
        Si la conexión falla, provee el valor en caché para mantener la continuidad del sistema.
        """
        try:
            valor = self._consumir_api_mindicador()
            self._cache_valor = valor
            self._ultima_act = datetime.now()
            return valor
        except Exception:
            # Fallback seguro
            return self._cache_valor
