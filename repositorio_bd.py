"""
Módulo RepositorioBibliotecaBD
Manejo de persistencia relacional SQLite para el sistema de la Biblioteca Cordillera.
Gestiona almacenamiento seguro de socios, catálogo, préstamos, ítems y bitácora de auditoría.
"""

import sqlite3
import json
import datetime
from typing import Optional, Dict, Any, List


class RepositorioBibliotecaBD:
    """Clase responsable del acceso y persistencia de datos (CRUD) en SQLite."""

    def __init__(self, connection_string: str = "biblioteca_cordillera.db"):
        self._connection_string: str = connection_string
        self._is_memory: bool = connection_string == ":memory:"
        self._persistent_conn: Optional[sqlite3.Connection] = None
        
        if self._is_memory:
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row

        self._inicializar_tablas()

    def _get_connection(self) -> sqlite3.Connection:
        """Retorna una conexión activa con formato de diccionario para filas."""
        if self._is_memory and self._persistent_conn:
            return self._persistent_conn
        conn = sqlite3.connect(self._connection_string)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_tablas(self) -> None:
        """Crea el esquema relacional en SQLite si no existe previamente."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Tabla de Socios
            cursor.execute("""
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
            """)

            # Tabla de Usuarios (Bibliotecarias y Administradoras)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    username TEXT PRIMARY KEY,
                    rut TEXT NOT NULL,
                    nombre_completo TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    turno TEXT,
                    nivel_acceso TEXT,
                    activo INTEGER DEFAULT 1
                )
            """)

            # Tabla de Materiales del Catálogo
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materiales (
                    codigo TEXT PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    autor_o_creador TEXT,
                    anio_publicacion INTEGER,
                    precio_base_reposicion REAL,
                    tipo_material TEXT NOT NULL,
                    prestado INTEGER DEFAULT 0,
                    extra_json TEXT
                )
            """)

            # Tabla Cabecera de Préstamos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prestamos (
                    id_prestamo INTEGER PRIMARY KEY,
                    fecha_prestamo TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    rut_socio TEXT NOT NULL,
                    username_bibliotecaria TEXT NOT NULL,
                    total_items INTEGER DEFAULT 0,
                    FOREIGN KEY (rut_socio) REFERENCES socios(rut),
                    FOREIGN KEY (username_bibliotecaria) REFERENCES usuarios(username)
                )
            """)

            # Tabla Detalle de Préstamos
            cursor.execute("""
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
                    FOREIGN KEY (id_prestamo) REFERENCES prestamos(id_prestamo),
                    FOREIGN KEY (codigo_material) REFERENCES materiales(codigo)
                )
            """)

            # Tabla de Bitácora de Auditoría
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS log_auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    usuario TEXT NOT NULL,
                    accion TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            if not self._is_memory:
                conn.close()

    # ==================== CRUD SOCIOS ====================
    def guardar_socio(self, socio: Any) -> bool:
        """Inserta o actualiza un socio en la base de datos."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO socios (
                    rut, nombre_completo, telefono, email, numero_socio,
                    fecha_inscripcion, tiene_multa_pendiente, monto_multa_acumulada, activo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                socio.get_rut(),
                socio.get_nombre(),
                socio.telefono,
                socio.email,
                socio.numero_socio,
                socio.fecha_inscripcion.isoformat() if hasattr(socio.fecha_inscripcion, 'isoformat') else str(socio.fecha_inscripcion),
                1 if socio.tiene_multa_pendiente else 0,
                socio.monto_multa_acumulada,
                1 if socio.activo else 0
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar socio {socio.get_rut()} en BD: {e}")
            return False
        finally:
            if not self._is_memory:
                conn.close()

    def obtener_socio(self, rut: str) -> Optional[Dict[str, Any]]:
        """Obtiene un socio por su RUT."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM socios WHERE rut = ?", (rut.strip().upper(),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            if not self._is_memory:
                conn.close()

    def listar_socios(self) -> List[Dict[str, Any]]:
        """Retorna todos los socios registrados."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM socios ORDER BY numero_socio ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            if not self._is_memory:
                conn.close()

    # ==================== CRUD USUARIOS ====================
    def guardar_usuario(self, usuario: Any) -> bool:
        """Inserta o actualiza un usuario en la base de datos."""
        conn = self._get_connection()
        try:
            turno = getattr(usuario, "turno", None)
            nivel = getattr(usuario, "nivel_acceso", None)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO usuarios (
                    username, rut, nombre_completo, telefono, email,
                    password_hash, rol, turno, nivel_acceso, activo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario.username,
                usuario.get_rut(),
                usuario.get_nombre(),
                usuario.telefono,
                usuario.email,
                usuario.password_hash,
                usuario.rol,
                turno,
                nivel,
                1 if usuario.activo else 0
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar usuario @{usuario.username} en BD: {e}")
            return False
        finally:
            if not self._is_memory:
                conn.close()

    def obtener_usuario(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtiene un usuario por su nombre de usuario."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username.strip().lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            if not self._is_memory:
                conn.close()

    def listar_usuarios(self) -> List[Dict[str, Any]]:
        """Retorna todos los usuarios del sistema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios ORDER BY rol ASC, username ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            if not self._is_memory:
                conn.close()

    # ==================== CRUD MATERIALES ====================
    def guardar_material(self, material: Any) -> bool:
        """Inserta o actualiza un material en el catálogo de la BD."""
        conn = self._get_connection()
        try:
            tipo = material.__class__.__name__
            extra_data = {}
            if hasattr(material, "isbn"):
                extra_data["isbn"] = material.isbn
                extra_data["editorial"] = material.editorial
                extra_data["numero_paginas"] = material.numero_paginas
            elif hasattr(material, "issn"):
                extra_data["issn"] = material.issn
                extra_data["numero_edicion"] = material.numero_edicion
                extra_data["mes_publicacion"] = material.mes_publicacion
            elif hasattr(material, "formato"):
                extra_data["formato"] = material.formato
                extra_data["duracion_minutos"] = material.duracion_minutos
                extra_data["clasificacion_edad"] = material.clasificacion_edad
            elif hasattr(material, "precio_usd"):
                extra_data["precio_usd"] = material.precio_usd
                extra_data["recargo_aduanero_pct"] = material.recargo_aduanero_pct
                extra_data["pais_origen"] = material.pais_origen

            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO materiales (
                    codigo, titulo, autor_o_creador, anio_publicacion,
                    precio_base_reposicion, tipo_material, prestado, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                material.codigo,
                material.titulo,
                material.autor_o_creador,
                material.anio_publicacion,
                material.precio_base_reposicion,
                tipo,
                1 if material.esta_prestado() else 0,
                json.dumps(extra_data)
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar material {material.codigo} en BD: {e}")
            return False
        finally:
            if not self._is_memory:
                conn.close()

    def actualizar_estado_material(self, codigo: str, prestado: bool) -> bool:
        """Actualiza la disponibilidad de un material."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE materiales SET prestado = ? WHERE codigo = ?
            """, (1 if prestado else 0, codigo.strip().upper()))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar estado de material {codigo} en BD: {e}")
            return False
        finally:
            if not self._is_memory:
                conn.close()

    def eliminar_material(self, codigo: str) -> bool:
        """Elimina un material del catálogo en BD."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM materiales WHERE codigo = ?", (codigo.strip().upper(),))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar material {codigo} de BD: {e}")
            return False
        finally:
            if not self._is_memory:
                conn.close()

    def listar_materiales(self) -> List[Dict[str, Any]]:
        """Retorna todos los materiales del catálogo."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM materiales ORDER BY codigo ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            if not self._is_memory:
                conn.close()

    # ==================== CRUD PRÉSTAMOS ====================
    def guardar_prestamo(self, prestamo: Any) -> bool:
        """Persiste la cabecera y todas las líneas de detalle de un préstamo."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Cabecera
            cursor.execute("""
                INSERT OR REPLACE INTO prestamos (
                    id_prestamo, fecha_prestamo, estado, rut_socio,
                    username_bibliotecaria, total_items
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                prestamo.id_prestamo,
                prestamo.fecha_prestamo.isoformat(),
                prestamo.estado,
                prestamo.socio.get_rut(),
                prestamo.bibliotecaria.username,
                len(prestamo.items_prestamo)
            ))

            # Detalles
            for det in prestamo.items_prestamo:
                cursor.execute("""
                    INSERT OR REPLACE INTO detalles_prestamo (
                        id_prestamo, id_detalle, codigo_material, fecha_inicio,
                        dias_prestamo_otorgados, fecha_devolucion_esperada,
                        fecha_devolucion_real, cantidad_renovaciones, devuelto
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prestamo.id_prestamo,
                    det.id_detalle,
                    det.material.codigo,
                    det.fecha_inicio.isoformat(),
                    det.dias_prestamo_otorgados,
                    det.fecha_devolucion_esperada.isoformat(),
                    det.fecha_devolucion_real.isoformat() if det.fecha_devolucion_real else None,
                    det.cantidad_renovaciones,
                    1 if det.devuelto else 0
                ))

            # Actualizar estado de los materiales en la tabla materiales
            for det in prestamo.items_prestamo:
                cursor.execute("""
                    UPDATE materiales SET prestado = ? WHERE codigo = ?
                """, (1 if not det.devuelto else 0, det.material.codigo))

            # Actualizar saldo de multas del socio en BD
            cursor.execute("""
                UPDATE socios SET
                    tiene_multa_pendiente = ?,
                    monto_multa_acumulada = ?
                WHERE rut = ?
            """, (
                1 if prestamo.socio.tiene_multa_pendiente else 0,
                prestamo.socio.monto_multa_acumulada,
                prestamo.socio.get_rut()
            ))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar préstamo N°{prestamo.id_prestamo} en BD: {e}")
            return False
        finally:
            if not self._is_memory:
                conn.close()

    def obtener_prestamo(self, id_prestamo: int) -> Optional[Dict[str, Any]]:
        """Obtiene la cabecera y lista de detalles de un préstamo."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prestamos WHERE id_prestamo = ?", (id_prestamo,))
            row = cursor.fetchone()
            if not row:
                return None
            
            prestamo_dict = dict(row)
            cursor.execute("SELECT * FROM detalles_prestamo WHERE id_prestamo = ? ORDER BY id_detalle ASC", (id_prestamo,))
            prestamo_dict["detalles"] = [dict(d) for d in cursor.fetchall()]
            return prestamo_dict
        finally:
            if not self._is_memory:
                conn.close()

    def listar_prestamos(self) -> List[Dict[str, Any]]:
        """Retorna el listado de préstamos con sus detalles."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prestamos ORDER BY id_prestamo ASC")
            prestamos = []
            for row in cursor.fetchall():
                p_dict = dict(row)
                c2 = conn.cursor()
                c2.execute("SELECT * FROM detalles_prestamo WHERE id_prestamo = ?", (p_dict["id_prestamo"],))
                p_dict["detalles"] = [dict(d) for d in c2.fetchall()]
                prestamos.append(p_dict)
            return prestamos
        finally:
            if not self._is_memory:
                conn.close()

    # ==================== BITÁCORA DE AUDITORÍA ====================
    def registrar_auditoria(self, usuario: str, accion: str) -> None:
        """Registra un evento con fecha y hora en el log de auditoría."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO log_auditoria (fecha, usuario, accion)
                VALUES (?, ?, ?)
            """, (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                usuario.strip(),
                accion.strip()
            ))
            conn.commit()
        except Exception as e:
            print(f"Error al registrar auditoría: {e}")
        finally:
            if not self._is_memory:
                conn.close()

    def obtener_logs_auditoria(self, limite: int = 50) -> List[Dict[str, Any]]:
        """Consulta los últimos eventos registrados en la bitácora."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM log_auditoria ORDER BY id DESC LIMIT ?", (limite,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            if not self._is_memory:
                conn.close()
