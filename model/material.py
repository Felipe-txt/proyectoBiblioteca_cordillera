"""
========================================================================================
PAQUETE: model
MÓDULO: material.py
ROL EN EL PROYECTO:
    Clase Base Abstracta (ABC) para todos los recursos del catálogo bibliográfico.
========================================================================================
"""

from abc import ABC, abstractmethod
try:
    from model.excepciones import MaterialYaPrestadoError
except ImportError:
    from excepciones import MaterialYaPrestadoError


class Material(ABC):
    """
    Clase abstracta que define la interfaz común y comportamiento general de un ítem del catálogo.
    """

    def __init__(
        self,
        codigo: str,
        titulo: str,
        autor_o_creador: str,
        anio_publicacion: int,
        precio_base_reposicion: float,
        prestado: bool = False
    ):
        self._codigo: str = codigo.strip().upper()
        self._titulo: str = titulo.strip()
        self._autor_o_creador: str = autor_o_creador.strip()
        self._anio_publicacion: int = int(anio_publicacion)
        self._precio_base_reposicion: float = max(0.0, float(precio_base_reposicion))
        self._prestado: bool = bool(prestado)

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def titulo(self) -> str:
        return self._titulo

    @titulo.setter
    def titulo(self, nuevo_titulo: str) -> None:
        if not nuevo_titulo or not nuevo_titulo.strip():
            raise ValueError("El título no puede estar vacío.")
        self._titulo = nuevo_titulo.strip()

    @property
    def autor_o_creador(self) -> str:
        return self._autor_o_creador

    @autor_o_creador.setter
    def autor_o_creador(self, nuevo_autor: str) -> None:
        if not nuevo_autor or not nuevo_autor.strip():
            raise ValueError("El autor/creador no puede estar vacío.")
        self._autor_o_creador = nuevo_autor.strip()

    @property
    def anio_publicacion(self) -> int:
        return self._anio_publicacion

    @anio_publicacion.setter
    def anio_publicacion(self, nuevo_anio: int) -> None:
        self._anio_publicacion = int(nuevo_anio)

    @property
    def precio_base_reposicion(self) -> float:
        return self._precio_base_reposicion

    @precio_base_reposicion.setter
    def precio_base_reposicion(self, nuevo_precio: float) -> None:
        if nuevo_precio < 0:
            raise ValueError("El precio de reposición no puede ser negativo.")
        self._precio_base_reposicion = float(nuevo_precio)

    @abstractmethod
    def dias_prestamo(self) -> int:
        pass

    @abstractmethod
    def permite_renovacion(self) -> bool:
        pass

    @abstractmethod
    def max_renovaciones(self) -> int:
        pass

    def esta_disponible(self) -> bool:
        return not self._prestado

    def esta_prestado(self) -> bool:
        return self._prestado

    def prestar(self) -> None:
        if self._prestado:
            raise MaterialYaPrestadoError(self._codigo, self._titulo)
        self._prestado = True

    def devolver(self) -> None:
        self._prestado = False

    def calcular_valor_reposicion(self, valor_dolar_actual: float = 0.0) -> float:
        return self._precio_base_reposicion

    def calcular_costo_reposicion(self, valor_dolar_actual: float = 0.0) -> float:
        return self.calcular_valor_reposicion(valor_dolar_actual)

    def __str__(self) -> str:
        estado = "PRESTADO" if self._prestado else "DISPONIBLE"
        return f"[{self._codigo}] '{self._titulo}' por {self._autor_o_creador} ({self._anio_publicacion}) - [{estado}]"
