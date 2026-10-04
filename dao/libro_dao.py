"""
========================================================================================
PAQUETE: dao
MÓDULO: libro_dao.py
ROL EN EL PROYECTO:
    DAO específico para la entidad Libro (Hereda de MaterialDao aplicando Table-per-Type).
========================================================================================
"""

import json
from typing import List, Optional
try:
    from dao.material_dao import MaterialDao
    from model.libro import Libro
except ImportError:
    from material_dao import MaterialDao
    from libro import Libro


class LibroDao(MaterialDao):
    """
    Data Access Object para la entidad Libro.
    Hereda de MaterialDao (que a su vez hereda de Dao).
    """

    def crear_tabla(self) -> None:
        """
        Invoca la creación de la tabla padre ('materiales') y luego 
        crea la tabla 'libros' en la base de datos si no existe.
        """
        super().crear_tabla()
        sql = """
        CREATE TABLE IF NOT EXISTS libros (
            codigo TEXT PRIMARY KEY,
            isbn TEXT NOT NULL,
            editorial TEXT NOT NULL,
            numero_paginas INTEGER NOT NULL,
            FOREIGN KEY (codigo) REFERENCES materiales (codigo) ON DELETE CASCADE
        )
        """
        self.cursor.execute(sql)
        self.conexion.commit()

    def guardar(self, libro: Libro) -> None:
        """Guarda un libro tanto en la tabla padre (materiales) como en la hija (libros)."""
        self.crear_tabla()
        metadatos = json.dumps({
            "isbn": libro.isbn,
            "editorial": libro.editorial,
            "numero_paginas": libro.numero_paginas
        })
        self.guardar_base(libro, tipo_material="LIBRO", metadatos_json=metadatos)
        
        sql = """
        INSERT INTO libros (codigo, isbn, editorial, numero_paginas)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            isbn = excluded.isbn,
            editorial = excluded.editorial,
            numero_paginas = excluded.numero_paginas
        """
        self.cursor.execute(sql, (
            libro.codigo,
            libro.isbn,
            libro.editorial,
            libro.numero_paginas
        ))
        self.conexion.commit()

    def obtener_por_codigo(self, codigo: str) -> Optional[Libro]:
        """Obtiene un libro reconstruido mediante JOIN entre materiales y libros."""
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, l.isbn, l.editorial, l.numero_paginas
        FROM materiales m
        INNER JOIN libros l ON m.codigo = l.codigo
        WHERE m.codigo = ?
        """
        self.cursor.execute(sql, (codigo.strip().upper(),))
        fila = self.cursor.fetchone()
        if not fila:
            return None
        return Libro(
            codigo=fila[0],
            titulo=fila[1],
            autor_o_creador=fila[2],
            anio_publicacion=fila[3],
            precio_base_reposicion=fila[4],
            prestado=bool(fila[5]),
            isbn=fila[6],
            editorial=fila[7],
            numero_paginas=fila[8]
        )

    def listar_todos(self) -> List[Libro]:
        """Lista todos los libros existentes en la base de datos."""
        self.crear_tabla()
        sql = """
        SELECT m.codigo, m.titulo, m.autor_o_creador, m.anio_publicacion, m.precio_base_reposicion,
               m.prestado, l.isbn, l.editorial, l.numero_paginas
        FROM materiales m
        INNER JOIN libros l ON m.codigo = l.codigo
        ORDER BY m.titulo ASC
        """
        self.cursor.execute(sql)
        filas = self.cursor.fetchall()
        libros = []
        for f in filas:
            libros.append(Libro(
                codigo=f[0],
                titulo=f[1],
                autor_o_creador=f[2],
                anio_publicacion=f[3],
                precio_base_reposicion=f[4],
                prestado=bool(f[5]),
                isbn=f[6],
                editorial=f[7],
                numero_paginas=f[8]
            ))
        return libros
