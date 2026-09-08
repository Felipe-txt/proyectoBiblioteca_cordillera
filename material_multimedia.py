"""
========================================================================================
MÓDULO: material_multimedia.py
ROL EN EL PROYECTO:
    Subclase concreta de Material que representa contenidos audiovisuales y ópticos
    (DVD, CD de música, Blu-ray, documentales).
    
    Implementación de Políticas Polimórficas:
    - dias_prestamo(): 3 días corridos.
    - permite_renovacion(): False (No admite renovaciones debido a su alta rotación).
    - max_renovaciones(): 0 renovaciones.
    
    Excepción Asociada:
    - Si se intenta renovar un material multimedia, el sistema dispara
      RenovacionNoPermitidaError impidiendo la extensión.
========================================================================================
"""

from material import Material


class MaterialMultimedia(Material):
    """
    Subclase que modela recursos audiovisuales (películas, documentales, música).
    """

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

    # ==================== PROPIEDADES ESPECÍFICAS ====================
    @property
    def formato(self) -> str:
        """Soporte físico (ej: 'DVD', 'BLU-RAY', 'CD')."""
        return self._formato

    @property
    def duracion_minutos(self) -> int:
        """Tiempo de reproducción en minutos."""
        return self._duracion_minutos

    @property
    def clasificacion_edad(self) -> str:
        """Calificación de edad (ej: 'TE' Todo Espectador, '+14', '+18')."""
        return self._clasificacion_edad

    # ==================== IMPLEMENTACIÓN DE MÉTODOS POLIMÓRFICOS ====================
    def dias_prestamo(self) -> int:
        """Política: 3 días corridos por tratarse de ítems de consumo rápido y alta rotación."""
        return 3

    def permite_renovacion(self) -> bool:
        """Política: No admite renovación."""
        return False

    def max_renovaciones(self) -> int:
        """Política: 0 renovaciones permitidas."""
        return 0

    def __str__(self) -> str:
        base = super().__str__()
        return (
            f"{base} | Formato: {self._formato} | Duración: {self._duracion_minutos} min | "
            f"Clasificación: {self._clasificacion_edad}"
        )
