"""
========================================================================================
MÓDULO: libro.py
ROL EN EL PROYECTO:
    Subclase concreta de Material que representa los libros físicos del catálogo.
    
    Implementación de Políticas Polimórficas:
    - dias_prestamo(): 14 días corridos.
    - permite_renovacion(): True (los libros son el único material general renovable).
    - max_renovaciones(): 1 renovación (otorga 14 días adicionales, totalizando máx. 28 días).
    
    Atributos Propios:
    - isbn: Identificador bibliográfico internacional estandarizado.
    - editorial: Casa editora del volumen.
    - numero_paginas: Extensión de la obra.
========================================================================================
"""

from material import Material


class Libro(Material):
    """
    Subclase que modela libros impresos tradicionales.
    """

    def __init__(
        self,
        codigo: str,
        titulo: str,
        autor_o_creador: str,
        anio_publicacion: int,
        precio_base_reposicion: float,
        isbn: str,
        editorial: str,
        numero_paginas: int,
        prestado: bool = False
    ):
        super().__init__(
            codigo=codigo,
            titulo=titulo,
            autor_o_creador=autor_o_creador,
            anio_publicacion=anio_publicacion,
            precio_base_reposicion=precio_base_reposicion,
            prestado=prestado
        )
        self._isbn: str = isbn.strip()
        self._editorial: str = editorial.strip()
        self._numero_paginas: int = int(numero_paginas)

    # ==================== PROPIEDADES ESPECÍFICAS ====================
    @property
    def isbn(self) -> str:
        """Código ISBN (International Standard Book Number)."""
        return self._isbn

    @property
    def editorial(self) -> str:
        """Sello editorial que publicó la edición."""
        return self._editorial

    @property
    def numero_paginas(self) -> int:
        """Cantidad total de páginas numeradas."""
        return self._numero_paginas

    # ==================== IMPLEMENTACIÓN DE MÉTODOS POLIMÓRFICOS ====================
    def dias_prestamo(self) -> int:
        """Política: Los libros se prestan por 14 días corridos (2 semanas)."""
        return 14

    def permite_renovacion(self) -> bool:
        """Política: Sí admite extensión de plazo si no está reservado."""
        return True

    def max_renovaciones(self) -> int:
        """Política: Límite estricto de 1 renovación (14 días más)."""
        return 1

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} | ISBN: {self._isbn} | Editorial: {self._editorial} ({self._numero_paginas} págs)"
