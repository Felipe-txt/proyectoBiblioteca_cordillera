"""
========================================================================================
MÓDULO: material.py
ROL EN EL PROYECTO:
    Clase Base Abstracta (ABC) para todos los recursos del catálogo bibliográfico.
    
    En el diagrama UML, representa el núcleo del "Dominio de Materiales (Polimorfismo)":
    
                             Material (Abstracta)
             ┌───────────────┼───────────────┬────────────────┐
           Libro          Revista       Multimedia       Extranjero
         (14d / 1ren)   (7d / 0ren)     (3d / 0ren)    (USD + 6% aduana)
         
    Responsabilidades Principales:
    - Encapsular metadatos universales: código de barras/inventario, título, autor, año,
      precio base de reposición y estado físico de disponibilidad (_prestado).
    - Definir métodos abstractos que cada subclase debe implementar obligatoriamente:
      dias_prestamo(), permite_renovacion(), max_renovaciones().
    - Administrar el ciclo de préstamo: prestar() y devolver().
    
    Regla Infranqueable Asociada:
    - Regla N°2 (Disponibilidad de Material): Si se intenta prestar un ejemplar que ya
      se encuentra en estado '_prestado=True', el método prestar() lanza de inmediato
      MaterialYaPrestadoError.
========================================================================================
"""

from abc import ABC, abstractmethod
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
        # Atributo protegido que controla si el ejemplar físico está en poder de un socio
        self._prestado: bool = bool(prestado)

    # ==================== PROPIEDADES (GETTERS) ====================
    @property
    def codigo(self) -> str:
        """Código de inventario único (ej: 'LIB-001', 'REV-001', 'DVD-001')."""
        return self._codigo

    @property
    def titulo(self) -> str:
        """Título formal de la obra o ejemplar."""
        return self._titulo

    @property
    def autor_o_creador(self) -> str:
        """Autor, editor, director o creador principal."""
        return self._autor_o_creador

    @property
    def anio_publicacion(self) -> int:
        """Año de edición o estreno."""
        return self._anio_publicacion

    @property
    def precio_base_reposicion(self) -> float:
        """Valor base en pesos chilenos para cobrar en caso de pérdida o deterioro."""
        return self._precio_base_reposicion

    # ==================== CONTRATO POLIMÓRFICO (MÉTODOS ABSTRACTOS) ====================
    @abstractmethod
    def dias_prestamo(self) -> int:
        """
        Duración estándar en días corridos otorgados al socio según el tipo de material:
        - Libros: 14 días
        - Revistas: 7 días
        - Multimedia: 3 días
        """
        pass

    @abstractmethod
    def permite_renovacion(self) -> bool:
        """Indica si la política del material admite solicitar prórrogas."""
        pass

    @abstractmethod
    def max_renovaciones(self) -> int:
        """Cantidad tope de renovaciones consecutivas permitidas antes de la devolución obligatoria."""
        pass

    # ==================== GESTIÓN DE DISPONIBILIDAD ====================
    def prestar(self) -> None:
        """
        Transición de estado: DISPONIBLE -> PRESTADO.
        
        Regla Infranqueable N°2:
        Si el material ya se encuentra prestado, se bloquea la operación y se lanza
        MaterialYaPrestadoError.
        """
        if self._prestado:
            raise MaterialYaPrestadoError(self._codigo)
        self._prestado = True

    def devolver(self) -> None:
        """
        Transición de estado: PRESTADO -> DISPONIBLE.
        Reintegra el ejemplar a las estanterías de la biblioteca.
        """
        self._prestado = False

    def esta_prestado(self) -> bool:
        """Retorna True si el material no se encuentra en inventario físico disponible."""
        return self._prestado

    def calcular_valor_reposicion(self) -> float:
        """
        Calcula el valor en dinero en caso de daño total o extravío.
        Por defecto retorna el precio base nacional. Las subclases (ej. extranjero)
        pueden sobreescribir este método aplicando tipos de cambio y recargos aduaneros.
        """
        return self._precio_base_reposicion

    def __str__(self) -> str:
        estado = "Prestado" if self._prestado else "Disponible"
        return (
            f"[{self.__class__.__name__}] {self._codigo} - '{self._titulo}' por {self._autor_o_creador} "
            f"({self._anio_publicacion}) | Reposición: ${self.calcular_valor_reposicion():,.0f} CLP | {estado}"
        )
