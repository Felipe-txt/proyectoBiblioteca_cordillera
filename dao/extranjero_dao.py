"""
========================================================================================
PAQUETE: dao
MÓDULO: extranjero_dao.py
ROL EN EL PROYECTO:
    DAO para obras y materiales extranjeros en USD (Hereda de MaterialDao).
========================================================================================
"""

import json
from typing import List, Optional
try:
    from dao.material_dao import MaterialDao
    from model.material_extranjero import MaterialExtranjero
except ImportError:
    from material_dao import MaterialDao
    from material_extranjero import MaterialExtranjero


class ExtranjeroDao(MaterialDao):
    """
    Data Access Object para la entidad MaterialExtranjero.
    """

    def crear_tabla(self) -> None:
        super().crear_tabla()
        sql = """
        CREATE TABLE IF NOT EXISTS extranjeros (
            codigo TEXT PRIMARY KEY,
            precio_usd REAL NOT NULL,
            pais_origen TEXT NOT NULL,
            recargo_aduanero_pct REAL DEFAULT 0.06,
            FOREIGN KEY (codigo) REFERENCES materiales (codigo) ON DELETE CASCADE
        )
        """
        self.cursor.execute(sql)
        self.conexion.commit()

    def guardar(self, item: MaterialExtranjero) -> None:
        self.crear_tabla()
        metadatos = json.dumps({
            "precio_usd": item.precio_usd,
            "pais_origen": item.pais_origen,
            "recargo_aduanero_pct": item.recargo_aduanero_pct
        })
        self.guardar_base(item, tipo_material="EXTRANJERO", metadatos_json=metadatos)
        
        sql = """
        INSERT INTO extranjeros (codigo, precio_usd, pais_origen, recargo_aduanero_pct)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            precio_usd = excluded.precio_usd,
            pais_origen = excluded.pais_origen,
            recargo_aduanero_pct = excluded.recargo_aduanero_pct
        """
        self.cursor.execute(sql, (
            item.codigo,
            item.precio_usd,
            item.pais_origen,
            item.recargo_aduanero_pct
        ))
        self.conexion.commit()

    def obtener_por_codigo(self, codigo: str) -> Optional[MaterialExtranjero]:
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, e.precio_usd, e.pais_origen, e.recargo_aduanero_pct
        FROM materiales m
        INNER JOIN extranjeros e ON m.codigo = e.codigo
        WHERE m.codigo = ?
        """
        self.cursor.execute(sql, (codigo.strip().upper(),))
        f = self.cursor.fetchone()
        if not f:
            return None
        return MaterialExtranjero(
            codigo=f[0],
            titulo=f[1],
            autor_o_creador=f[2],
            anio_publicacion=f[3],
            precio_usd=f[6],
            pais_origen=f[7],
            recargo_aduanero_pct=f[8],
            prestado=bool(f[5])
        )

    def listar_todos(self) -> List[MaterialExtranjero]:
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, e.precio_usd, e.pais_origen, e.recargo_aduanero_pct
        FROM materiales m
        INNER JOIN extranjeros e ON m.codigo = e.codigo
        ORDER BY m.titulo ASC
        """
        self.cursor.execute(sql)
        filas = self.cursor.fetchall()
        return [
            MaterialExtranjero(
                codigo=f[0],
                titulo=f[1],
                autor_o_creador=f[2],
                anio_publicacion=f[3],
                precio_usd=f[6],
                pais_origen=f[7],
                recargo_aduanero_pct=f[8],
                prestado=bool(f[5])
            )
            for f in filas
        ]
