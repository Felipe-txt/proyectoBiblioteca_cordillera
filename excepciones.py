"""
========================================================================================
MÓDULO: excepciones.py (Raíz / Re-exportador)
Exporta las excepciones del paquete model para compatibilidad total.
========================================================================================
"""

from model.excepciones import (
    BibliotecaError,
    RutInvalidoError,
    SocioConMultaPendienteError,
    MaterialYaPrestadoError,
    MaterialNoEncontradoError,
    SocioNoEncontradoError,
    PrestamoNoEncontradoError,
    RenovacionNoPermitidaError,
    PermisoInsuficienteError
)

__all__ = [
    "BibliotecaError",
    "RutInvalidoError",
    "SocioConMultaPendienteError",
    "MaterialYaPrestadoError",
    "MaterialNoEncontradoError",
    "SocioNoEncontradoError",
    "PrestamoNoEncontradoError",
    "RenovacionNoPermitidaError",
    "PermisoInsuficienteError"
]
