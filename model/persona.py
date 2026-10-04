"""
========================================================================================
PAQUETE: model
MÓDULO: persona.py
ROL EN EL PROYECTO:
    Clase Base Abstracta (ABC) para todo ser humano registrado en el sistema.
========================================================================================
"""

from abc import ABC
try:
    from model.excepciones import RutInvalidoError
except ImportError:
    from excepciones import RutInvalidoError


class Persona(ABC):
    """
    Clase base abstracta que representa a una persona en el sistema.
    Aplica encapsulamiento mediante atributos protegidos y valida el RUT con Módulo 11.
    """

    def __init__(self, rut: str, nombre_completo: str, telefono: str, email: str):
        if not self.validar_rut(rut):
            raise RutInvalidoError(rut)

        self._rut: str = self._formatear_rut(rut)
        self._nombre_completo: str = nombre_completo.strip()
        self._telefono: str = telefono.strip()
        self._email: str = email.strip()

    @staticmethod
    def _calcular_dv(cuerpo: str) -> str:
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
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        cuerpo_con_puntos = f"{int(cuerpo):,}".replace(",", ".")
        return f"{cuerpo_con_puntos}-{dv}"

    def get_rut(self) -> str:
        return self._rut

    def get_nombre(self) -> str:
        return self._nombre_completo

    def get_nombre_completo(self) -> str:
        return self._nombre_completo

    def set_nombre_completo(self, nuevo_nombre: str) -> None:
        if nuevo_nombre and nuevo_nombre.strip():
            self._nombre_completo = nuevo_nombre.strip()

    def get_telefono(self) -> str:
        return self._telefono

    def set_telefono(self, nuevo_telefono: str) -> None:
        self._telefono = nuevo_telefono.strip()

    def get_email(self) -> str:
        return self._email

    def set_email(self, nuevo_email: str) -> None:
        self._email = nuevo_email.strip()

    @property
    def rut(self) -> str:
        return self._rut

    @property
    def nombre(self) -> str:
        return self._nombre_completo

    @property
    def nombre_completo(self) -> str:
        return self._nombre_completo

    @property
    def telefono(self) -> str:
        return self._telefono

    @property
    def email(self) -> str:
        return self._email

    def __str__(self) -> str:
        return f"RUT: {self._rut} | Nombre: {self._nombre_completo} | Contacto: {self._telefono} ({self._email})"
