"""
========================================================================================
PAQUETE: model
MÓDULO: material_multimedia.py
ROL EN EL PROYECTO:
    Subclase concreta de Material para recursos audiovisuales (CD, DVD, Blu-Ray).
========================================================================================
"""

try:
    from model.material import Material
except ImportError:
    from material import Material


class MaterialMultimedia(Material):
    """
    Subclase que modela recursos audiovisuales (DVD, Blu-Ray, CD de Audio).
    """

    def __init__(
        self,
        codigo: str,
        titulo: str,
        autor_o_creador: str,
        anio_publicacion: int,
        precio_base_reposicion: float,
        formato: str,
        duracion_minutos: int,
        clasificacion_edad: str,
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
        self._clasificacion_edad: str = clasificacion_edad.strip()

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
        return 3

    def permite_renovacion(self) -> bool:
        return False

    def max_renovaciones(self) -> int:
        return 0

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} | Formato: {self._formato} ({self._duracion_minutos} mins) | Censura: {self._clasificacion_edad}"
