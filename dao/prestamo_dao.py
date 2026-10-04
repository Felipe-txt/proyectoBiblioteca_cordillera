"""
========================================================================================
PAQUETE: dao
MÓDULO: prestamo_dao.py
ROL EN EL PROYECTO:
    DAO para transacciones de préstamos y detalles (Tablas 'prestamos' y 'detalles_prestamo').
========================================================================================
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
try:
    from dao.dao import Dao
    from model.prestamo import Prestamo
    from model.detalle_prestamo import DetallePrestamo
    from model.socio import Socio
    from model.usuario import Usuario
    from model.material import Material
except ImportError:
    from dao import Dao
    from prestamo import Prestamo
    from detalle_prestamo import DetallePrestamo
    from socio import Socio
    from usuario import Usuario
    from material import Material


class PrestamoDao(Dao):
    """
    Data Access Object para la cabecera transaccional y líneas de detalle de préstamos.
    """

    def crear_tabla(self) -> None:
        """Crea las tablas prestamos y detalles_prestamo si no existen."""
        sql_prestamos = """
        CREATE TABLE IF NOT EXISTS prestamos (
            id_prestamo INTEGER PRIMARY KEY,
            fecha_prestamo TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            rut_socio TEXT NOT NULL,
            username_bibliotecaria TEXT NOT NULL,
            total_items INTEGER DEFAULT 0,
            FOREIGN KEY (rut_socio) REFERENCES socios (rut),
            FOREIGN KEY (username_bibliotecaria) REFERENCES usuarios (username)
        )
        """
        sql_detalles = """
        CREATE TABLE IF NOT EXISTS detalles_prestamo (
            id_prestamo INTEGER NOT NULL,
            id_detalle INTEGER NOT NULL,
            codigo_material TEXT NOT NULL,
            fecha_inicio TEXT NOT NULL,
            dias_prestamo_otorgados INTEGER NOT NULL,
            fecha_devolucion_esperada TEXT NOT NULL,
            fecha_devolucion_real TEXT,
            cantidad_renovaciones INTEGER DEFAULT 0,
            devuelto INTEGER DEFAULT 0,
            PRIMARY KEY (id_prestamo, id_detalle),
            FOREIGN KEY (id_prestamo) REFERENCES prestamos (id_prestamo) ON DELETE CASCADE,
            FOREIGN KEY (codigo_material) REFERENCES materiales (codigo)
        )
        """
        self.cursor.execute(sql_prestamos)
        self.cursor.execute(sql_detalles)
        self.conexion.commit()

    def guardar(self, prestamo: Prestamo) -> None:
        """Guarda la cabecera y todas las líneas de detalle del préstamo."""
        self.crear_tabla()
        sql_prestamo = """
        INSERT INTO prestamos (id_prestamo, fecha_prestamo, estado, rut_socio, username_bibliotecaria, total_items)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_prestamo) DO UPDATE SET
            fecha_prestamo = excluded.fecha_prestamo,
            estado = excluded.estado,
            rut_socio = excluded.rut_socio,
            username_bibliotecaria = excluded.username_bibliotecaria,
            total_items = excluded.total_items
        """
        self.cursor.execute(sql_prestamo, (
            prestamo.id_prestamo,
            prestamo.fecha_prestamo.isoformat(),
            prestamo.estado,
            prestamo.socio.get_rut(),
            prestamo.bibliotecaria.username,
            len(prestamo.items_prestamo)
        ))

        sql_detalle = """
        INSERT INTO detalles_prestamo (
            id_prestamo, id_detalle, codigo_material, fecha_inicio,
            dias_prestamo_otorgados, fecha_devolucion_esperada,
            fecha_devolucion_real, cantidad_renovaciones, devuelto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_prestamo, id_detalle) DO UPDATE SET
            codigo_material = excluded.codigo_material,
            fecha_inicio = excluded.fecha_inicio,
            dias_prestamo_otorgados = excluded.dias_prestamo_otorgados,
            fecha_devolucion_esperada = excluded.fecha_devolucion_esperada,
            fecha_devolucion_real = excluded.fecha_devolucion_real,
            cantidad_renovaciones = excluded.cantidad_renovaciones,
            devuelto = excluded.devuelto
        """
        for item in prestamo.items_prestamo:
            self.cursor.execute(sql_detalle, (
                prestamo.id_prestamo,
                item.id_detalle,
                item.material.codigo,
                item.fecha_inicio.isoformat() if item.fecha_inicio else date.today().isoformat(),
                item.dias_prestamo_otorgados,
                item.fecha_devolucion_esperada.isoformat(),
                item.fecha_devolucion_real.isoformat() if item.fecha_devolucion_real else None,
                item.cantidad_renovaciones,
                1 if item.devuelto else 0
            ))
            sql_upd_mat = "UPDATE materiales SET prestado = ? WHERE codigo = ?"
            self.cursor.execute(sql_upd_mat, (1 if not item.devuelto else 0, item.material.codigo))

        self.conexion.commit()

    def listar_todos_crudos(self) -> List[Dict[str, Any]]:
        """Retorna las filas de préstamos con sus detalles asociados."""
        self.crear_tabla()
        self.cursor.execute("SELECT * FROM prestamos ORDER BY id_prestamo DESC")
        cols_p = [d[0] for d in self.cursor.description]
        filas_p = self.cursor.fetchall()
        
        resultado = []
        for fp in filas_p:
            p_dict = dict(zip(cols_p, fp))
            self.cursor.execute("SELECT * FROM detalles_prestamo WHERE id_prestamo = ? ORDER BY id_detalle ASC", (p_dict["id_prestamo"],))
            cols_d = [d[0] for d in self.cursor.description]
            filas_d = self.cursor.fetchall()
            p_dict["detalles"] = [dict(zip(cols_d, fd)) for fd in filas_d]
            resultado.append(p_dict)
            
        return resultado
