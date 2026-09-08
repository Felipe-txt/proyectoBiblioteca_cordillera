"""
Módulo Material
Clase base abstracta para todo ítem bibliográfico o multimedia del catálogo.
Define la interfaz polimórfica para duración de préstamos y políticas de renovación.
"""

from abc import ABC, abstractmethod
from excepciones import MaterialYaPrestadoError


class Material(ABC):
    """Clase base abstracta representativa de cualquier material de la biblioteca."""

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

    @property
    def autor_o_creador(self) -> str:
        return self._autor_o_creador

    @property
    def anio_publicacion(self) -> int:
        return self._anio_publicacion

    @property
    def precio_base_reposicion(self) -> float:
        return self._precio_base_reposicion

    @abstractmethod
    def dias_prestamo(self) -> int:
        """Cantidad estándar de días asignados por préstamo para este tipo de material."""
        pass

    @abstractmethod
    def permite_renovacion(self) -> bool:
        """Indica si el material es elegible para extensiones de plazo."""
        pass

    @abstractmethod
    def max_renovaciones(self) -> int:
        """Número máximo de renovaciones permitidas consecutivamente."""
        pass

    def prestar(self) -> None:
        """
        Marca el material como prestado.
        Regla Infranqueable N°2: No se puede prestar un material que ya está en préstamo.
        """
        if self._prestado:
            raise MaterialYaPrestadoError(self._codigo)
        self._prestado = True

    def devolver(self) -> None:
        """Marca el material como disponible en estantería."""
        self._prestado = False

    def esta_prestado(self) -> bool:
        """Indica el estado actual de disponibilidad."""
        return self._prestado

    def calcular_valor_reposicion(self) -> float:
        """Retorna el costo de reposición estándar en moneda local (CLP)."""
        return self._precio_base_reposicion

    def __str__(self) -> str:
        estado = "Prestado" if self._prestado else "Disponible"
        return (
            f"[{self.__class__.__name__}] {self._codigo} - '{self._titulo}' por {self._autor_o_creador} "
            f"({self._anio_publicacion}) | Reposición: ${self.calcular_valor_reposicion():,.0f} CLP | {estado}"
        )
