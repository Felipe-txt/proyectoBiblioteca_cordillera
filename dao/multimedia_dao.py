"""
========================================================================================
PAQUETE: dao
MÓDULO: multimedia_dao.py
ROL EN EL PROYECTO:
    DAO para recursos audiovisuales y multimedia (Hereda de MaterialDao).
========================================================================================
"""

import json
from typing import List, Optional
try:
    from dao.material_dao import MaterialDao
    from model.material_multimedia import MaterialMultimedia
except ImportError:
    from material_dao import MaterialDao
    from material_multimedia import MaterialMultimedia


class MultimediaDao(MaterialDao):
    """
    Data Access Object para la entidad MaterialMultimedia.
    """

    def crear_tabla(self) -> None:
        super().crear_tabla()
        sql = """
        CREATE TABLE IF NOT EXISTS multimedia (
            codigo TEXT PRIMARY KEY,
            formato TEXT NOT NULL,
            duracion_minutos INTEGER NOT NULL,
            clasificacion_edad TEXT NOT NULL,
            FOREIGN KEY (codigo) REFERENCES materiales (codigo) ON DELETE CASCADE
        )
        """
        self.cursor.execute(sql)
        self.conexion.commit()

    def guardar(self, item: MaterialMultimedia) -> None:
        self.crear_tabla()
        metadatos = json.dumps({
            "formato": item.formato,
            "duracion_minutos": item.duracion_minutos,
            "clasificacion_edad": item.clasificacion_edad
        })
        self.guardar_base(item, tipo_material="MULTIMEDIA", metadatos_json=metadatos)
        
        sql = """
        INSERT INTO multimedia (codigo, formato, duracion_minutos, clasificacion_edad)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            formato = excluded.formato,
            duracion_minutos = excluded.duracion_minutos,
            clasificacion_edad = excluded.clasificacion_edad
        """
        self.cursor.execute(sql, (
            item.codigo,
            item.formato,
            item.duracion_minutos,
            item.clasificacion_edad
        ))
        self.conexion.commit()

    def obtener_por_codigo(self, codigo: str) -> Optional[MaterialMultimedia]:
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, mm.formato, mm.duracion_minutos, mm.clasificacion_edad
        FROM materiales m
        INNER JOIN multimedia mm ON m.codigo = mm.codigo
        WHERE m.codigo = ?
        """
        self.cursor.execute(sql, (codigo.strip().upper(),))
        f = self.cursor.fetchone()
        if not f:
            return None
        return MaterialMultimedia(
            codigo=f[0],
            titulo=f[1],
            autor_o_creador=f[2],
            anio_publicacion=f[3],
            precio_base_reposicion=f[4],
            prestado=bool(f[5]),
            formato=f[6],
            duracion_minutos=f[7],
            clasificacion_edad=f[8]
        )

    def listar_todos(self) -> List[MaterialMultimedia]:
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, mm.formato, mm.duracion_minutos, mm.clasificacion_edad
        FROM materiales m
        INNER JOIN multimedia mm ON m.codigo = mm.codigo
        ORDER BY m.titulo ASC
        """
        self.cursor.execute(sql)
        filas = self.cursor.fetchall()
        return [
            MaterialMultimedia(
                codigo=f[0],
                titulo=f[1],
                autor_o_creador=f[2],
                anio_publicacion=f[3],
                precio_base_reposicion=f[4],
                prestado=bool(f[5]),
                formato=f[6],
                duracion_minutos=f[7],
                clasificacion_edad=f[8]
            )
            for f in filas
        ]
