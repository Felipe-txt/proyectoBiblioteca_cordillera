"""
========================================================================================
PAQUETE: model
MÓDULO: libro.py
ROL EN EL PROYECTO:
    Subclase concreta de Material que representa los libros físicos del catálogo.
========================================================================================
"""

try:
    from model.material import Material
except ImportError:
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
        return 14

    def permite_renovacion(self) -> bool:
        return True

    def max_renovaciones(self) -> int:
        return 1

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} | ISBN: {self._isbn} | Editorial: {self._editorial} ({self._numero_paginas} págs)"
