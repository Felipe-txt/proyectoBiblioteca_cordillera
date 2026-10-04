"""
========================================================================================
PAQUETE: dao
MÓDULO: socio_dao.py
ROL EN EL PROYECTO:
    DAO para la entidad Socio (Tabla 'socios' en SQLite).
========================================================================================
"""

from datetime import date
from typing import List, Optional
try:
    from dao.dao import Dao
    from model.socio import Socio
except ImportError:
    from dao import Dao
    from socio import Socio


class SocioDao(Dao):
    """
    Data Access Object para la tabla de socios.
    """

    def crear_tabla(self) -> None:
        """Crea la tabla socios si no existe."""
        sql = """
        CREATE TABLE IF NOT EXISTS socios (
            rut TEXT PRIMARY KEY,
            nombre_completo TEXT NOT NULL,
            telefono TEXT,
            email TEXT,
            numero_socio INTEGER UNIQUE,
            fecha_inscripcion TEXT,
            tiene_multa_pendiente INTEGER DEFAULT 0,
            monto_multa_acumulada REAL DEFAULT 0.0,
            activo INTEGER DEFAULT 1
        )
        """
        self.cursor.execute(sql)
        self.conexion.commit()

    def guardar(self, socio: Socio) -> None:
        """Inserta o actualiza un socio."""
        self.crear_tabla()
        sql = """
        INSERT INTO socios (
            rut, nombre_completo, telefono, email,
            numero_socio, fecha_inscripcion,
            tiene_multa_pendiente, monto_multa_acumulada, activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rut) DO UPDATE SET
            nombre_completo = excluded.nombre_completo,
            telefono = excluded.telefono,
            email = excluded.email,
            numero_socio = excluded.numero_socio,
            fecha_inscripcion = excluded.fecha_inscripcion,
            tiene_multa_pendiente = excluded.tiene_multa_pendiente,
            monto_multa_acumulada = excluded.monto_multa_acumulada,
            activo = excluded.activo
        """
        self.cursor.execute(sql, (
            socio.get_rut(),
            socio.get_nombre_completo(),
            socio.get_telefono(),
            socio.get_email(),
            socio.numero_socio,
            socio.fecha_inscripcion.isoformat() if socio.fecha_inscripcion else date.today().isoformat(),
            1 if socio.tiene_multa_pendiente else 0,
            socio.monto_multa_acumulada,
            1 if socio.activo else 0
        ))
        self.conexion.commit()

    def obtener_por_rut(self, rut: str) -> Optional[Socio]:
        """Recupera un socio por su RUT."""
        self.crear_tabla()
        rut_limpio = rut.replace(".", "").replace("-", "").strip().upper()
        
        self.cursor.execute("SELECT * FROM socios")
        filas = self.cursor.fetchall()
        for f in filas:
            f_rut_limpio = f[0].replace(".", "").replace("-", "").strip().upper()
            if f_rut_limpio == rut_limpio:
                fecha_obj = date.fromisoformat(f[5]) if f[5] else date.today()
                return Socio(
                    rut=f[0],
                    nombre_completo=f[1],
                    telefono=f[2] or "",
                    email=f[3] or "",
                    numero_socio=f[4],
                    fecha_inscripcion=fecha_obj,
                    tiene_multa_pendiente=bool(f[6]),
                    monto_multa_acumulada=float(f[7]),
                    activo=bool(f[8])
                )
        return None

    def listar_todos(self) -> List[Socio]:
        """Lista todos los socios ordenados por número de socio."""
        self.crear_tabla()
        self.cursor.execute("SELECT * FROM socios ORDER BY numero_socio ASC")
        filas = self.cursor.fetchall()
        socios = []
        for f in filas:
            fecha_obj = date.fromisoformat(f[5]) if f[5] else date.today()
            socios.append(Socio(
                rut=f[0],
                nombre_completo=f[1],
                telefono=f[2] or "",
                email=f[3] or "",
                numero_socio=f[4],
                fecha_inscripcion=fecha_obj,
                tiene_multa_pendiente=bool(f[6]),
                monto_multa_acumulada=float(f[7]),
                activo=bool(f[8])
            ))
        return socios
