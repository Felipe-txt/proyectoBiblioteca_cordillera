"""
========================================================================================
MÓDULO: persona.py
ROL EN EL PROYECTO:
    Clase Base Abstracta (ABC) para todo ser humano registrado en el sistema.
    
    En el diagrama UML de Biblioteca Cordillera, Persona se ubica en el "Dominio de
    Personas & Seguridad", actuando como raíz de la jerarquía de herencia:
    
            Persona (Abstracta)
             ├── Socio (Lector / Usuario de la biblioteca)
             └── Usuario (Personal del sistema)
                  ├── BibliotecariaAtencion (Mesón de préstamos)
                  └── Administradora (Superadmin)
                  
    Responsabilidades Principales:
    - Encapsulamiento de datos básicos de contacto (RUT, nombre, teléfono, email).
    - Implementación canónica del algoritmo Módulo 11 para la validación estricta de
      RUT chileno.
    - Lanzamiento de RutInvalidoError si el RUT ingresado no es válido.
========================================================================================
"""

from abc import ABC
from excepciones import RutInvalidoError


class Persona(ABC):
    """
    Clase base abstracta que representa a una persona en el sistema.
    
    Aplica encapsulamiento mediante atributos protegidos con guion bajo (_nombre_variable)
    y expone métodos de acceso (getters/setters/properties).
    """

    def __init__(self, rut: str, nombre_completo: str, telefono: str, email: str):
        # Regla Infranqueable N°3: Validación matemática obligatoria antes de instanciar
        if not self.validar_rut(rut):
            raise RutInvalidoError(rut)

        # Almacenamiento seguro con formato canónico (ej: 12.345.678-5)
        self._rut: str = self._formatear_rut(rut)
        self._nombre_completo: str = nombre_completo.strip()
        self._telefono: str = telefono.strip()
        self._email: str = email.strip()

    @staticmethod
    def _calcular_dv(cuerpo: str) -> str:
        """
        Calcula el Dígito Verificador (DV) para una secuencia numérica de RUT
        utilizando el algoritmo matemático Módulo 11 oficial de Chile.
        
        Paso a paso:
        1. Se invierte la secuencia de dígitos.
        2. Se multiplica cada dígito por la serie cíclica [2, 3, 4, 5, 6, 7].
        3. Se suma el total de las multiplicaciones.
        4. Se calcula el resto mediante: 11 - (suma % 11).
        5. Casos especiales: Si es 11 -> DV '0'. Si es 10 -> DV 'K'. Caso contrario -> número.
        """
        suma = 0
        multiplicador = 2
        for d in reversed(cuerpo):
            suma += int(d) * multiplicador
            # La serie de ponderación es 2, 3, 4, 5, 6, 7 y reinicia en 2
            multiplicador = 2 if multiplicador == 7 else multiplicador + 1

        resto = 11 - (suma % 11)
        if resto == 11:
            return "0"
        elif resto == 10:
            return "K"
        else:
            return str(resto)

    @classmethod
    def validar_rut(cls, rut: str) -> bool:
        """
        Valida si una cadena de texto corresponde a un RUT chileno matemáticamente correcto.
        
        Soporta múltiples formatos de entrada:
        - Con puntos y guión: '16.789.456-7'
        - Sin puntos, con guión: '16789456-7'
        - Solo dígitos y DV: '167894567' o '16789456K'
        """
        if not isinstance(rut, str):
            return False

        # Limpieza de caracteres separadores y estandarización a mayúsculas
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        if len(rut_limpio) < 2:
            return False

        cuerpo = rut_limpio[:-1]
        dv_ingresado = rut_limpio[-1]

        # El cuerpo del RUT debe ser estrictamente numérico
        if not cuerpo.isdigit():
            return False

        dv_esperado = cls._calcular_dv(cuerpo)
        return dv_ingresado == dv_esperado

    @classmethod
    def _formatear_rut(cls, rut: str) -> str:
        """
        Normaliza el RUT a su formato estándar chileno con puntos y guion: XX.XXX.XXX-X.
        Facilita la visualización consistente en reportes, pantalla y base de datos.
        """
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        
        # Inserción de separadores de miles con punto
        cuerpo_formateado = f"{int(cuerpo):,}".replace(",", ".")
        return f"{cuerpo_formateado}-{dv}"

    # ==================== MÉTODOS DE ACCESO (ENCAPSULAMIENTO) ====================
    def get_rut(self) -> str:
        """Retorna el RUT normalizado de la persona."""
        return self._rut

    def get_nombre(self) -> str:
        """Retorna el nombre completo de la persona."""
        return self._nombre_completo

    @property
    def rut(self) -> str:
        return self._rut

    @property
    def nombre_completo(self) -> str:
        return self._nombre_completo

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        self._telefono = valor.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        self._email = valor.strip()

    def __str__(self) -> str:
        return f"{self._nombre_completo} (RUT: {self._rut}) | Tel: {self._telefono} | Email: {self._email}"
