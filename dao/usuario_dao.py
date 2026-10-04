"""
========================================================================================
PAQUETE: dao
MÓDULO: usuario_dao.py
ROL EN EL PROYECTO:
    DAO para personal y usuarios del sistema (Tabla 'usuarios' en SQLite).
========================================================================================
"""

from typing import List, Optional
try:
    from dao.dao import Dao
    from model.usuario import Usuario
    from model.administradora import Administradora
    from model.bibliotecaria_atencion import BibliotecariaAtencion
except ImportError:
    from dao import Dao
    from usuario import Usuario
    from administradora import Administradora
    from bibliotecaria_atencion import BibliotecariaAtencion


class UsuarioDao(Dao):
    """
    Data Access Object para la tabla de usuarios del sistema.
    """

    def crear_tabla(self) -> None:
        """Crea la tabla usuarios si no existe."""
        sql = """
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
        """
        self.cursor.execute(sql)
        self.conexion.commit()

    def guardar(self, usuario: Usuario) -> None:
        """Inserta o actualiza un usuario en la BD."""
        self.crear_tabla()
        rol = usuario.obtener_rol()
        turno = getattr(usuario, "turno", None)
        nivel_acceso = getattr(usuario, "nivel_acceso", None)
        
        sql = """
        INSERT INTO usuarios (
            username, rut, nombre_completo, telefono, email,
            password_hash, rol, turno, nivel_acceso, activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(username) DO UPDATE SET
            rut = excluded.rut,
            nombre_completo = excluded.nombre_completo,
            telefono = excluded.telefono,
            email = excluded.email,
            password_hash = excluded.password_hash,
            rol = excluded.rol,
            turno = excluded.turno,
            nivel_acceso = excluded.nivel_acceso,
            activo = excluded.activo
        """
        self.cursor.execute(sql, (
            usuario.username,
            usuario.get_rut(),
            usuario.get_nombre_completo(),
            usuario.get_telefono(),
            usuario.get_email(),
            usuario.password_hash,
            rol,
            turno,
            nivel_acceso
        ))
        self.conexion.commit()

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        """Obtiene un usuario por su nombre de usuario."""
        self.crear_tabla()
        sql = "SELECT * FROM usuarios WHERE LOWER(username) = LOWER(?)"
        self.cursor.execute(sql, (username.strip(),))
        f = self.cursor.fetchone()
        if not f:
            return None
        
        rol_str = f[6].upper()
        if "ADMINISTRADORA" in rol_str:
            user = Administradora(
                rut=f[1],
                nombre_completo=f[2],
                telefono=f[3] or "",
                email=f[4] or "",
                username=f[0],
                password="",
                nivel_acceso=f[8] or "SUPERADMIN"
            )
        else:
            user = BibliotecariaAtencion(
                rut=f[1],
                nombre_completo=f[2],
                telefono=f[3] or "",
                email=f[4] or "",
                username=f[0],
                password="",
                turno=f[7] or "Manana"
            )
        # Asignamos el hash original directamente
        user._password_hash = f[5]
        return user

    def listar_todos(self) -> List[Usuario]:
        """Lista todos los usuarios del sistema."""
        self.crear_tabla()
        self.cursor.execute("SELECT * FROM usuarios ORDER BY username ASC")
        filas = self.cursor.fetchall()
        usuarios = []
        for f in filas:
            rol_str = f[6].upper()
            if "ADMINISTRADORA" in rol_str:
                user = Administradora(
                    rut=f[1],
                    nombre_completo=f[2],
                    telefono=f[3] or "",
                    email=f[4] or "",
                    username=f[0],
                    password="",
                    nivel_acceso=f[8] or "SUPERADMIN"
                )
            else:
                user = BibliotecariaAtencion(
                    rut=f[1],
                    nombre_completo=f[2],
                    telefono=f[3] or "",
                    email=f[4] or "",
                    username=f[0],
                    password="",
                    turno=f[7] or "Manana"
                )
            user._password_hash = f[5]
            usuarios.append(user)
        return usuarios
