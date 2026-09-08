"""
Módulo Libro
Representa los libros del catálogo de la biblioteca.
Política: 14 días de préstamo base y hasta 1 renovación autorizada (14 días más).
"""

from material import Material


class Libro(Material):
    """Subclase representativa de libros impresos."""

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

    @property
    def isbn(self) -> str:
        return self._isbn

    @property
    def editorial(self) -> str:
        return self._editorial

    @property
    def numero_paginas(self) -> int:
        return self._numero_paginas

    def dias_prestamo(self) -> int:
        """Los libros se prestan por 14 días corridos."""
        return 14

    def permite_renovacion(self) -> bool:
        """Los libros sí admiten renovación."""
        return True

    def max_renovaciones(self) -> int:
        """Límite de 1 renovación adicional."""
        return 1

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} | ISBN: {self._isbn} | Editorial: {self._editorial} ({self._numero_paginas} págs)"
