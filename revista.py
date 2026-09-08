"""
========================================================================================
MÓDULO: revista.py
ROL EN EL PROYECTO:
    Subclase concreta de Material que representa publicaciones periódicas y revistas.
    
    Implementación de Políticas Polimórficas:
    - dias_prestamo(): 7 días corridos (1 semana).
    - permite_renovacion(): False (No permite renovaciones bajo ninguna circunstancia).
    - max_renovaciones(): 0 renovaciones.
    
    Excepción Asociada:
    - Si un socio solicita renovar una revista, DetallePrestamo detecta que
      permite_renovacion() es False y lanza RenovacionNoPermitidaError.
========================================================================================
"""

from material import Material


class Revista(Material):
    """
    Subclase que modela revistas científicas, de divulgación, prensa o magazín.
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

    # ==================== PROPIEDADES ESPECÍFICAS ====================
    @property
    def issn(self) -> str:
        """Código ISSN (International Standard Serial Number)."""
        return self._issn

    @property
    def numero_edicion(self) -> int:
        """Número de entrega, tiraje o edición."""
        return self._numero_edicion

    @property
    def mes_publicacion(self) -> str:
        """Mes de publicación (ej: 'Agosto 2024')."""
        return self._mes_publicacion

    # ==================== IMPLEMENTACIÓN DE MÉTODOS POLIMÓRFICOS ====================
    def dias_prestamo(self) -> int:
        """Política: 7 días corridos."""
        return 7

    def permite_renovacion(self) -> bool:
        """Política: Las revistas no admiten renovación por rotación editorial."""
        return False

    def max_renovaciones(self) -> int:
        """Política: 0 renovaciones permitidas."""
        return 0

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} | ISSN: {self._issn} | Edición N°{self._numero_edicion} ({self._mes_publicacion})"
