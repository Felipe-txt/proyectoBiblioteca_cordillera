"""
========================================================================================
PAQUETE: model
MÓDULO: revista.py
ROL EN EL PROYECTO:
    Subclase concreta de Material que modela publicaciones periódicas y revistas.
========================================================================================
"""

try:
    from model.material import Material
except ImportError:
    from material import Material


class Revista(Material):
    """
    Subclase que modela revistas y publicaciones periódicas.
    """

    def __init__(
        self,
        codigo: str,
        titulo: str,
        autor_o_creador: str,
        anio_publicacion: int,
        precio_base_reposicion: float,
        issn: str,
        numero_edicion: int,
        mes_publicacion: str,
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
        self._issn: str = issn.strip()
        self._numero_edicion: int = int(numero_edicion)
        self._mes_publicacion: str = mes_publicacion.strip()

    @property
    def issn(self) -> str:
        return self._issn

    @property
    def numero_edicion(self) -> int:
        return self._numero_edicion

    @property
    def mes_publicacion(self) -> str:
        return self._mes_publicacion

    def dias_prestamo(self) -> int:
        return 7

    def permite_renovacion(self) -> bool:
        return False

    def max_renovaciones(self) -> int:
        return 0

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} | ISSN: {self._issn} | Edición #{self._numero_edicion} ({self._mes_publicacion})"
