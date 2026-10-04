"""
========================================================================================
PAQUETE: dao
ROL EN EL PROYECTO:
    Exporta todos los DAOs de la arquitectura orientada a objetos de la biblioteca.
========================================================================================
"""

from dao.dao import Dao
from dao.material_dao import MaterialDao
from dao.libro_dao import LibroDao
from dao.revista_dao import RevistaDao
from dao.multimedia_dao import MultimediaDao
from dao.extranjero_dao import ExtranjeroDao
from dao.socio_dao import SocioDao
from dao.usuario_dao import UsuarioDao
from dao.prestamo_dao import PrestamoDao
from dao.boleta_dao import BoletaDao
from dao.json_dao import JsonDao

__all__ = [
    "Dao",
    "MaterialDao",
    "LibroDao",
    "RevistaDao",
    "MultimediaDao",
    "ExtranjeroDao",
    "SocioDao",
    "UsuarioDao",
    "PrestamoDao",
    "BoletaDao",
    "JsonDao"
]
