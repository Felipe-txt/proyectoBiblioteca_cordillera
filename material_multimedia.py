"""
Módulo MaterialMultimedia
Representa ítems audiovisuales (DVD, CD, Blu-ray).
Política: 3 días de préstamo base por alta rotación de público y 0 renovaciones permitidas.
"""

from material import Material


class MaterialMultimedia(Material):
    """Subclase representativa de discos ópticos y contenidos audiovisuales."""

    def __init__(
        self,
        codigo: str,
        titulo: str,
        autor_o_creador: str,
        anio_publicacion: int,
        precio_base_reposicion: float,
        formato: str = "DVD",
        duracion_minutos: int = 120,
        clasificacion_edad: str = "TE",
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
        self._formato: str = formato.strip().upper()
        self._duracion_minutos: int = int(duracion_minutos)
        self._clasificacion_edad: str = clasificacion_edad.strip().upper()

    @property
    def formato(self) -> str:
        return self._formato

    @property
    def duracion_minutos(self) -> int:
        return self._duracion_minutos

    @property
    def clasificacion_edad(self) -> str:
        return self._clasificacion_edad

    def dias_prestamo(self) -> int:
        """Los ítems multimedia se prestan por un plazo máximo de 3 días."""
        return 3

    def permite_renovacion(self) -> bool:
        """Los ítems multimedia no admiten renovación."""
        return False

    def max_renovaciones(self) -> int:
        """0 renovaciones permitidas."""
        return 0

    def __str__(self) -> str:
        base = super().__str__()
        return (
            f"{base} | Formato: {self._formato} | Duración: {self._duracion_minutos} min | "
            f"Clasificación: {self._clasificacion_edad}"
        )
