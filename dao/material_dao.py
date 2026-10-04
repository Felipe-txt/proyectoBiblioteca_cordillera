"""
========================================================================================
PAQUETE: dao
MÓDULO: material_dao.py
ROL EN EL PROYECTO:
    DAO base para la entidad Material (tabla padre del catálogo de biblioteca).
========================================================================================
"""

from typing import List, Optional, Dict, Any
try:
    from dao.dao import Dao
    from model.material import Material
except ImportError:
    from dao import Dao
    from material import Material


class MaterialDao(Dao):
    """
    Data Access Object para la tabla base 'materiales'.
    """

    def crear_tabla(self) -> None:
        """Crea la tabla padre de materiales en SQLite si no existe."""
        sql = """
        CREATE TABLE IF NOT EXISTS materiales (
            codigo TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            autor_o_creador TEXT,
            anio_publicacion INTEGER,
            precio_base_reposicion REAL DEFAULT 0.0,
            tipo_material TEXT NOT NULL,
            prestado INTEGER DEFAULT 0,
            extra_json TEXT
        )
        """
        self.cursor.execute(sql)
        self.conexion.commit()

    def guardar_base(self, material: Material, tipo_material: str, metadatos_json: str = "{}") -> None:
        """Inserta o actualiza un registro en la tabla materiales."""
        self.crear_tabla()
        sql = """
        INSERT INTO materiales (codigo, titulo, autor_o_creador, anio_publicacion, precio_base_reposicion, tipo_material, prestado, extra_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            titulo = excluded.titulo,
            autor_o_creador = excluded.autor_o_creador,
            anio_publicacion = excluded.anio_publicacion,
            precio_base_reposicion = excluded.precio_base_reposicion,
            tipo_material = excluded.tipo_material,
            prestado = excluded.prestado,
            extra_json = excluded.extra_json
        """
        self.cursor.execute(sql, (
            material.codigo,
            material.titulo,
            material.autor_o_creador,
            material.anio_publicacion,
            material.precio_base_reposicion,
            tipo_material,
            1 if material.esta_prestado() else 0,
            metadatos_json
        ))
        self.conexion.commit()

    def actualizar_estado_prestado(self, codigo: str, prestado: bool) -> None:
        """Actualiza la bandera de préstamo de un material."""
        sql = "UPDATE materiales SET prestado = ? WHERE codigo = ?"
        self.cursor.execute(sql, (1 if prestado else 0, codigo.strip().upper()))
        self.conexion.commit()

    def eliminar_por_codigo(self, codigo: str) -> None:
        """Elimina un material por su código primario."""
        sql = "DELETE FROM materiales WHERE codigo = ?"
        self.cursor.execute(sql, (codigo.strip().upper(),))
        self.conexion.commit()

    def listar_todos_crudos(self) -> List[Dict[str, Any]]:
        """Retorna todas las filas de materiales."""
        self.crear_tabla()
        self.cursor.execute("SELECT * FROM materiales")
        columnas = [d[0] for d in self.cursor.description]
        return [dict(zip(columnas, fila)) for fila in self.cursor.fetchall()]
