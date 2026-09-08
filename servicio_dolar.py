"""
========================================================================================
MÓDULO: servicio_dolar.py
ROL EN EL PROYECTO:
    Adaptador de servicio externo para consultar indicadores económicos en tiempo real.
    
    En el diagrama UML, actúa como un componente <<External Service>> que consume la
    API pública chilena de 'mindicador.cl' para obtener el valor del Dólar Observado.
    
    Mecanismos de Resiliencia:
    - Conexión HTTP segura con tiempo límite (timeout de 5 segundos).
    - Mecanismo de contingencia (Fallback): Si la biblioteca pierde conectividad a
      internet o la API externa no responde, el sistema no colapsa; en su lugar,
      emplea un valor en caché ($950.0 CLP o el último consultado con éxito) para
      garantizar la continuidad operativa del servicio.
========================================================================================
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional


class ServicioDolarAPI:
    """
    Cliente de integración HTTP REST con APIs de indicadores económicos oficiales.
    """

    def __init__(self, endpoint_url: str = "https://mindicador.cl/api/dolar", timeout: int = 5):
        self._endpoint_url: str = endpoint_url
        self._timeout: int = timeout
        # Valor de contingencia inicial en caso de operar sin conexión
        self._cache_valor: float = 950.0
        self._ultima_act: Optional[datetime] = None

    # ==================== PROPIEDADES (GETTERS) ====================
    @property
    def endpoint_url(self) -> str:
        """URL del endpoint REST del servicio económico."""
        return self._endpoint_url

    @property
    def timeout(self) -> int:
        """Tiempo máximo de espera en segundos antes de activar el fallback."""
        return self._timeout

    @property
    def cache_valor(self) -> float:
        """Último valor registrado del dólar disponible en memoria."""
        return self._cache_valor

    @property
    def ultima_act(self) -> Optional[datetime]:
        """Marca temporal de la última sincronización en vivo."""
        return self._ultima_act

    def _consumir_api_mindicador(self) -> float:
        """
        Envía una petición HTTP GET con User-Agent personalizado y parsea el JSON recibido.
        Compatible con los formatos habituales de la API mindicador.cl.
        """
        req = urllib.request.Request(
            self._endpoint_url,
            headers={"User-Agent": "Antigravity-BibliotecaCordillera/1.0"}
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as response:
            if response.status == 200:
                contenido = response.read().decode("utf-8")
                data = json.loads(contenido)

                # Formato tipo serie: {"serie": [{"valor": 933.82, ...}]}
                if "serie" in data and len(data["serie"]) > 0:
                    return float(data["serie"][0]["valor"])
                # Formato tipo objeto: {"dolar": {"valor": 933.82}}
                elif "dolar" in data and "valor" in data["dolar"]:
                    return float(data["dolar"]["valor"])
                # Formato simple: {"valor": 933.82}
                elif "valor" in data:
                    return float(data["valor"])

        raise ValueError("Respuesta JSON de la API no contiene el formato esperado del dólar.")

    def obtener_valor_dolar(self) -> float:
        """
        Retorna la cotización del dólar en pesos chilenos (CLP).
        
        Si ocurre cualquier excepción (falla de red, timeout, DNS, error HTTP),
        captura el fallo de forma transparente y entrega el valor cacheado.
        """
        try:
            valor = self._consumir_api_mindicador()
            self._cache_valor = valor
            self._ultima_act = datetime.now()
            return valor
        except Exception:
            # Fallback seguro para asegurar que el sistema continúe operando
            return self._cache_valor
