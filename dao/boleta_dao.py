"""
========================================================================================
PAQUETE: dao
MÓDULO: boleta_dao.py
ROL EN EL PROYECTO:
    DAO para Boletas, Comprobantes de Cobro y Órdenes de Trabajo (Tablas 'boletas' y 'lineas_boleta').
========================================================================================
"""

from typing import List, Dict, Any, Optional
try:
    from dao.dao import Dao
    from model.boleta import Boleta, LineaDetalleBoleta
except ImportError:
    from dao import Dao
    from boleta import Boleta, LineaDetalleBoleta


class BoletaDao(Dao):
    """
    Data Access Object para la emisión y consulta de boletas u órdenes de trabajo.
    """

    def crear_tabla(self) -> None:
        """Crea las tablas boletas y lineas_boleta si no existen."""
        sql_boletas = """
        CREATE TABLE IF NOT EXISTS boletas (
            numero INTEGER PRIMARY KEY,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'EMITIDA',
            socio_rut TEXT NOT NULL,
            usuario_username TEXT NOT NULL,
            prestamo_id INTEGER,
            subtotal REAL DEFAULT 0.0,
            iva REAL DEFAULT 0.0,
            descuento REAL DEFAULT 0.0,
            total REAL DEFAULT 0.0,
            FOREIGN KEY (socio_rut) REFERENCES socios (rut),
            FOREIGN KEY (usuario_username) REFERENCES usuarios (username)
        )
        """
        sql_lineas = """
        CREATE TABLE IF NOT EXISTS lineas_boleta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boleta_numero INTEGER NOT NULL,
            concepto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            codigo_referencia TEXT,
            tipo_item TEXT NOT NULL,
            FOREIGN KEY (boleta_numero) REFERENCES boletas (numero) ON DELETE CASCADE
        )
        """
        self.cursor.execute(sql_boletas)
        self.cursor.execute(sql_lineas)
        self.conexion.commit()

    def guardar(self, boleta: Boleta) -> None:
        """Guarda la boleta y todas sus líneas de detalle."""
        self.crear_tabla()
        sql_b = """
        INSERT INTO boletas (
            numero, tipo, descripcion, fecha, estado,
            socio_rut, usuario_username, prestamo_id,
            subtotal, iva, descuento, total
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(numero) DO UPDATE SET
            tipo = excluded.tipo,
            descripcion = excluded.descripcion,
            fecha = excluded.fecha,
            estado = excluded.estado,
            socio_rut = excluded.socio_rut,
            usuario_username = excluded.usuario_username,
            prestamo_id = excluded.prestamo_id,
            subtotal = excluded.subtotal,
            iva = excluded.iva,
            descuento = excluded.descuento,
            total = excluded.total
        """
        self.cursor.execute(sql_b, (
            boleta.numero,
            boleta.tipo,
            boleta.descripcion,
            boleta.fecha.isoformat(),
            boleta.estado,
            boleta.socio.get_rut(),
            boleta.usuario.username,
            boleta.prestamo_id,
            boleta.subtotal(),
            boleta.monto_iva(),
            boleta.monto_descuento(),
            boleta.total()
        ))

        # Borramos líneas antiguas e insertamos las actuales
        self.cursor.execute("DELETE FROM lineas_boleta WHERE boleta_numero = ?", (boleta.numero,))
        sql_l = """
        INSERT INTO lineas_boleta (
            boleta_numero, concepto, cantidad, precio_unitario,
            subtotal, codigo_referencia, tipo_item
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        for linea in boleta.lineas:
            self.cursor.execute(sql_l, (
                boleta.numero,
                linea.concepto,
                linea.cantidad,
                linea.precio_unitario,
                linea.subtotal(),
                linea.codigo_referencia,
                linea.tipo_item
            ))

        self.conexion.commit()

    def listar_todas_crudas(self) -> List[Dict[str, Any]]:
        """Retorna todas las boletas con sus líneas de detalle."""
        self.crear_tabla()
        self.cursor.execute("SELECT * FROM boletas ORDER BY numero DESC")
        cols_b = [d[0] for d in self.cursor.description]
        filas_b = self.cursor.fetchall()
        
        resultado = []
        for fb in filas_b:
            b_dict = dict(zip(cols_b, fb))
            self.cursor.execute("SELECT * FROM lineas_boleta WHERE boleta_numero = ?", (b_dict["numero"],))
            cols_l = [d[0] for d in self.cursor.description]
            filas_l = self.cursor.fetchall()
            b_dict["lineas"] = [dict(zip(cols_l, fl)) for fl in filas_l]
            resultado.append(b_dict)
            
        return resultado
