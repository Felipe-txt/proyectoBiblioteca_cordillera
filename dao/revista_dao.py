"""
========================================================================================
PAQUETE: dao
MÓDULO: revista_dao.py
ROL EN EL PROYECTO:
    DAO para publicaciones periódicas y revistas (Hereda de MaterialDao).
========================================================================================
"""

import json
from typing import List, Optional
try:
    from dao.material_dao import MaterialDao
    from model.revista import Revista
except ImportError:
    from material_dao import MaterialDao
    from revista import Revista


class RevistaDao(MaterialDao):
    """
    Data Access Object para la entidad Revista.
    """

    def crear_tabla(self) -> None:
        super().crear_tabla()
        sql = """
        CREATE TABLE IF NOT EXISTS revistas (
            codigo TEXT PRIMARY KEY,
            issn TEXT NOT NULL,
            numero_edicion INTEGER NOT NULL,
            mes_publicacion TEXT NOT NULL,
            FOREIGN KEY (codigo) REFERENCES materiales (codigo) ON DELETE CASCADE
        )
        """
        self.cursor.execute(sql)
        self.conexion.commit()

    def guardar(self, revista: Revista) -> None:
        self.crear_tabla()
        metadatos = json.dumps({
            "issn": revista.issn,
            "numero_edicion": revista.numero_edicion,
            "mes_publicacion": revista.mes_publicacion
        })
        self.guardar_base(revista, tipo_material="REVISTA", metadatos_json=metadatos)
        
        sql = """
        INSERT INTO revistas (codigo, issn, numero_edicion, mes_publicacion)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            issn = excluded.issn,
            numero_edicion = excluded.numero_edicion,
            mes_publicacion = excluded.mes_publicacion
        """
        self.cursor.execute(sql, (
            revista.codigo,
            revista.issn,
            revista.numero_edicion,
            revista.mes_publicacion
        ))
        self.conexion.commit()

    def obtener_por_codigo(self, codigo: str) -> Optional[Revista]:
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, r.issn, r.numero_edicion, r.mes_publicacion
        FROM materiales m
        INNER JOIN revistas r ON m.codigo = r.codigo
        WHERE m.codigo = ?
        """
        self.cursor.execute(sql, (codigo.strip().upper(),))
        f = self.cursor.fetchone()
        if not f:
            return None
        return Revista(
            codigo=f[0],
            titulo=f[1],
            autor_o_creador=f[2],
            anio_publicacion=f[3],
            precio_base_reposicion=f[4],
            prestado=bool(f[5]),
            issn=f[6],
            numero_edicion=f[7],
            mes_publicacion=f[8]
        )

    def listar_todos(self) -> List[Revista]:
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, r.issn, r.numero_edicion, r.mes_publicacion
        FROM materiales m
        INNER JOIN revistas r ON m.codigo = r.codigo
        ORDER BY m.titulo ASC
        """
        self.cursor.execute(sql)
        filas = self.cursor.fetchall()
        return [
            Revista(
                codigo=f[0],
                titulo=f[1],
                autor_o_creador=f[2],
                anio_publicacion=f[3],
                precio_base_reposicion=f[4],
                prestado=bool(f[5]),
                issn=f[6],
                numero_edicion=f[7],
                mes_publicacion=f[8]
            )
            for f in filas
        ]
