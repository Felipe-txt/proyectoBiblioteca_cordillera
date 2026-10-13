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

    def listar_todos_objetos(
        self,
        materiales_dict: Dict[str, Material],
        socios_dict: Dict[str, Socio],
        usuarios_dict: Dict[str, Usuario]
    ) -> List[Prestamo]:
        """
        Reconstruye la lista completa de objetos Prestamo con sus DetallePrestamo
        vinculados a sus entidades de dominio respectivas.
        """
        filas_crudas = self.listar_todos_crudos()
        prestamos_reconstruidos = []

        # Mapa para normalizar RUTs
        socios_por_rut = {}
        for s in socios_dict.values():
            rut_clean = s.get_rut().replace(".", "").replace("-", "").strip().upper()
            socios_por_rut[rut_clean] = s

        for pc in filas_crudas:
            rut_clean = pc["rut_socio"].replace(".", "").replace("-", "").strip().upper()
            socio_obj = socios_por_rut.get(rut_clean)
            if not socio_obj:
                continue

            user_obj = usuarios_dict.get(pc["username_bibliotecaria"].lower())
            if not user_obj and usuarios_dict:
                user_obj = list(usuarios_dict.values())[0]

            fecha_p = datetime.fromisoformat(pc["fecha_prestamo"]) if pc.get("fecha_prestamo") else datetime.now()
            p = Prestamo(
                id_prestamo=pc["id_prestamo"],
                socio=socio_obj,
                bibliotecaria=user_obj,
                fecha_prestamo=fecha_p,
                estado=pc.get("estado", "ACTIVO")
            )

            for dc in pc.get("detalles", []):
                cod_m = dc["codigo_material"].upper()
                mat_obj = materiales_dict.get(cod_m)
                if not mat_obj:
                    continue

                f_inicio = date.fromisoformat(dc["fecha_inicio"]) if dc.get("fecha_inicio") else date.today()
                f_esp = date.fromisoformat(dc["fecha_devolucion_esperada"]) if dc.get("fecha_devolucion_esperada") else f_inicio
                f_real = date.fromisoformat(dc["fecha_devolucion_real"]) if dc.get("fecha_devolucion_real") else None

                item = DetallePrestamo(
                    id_detalle=dc["id_detalle"],
                    material=mat_obj,
                    fecha_inicio=f_inicio,
                    dias_prestamo=dc["dias_prestamo_otorgados"],
                    devuelto=bool(dc["devuelto"]),
                    cantidad_renovaciones=dc["cantidad_renovaciones"],
                    fecha_devolucion_real=f_real,
                    fecha_devolucion_esperada=f_esp
                )
                p._items_prestamo.append(item)

            prestamos_reconstruidos.append(p)

        return prestamos_reconstruidos

    def eliminar(self, id_prestamo: int) -> None:
        """Elimina un préstamo y sus detalles asociados en cascada."""
        self.crear_tabla()
        self.cursor.execute("DELETE FROM detalles_prestamo WHERE id_prestamo = ?", (int(id_prestamo),))
        self.cursor.execute("DELETE FROM prestamos WHERE id_prestamo = ?", (int(id_prestamo),))
        self.conexion.commit()
