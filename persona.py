"""
Módulo Persona
Clase base abstracta para todas las personas en el sistema (Socios y Usuarios).
Implementa encapsulamiento y validación estricta de RUT chileno con Módulo 11.
"""

from abc import ABC
from excepciones import RutInvalidoError


class Persona(ABC):
    """Clase base abstracta que representa a una persona en el sistema de la biblioteca."""

    def __init__(self, rut: str, nombre_completo: str, telefono: str, email: str):
        if not self.validar_rut(rut):
            raise RutInvalidoError(rut)

        self._rut: str = self._formatear_rut(rut)
        self._nombre_completo: str = nombre_completo.strip()
        self._telefono: str = telefono.strip()
        self._email: str = email.strip()

    @staticmethod
    def _calcular_dv(cuerpo: str) -> str:
        """
        Calcula el dígito verificador para un cuerpo numérico de RUT
        utilizando el algoritmo estándar de Módulo 11 chileno.
        """
        suma = 0
        multiplicador = 2
        for d in reversed(cuerpo):
            suma += int(d) * multiplicador
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
        Valida el RUT chileno mediante el algoritmo Módulo 11.
        Acepta formatos con puntos y guión (12.345.678-5) o sin formato (12345678-5, 123456785).
        """
        if not isinstance(rut, str):
            return False

        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        if len(rut_limpio) < 2:
            return False

        cuerpo = rut_limpio[:-1]
        dv_ingresado = rut_limpio[-1]

        if not cuerpo.isdigit():
            return False

        dv_esperado = cls._calcular_dv(cuerpo)
        return dv_ingresado == dv_esperado

    @classmethod
    def _formatear_rut(cls, rut: str) -> str:
        """Formatea un RUT a su representación canónica XX.XXX.XXX-X."""
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        
        # Formatear cuerpo con puntos
        cuerpo_formateado = f"{int(cuerpo):,}".replace(",", ".")
        return f"{cuerpo_formateado}-{dv}"

    def get_rut(self) -> str:
        """Retorna el RUT formateado de la persona."""
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
