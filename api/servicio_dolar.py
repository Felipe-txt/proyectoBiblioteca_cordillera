"""
========================================================================================
PAQUETE: api
MÓDULO: servicio_dolar.py
ROL EN EL PROYECTO:
    Adaptador de servicio externo para consultar indicadores económicos en tiempo real (mindicador.cl)
    utilizando la librería oficial requests, con timeout controlado y manejo de contingencia.
========================================================================================
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import requests


class ServicioDolarAPI:
    """
    Cliente de integración HTTP REST con APIs de indicadores económicos oficiales.
    Consume https://mindicador.cl/api/dolar mediante requests, controlando timeout y contingencias.
    """

    def __init__(self, endpoint_url: str = "https://mindicador.cl/api/dolar", timeout: int = 5):
        self._endpoint_url: str = endpoint_url
        self._timeout: int = int(timeout)
        self._cache_valor: float = 950.0  # Valor de respaldo predeterminado
        self._ultima_act: Optional[datetime] = None
        self._ultima_conexion_exitosa: bool = False

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

    @property
    def ultima_conexion_exitosa(self) -> bool:
        return self._ultima_conexion_exitosa

    def _consumir_api_mindicador(self) -> float:
        """
        Realiza la petición HTTP GET a la API con timeout controlado.
        Lanza excepciones específicas de requests o ValueError si el formato es inválido.
        """
        headers = {"User-Agent": "BibliotecaCordillera/2.0"}
        response = requests.get(self._endpoint_url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        data = response.json()
        if "serie" in data and len(data["serie"]) > 0:
            return float(data["serie"][0]["valor"])
        elif "dolar" in data and "valor" in data["dolar"]:
            return float(data["dolar"]["valor"])
        elif "valor" in data:
            return float(data["valor"])

        raise ValueError("La estructura JSON de la API no contiene el formato esperado del dólar.")

    def obtener_valor_dolar(self) -> float:
        """
        Retorna la cotización del dólar observado en pesos chilenos (CLP).
        
        Mecanismos de Resiliencia:
        - Si hay conexión y respuesta válida: actualiza la caché y retorna el valor en vivo.
        - Si no hay internet, timeout o error HTTP: informa claramente el problema y retorna
          el valor de contingencia para que el sistema continúe funcionando sin interrupciones.
        """
        try:
            valor = self._consumir_api_mindicador()
            self._cache_valor = valor
            self._ultima_act = datetime.now()
            self._ultima_conexion_exitosa = True
            return valor
        except requests.exceptions.Timeout:
            self._ultima_conexion_exitosa = False
            print(f"\n[AVISO - TIEMPO DE ESPERA AGOTADO] La API '{self._endpoint_url}' tardó más de {self._timeout}s en responder.")
            print(f"                                   Se utilizará valor de contingencia: ${self._cache_valor:,.2f} CLP.")
            return self._cache_valor
        except requests.exceptions.ConnectionError:
            self._ultima_conexion_exitosa = False
            print(f"\n[AVISO - SIN CONEXIÓN A INTERNET] No fue posible conectar con la API ({self._endpoint_url}).")
            print(f"                                   Se utilizará valor de contingencia: ${self._cache_valor:,.2f} CLP.")
            return self._cache_valor
        except requests.exceptions.HTTPError as e:
            self._ultima_conexion_exitosa = False
            print(f"\n[AVISO - ERROR HTTP EN API] Respuesta no exitosa de la API: {e}")
            print(f"                            Se utilizará valor de contingencia: ${self._cache_valor:,.2f} CLP.")
            return self._cache_valor
        except Exception as e:
            self._ultima_conexion_exitosa = False
            print(f"\n[AVISO - RESPUESTA INESPERADA DE API] No se pudo procesar la respuesta: {e}")
            print(f"                                      Se utilizará valor de contingencia: ${self._cache_valor:,.2f} CLP.")
            return self._cache_valor

    def calcular_precio_reposicion_extranjero(
        self,
        precio_usd: float,
        recargo_aduanero_pct: float = 0.06
    ) -> Dict[str, Any]:
        """
        Calcula el valor de reposición de un material comprado en el extranjero en USD.
        Aplica: Precio CLP = (USD * (1 + Recargo)) * Dólar Observado.
        """
        valor_dolar = self.obtener_valor_dolar()
        costo_usd_total = precio_usd * (1.0 + recargo_aduanero_pct)
        total_clp = round(costo_usd_total * valor_dolar)

        return {
            "precio_usd": precio_usd,
            "recargo_pct": recargo_aduanero_pct * 100.0,
            "costo_usd_total": costo_usd_total,
            "valor_dolar": valor_dolar,
            "total_clp": total_clp,
            "conexion_exitosa": self._ultima_conexion_exitosa,
            "fecha_consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
