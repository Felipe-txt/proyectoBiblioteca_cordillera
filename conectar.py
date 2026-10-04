"""
========================================================================================
MÓDULO: conectar.py
ROL EN EL PROYECTO:
    Manejador central de conexión a la base de datos relacional SQLite y factoría de DAOs.
    Sigue el patrón de diseño utilizado en el Taller Mecánico con soporte extendido para JSON.
========================================================================================
"""

import sqlite3
from typing import Optional
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


def crear_conexion(nombre_bd: str = "biblioteca_cordillera.db") -> sqlite3.Connection:
    """
    Crea y retorna un objeto de conexión SQLite con claves foráneas activadas y row_factory.
    
    Args:
        nombre_bd: Ruta o nombre del archivo .db (o ':memory:' para pruebas en memoria).
        
    Returns:
        sqlite3.Connection: Conexión lista para ser entregada a los DAOs.
    """
    conn = sqlite3.connect(nombre_bd)
    conn.row_factory = sqlite3.Row
    # Habilitación explícita de llaves foráneas para mantener integridad referencial
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_base_datos(conn: Optional[sqlite3.Connection] = None) -> sqlite3.Connection:
    """
    Inicializa todas las tablas de la base de datos utilizando sus respectivos DAOs.
    
    Args:
        conn: Conexión opcional. Si no se provee, se crea una a 'biblioteca_cordillera.db'.
        
    Returns:
        sqlite3.Connection: La conexión inicializada con todas las tablas creadas.
    """
    if conn is None:
        conn = crear_conexion()

    # 1. Instanciamos los DAOs entregándoles la conexión
    libro_dao = LibroDao(conn)
    revista_dao = RevistaDao(conn)
    multimedia_dao = MultimediaDao(conn)
    extranjero_dao = ExtranjeroDao(conn)
    socio_dao = SocioDao(conn)
    usuario_dao = UsuarioDao(conn)
    prestamo_dao = PrestamoDao(conn)
    boleta_dao = BoletaDao(conn)

    # 2. Invocamos la creación de tablas en orden jerárquico
    socio_dao.crear_tabla()
    usuario_dao.crear_tabla()
    libro_dao.crear_tabla()        # auto-crea 'materiales' y 'libros'
    revista_dao.crear_tabla()      # auto-crea 'revistas'
    multimedia_dao.crear_tabla()   # auto-crea 'multimedia'
    extranjero_dao.crear_tabla()   # auto-crea 'extranjeros'
    prestamo_dao.crear_tabla()     # auto-crea 'prestamos' y 'detalles_prestamo'
    boleta_dao.crear_tabla()       # auto-crea 'boletas' y 'lineas_boleta'

    return conn


def obtener_json_dao(ruta_archivo: str = "biblioteca_db.json") -> JsonDao:
    """
    Retorna una instancia del DAO de persistencia en archivos JSON.
    """
    return JsonDao(ruta_archivo)
