"""
========================================================================================
MÓDULO: test_backend.py
ROL EN EL PROYECTO:
    Suite de Pruebas Unitarias Automatizadas para el nuevo Backend, DAOs, API, Boletas y JSON.
========================================================================================
"""

import os
import unittest
import sqlite3
from datetime import date, datetime

import conectar
from model.socio import Socio
from model.administradora import Administradora
from model.bibliotecaria_atencion import BibliotecariaAtencion
from model.libro import Libro
from model.revista import Revista
from model.material_multimedia import MaterialMultimedia
from model.material_extranjero import MaterialExtranjero
from model.prestamo import Prestamo
from model.boleta import Boleta
from dao.libro_dao import LibroDao
from dao.socio_dao import SocioDao
from dao.usuario_dao import UsuarioDao
from dao.prestamo_dao import PrestamoDao
from dao.boleta_dao import BoletaDao
from dao.json_dao import JsonDao
from api.servicio_dolar import ServicioDolarAPI
from api.biblioteca_api import BibliotecaAPI
from sistema_biblioteca import SistemaBiblioteca


class TestBackendCompleto(unittest.TestCase):
    """Pruebas integrales de DAOs, Modelos, Boletas, API y Persistencia JSON."""

    def setUp(self):
        # Base de datos en memoria para aislamiento
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        
        # Inicializar tablas con DAOs
        conectar.inicializar_base_datos(self.conn)
        
        self.socio_dao = SocioDao(self.conn)
        self.usuario_dao = UsuarioDao(self.conn)
        self.libro_dao = LibroDao(self.conn)
        self.prestamo_dao = PrestamoDao(self.conn)
        self.boleta_dao = BoletaDao(self.conn)
        
        self.json_test_file = "test_biblioteca_db.json"
        self.json_dao = JsonDao(self.json_test_file)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.json_test_file):
            try:
                os.remove(self.json_test_file)
            except Exception:
                pass

    def test_daos_crud_completo(self):
        """Prueba inserción y recuperación en SQLite mediante DAOs."""
        # 1. Socio DAO
        socio = Socio("18.234.567-9", "Juan Pruebas", "+56911223344", "juan@test.cl", numero_socio=101)
        self.socio_dao.guardar(socio)
        recup_socio = self.socio_dao.obtener_por_rut("18.234.567-9")
        self.assertIsNotNone(recup_socio)
        self.assertEqual(recup_socio.get_nombre(), "Juan Pruebas")

        # 2. Usuario DAO
        admin = Administradora("19.876.543-0", "Camila Admin", "+56999887766", "admin@cordillera.cl", "admin", "Clave123*")
        self.usuario_dao.guardar(admin)
        recup_user = self.usuario_dao.obtener_por_username("admin")
        self.assertIsNotNone(recup_user)
        self.assertTrue(recup_user.autenticar("Clave123*"))

        # 3. Libro DAO (Herencia relacional Table-per-Type)
        libro = Libro("LIB-100", "Estructuras de Datos", "Goodrich", 2018, 30000.0, "978-1118771334", "Wiley", 720)
        self.libro_dao.guardar(libro)
        recup_libro = self.libro_dao.obtener_por_codigo("LIB-100")
        self.assertIsNotNone(recup_libro)
        self.assertEqual(recup_libro.isbn, "978-1118771334")
        self.assertEqual(recup_libro.dias_prestamo(), 14)

    def test_boleta_y_calculo_totales(self):
        """Prueba generación de boletas, multas, órdenes de trabajo y cálculo de subtotales."""
        socio = Socio("18.234.567-9", "Juan Pruebas", "+56911223344", "juan@test.cl", numero_socio=1)
        admin = Administradora("19.876.543-0", "Camila Admin", "+56999887766", "admin@cordillera.cl", "admin", "Clave123*")
        libro = Libro("LIB-100", "Clean Code", "Robert C. Martin", 2008, 35000.0, "978-0132350884", "Prentice", 464)
        
        boleta = Boleta(
            numero=1001,
            socio=socio,
            usuario=admin,
            tipo="ORDEN_TRABAJO_TALLER",
            descripcion="Restauración y cobro de mora"
        )
        
        # Agregar líneas
        boleta.agregar_cargo_prestamo(libro, tarifa_base=1000.0)
        boleta.agregar_cargo_multa(dias_atraso=4, tarifa_diaria=500.0, codigo_material="LIB-100")
        boleta.agregar_orden_trabajo_taller(servicio="Empastado en cuero", horas=3, tarifa_hora=4000.0)
        
        # Subtotales: 1000 + (4*500 = 2000) + (3*4000 = 12000) = 15,000 CLP
        self.assertEqual(boleta.subtotal(), 15000.0)
        self.assertEqual(boleta.total(), 15000.0)
        
        # Generar texto de recibo
        recibo_texto = boleta.generar_recibo_texto()
        self.assertIn("15,000 CLP", recibo_texto)
        self.assertIn("Clean Code", recibo_texto)
        
        # Guardar en DAO
        self.socio_dao.guardar(socio)
        self.usuario_dao.guardar(admin)
        self.boleta_dao.guardar(boleta)
        
        boletas_db = self.boleta_dao.listar_todas_crudas()
        self.assertEqual(len(boletas_db), 1)
        self.assertEqual(boletas_db[0]["total"], 15000.0)

    def test_persistencia_json(self):
        """Prueba exportación y carga completa de la base de datos en JSON."""
        sistema = SistemaBiblioteca(nombre_biblioteca="Biblioteca Cordillera Test")
        
        admin = Administradora("19.876.543-0", "Admin Jefa", "+56911", "a@test.cl", "admin", "Clave123*")
        sistema.registrar_usuario(admin)
        
        socio = sistema.inscribir_socio("18.234.567-9", "Lector Uno", "+56922", "l@test.cl")
        libro = Libro("LIB-999", "Python Avanzado", "Autor X", 2024, 25000.0, "978-999", "Editorial", 300)
        sistema.alta_nuevo_material(admin, libro)
        
        # Exportar a JSON
        ruta_guardada = self.json_dao.exportar_desde_sistema(sistema)
        self.assertTrue(os.path.exists(ruta_guardada))
        
        # Crear nuevo sistema y rehidratar desde JSON
        nuevo_sistema = SistemaBiblioteca(nombre_biblioteca="Biblioteca Rehidratada")
        datos_cargados = self.json_dao.cargar_base_datos()
        self.assertIsNotNone(datos_cargados)
        nuevo_sistema.hidratar_desde_json(datos_cargados)
        
        self.assertIn("18.234.567-9", nuevo_sistema.registro_socios)
        self.assertIn("LIB-999", nuevo_sistema.catalogo_materiales)
        self.assertEqual(nuevo_sistema.catalogo_materiales["LIB-999"].titulo, "Python Avanzado")

    def test_api_controller(self):
        """Prueba métodos del API backend controller."""
        sistema = SistemaBiblioteca()
        admin = Administradora("19.876.543-0", "Admin Jefa", "+56911", "a@test.cl", "admin", "Clave123*")
        sistema.registrar_usuario(admin)
        
        api = BibliotecaAPI(sistema)
        
        # 1. Registrar socio por API
        resp_socio = api.registrar_socio({
            "rut": "18.234.567-9",
            "nombre_completo": "Socio API",
            "telefono": "+56988887777",
            "email": "socio.api@test.cl"
        })
        self.assertTrue(resp_socio["exito"])
        
        # 2. Agregar libro por API
        resp_libro = api.agregar_libro({
            "codigo": "LIB-API",
            "titulo": "Libro de API",
            "autor": "Ingeniero",
            "anio": 2025,
            "precio_reposicion": 20000.0,
            "isbn": "978-API",
            "editorial": "Tech Books",
            "paginas": 150
        }, username_admin="admin")
        self.assertTrue(resp_libro["exito"])
        
        # 3. Consultar Dólar
        resp_dolar = api.consultar_dolar()
        self.assertGreater(resp_dolar["valor_clp"], 0)


if __name__ == "__main__":
    unittest.main()
