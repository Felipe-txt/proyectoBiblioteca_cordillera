"""
========================================================================================
PAQUETE: dao
MÓDULO: dao.py
ROL EN EL PROYECTO:
    Clase base Data Access Object (DAO).
    Mantiene la conexión y el cursor a la base de datos relacional (SQLite).
========================================================================================
"""


class Dao:
    """
    Clase base Data Access Object (DAO).
    Se encarga de inicializar y mantener la conexión a la base de datos y su cursor.
    """

    def __init__(self, conexion):
        """
        Constructor que recibe un objeto de conexión y establece el cursor.
        
        Args:
            conexion: El objeto de conexión a la base de datos (sqlite3.Connection).
        """
        self.conexion = conexion
        self.cursor = self.conexion.cursor()
