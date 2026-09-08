"""
Suite de Pruebas Unitarias para el Sistema de Biblioteca Cordillera
Verifica validación de RUT, jerarquía de materiales, transacciones de préstamos,
políticas de renovación, reglas infranqueables y persistencia SQLite.
"""

import unittest
from persona import Persona
from socio import Socio
from bibliotecaria_atencion import BibliotecariaAtencion
from administradora import Administradora
from libro import Libro
from revista import Revista
from material_multimedia import MaterialMultimedia
from material_extranjero import MaterialExtranjero
from repositorio_bd import RepositorioBibliotecaBD
from sistema_biblioteca import SistemaBiblioteca
from excepciones import (
    RutInvalidoError,
    SocioConMultaPendienteError,
    MaterialYaPrestadoError,
    RenovacionNoPermitidaError,
    PermisoInsuficienteError
)


class TestBiblioteca(unittest.TestCase):

    def setUp(self):
        # Usamos base de datos en memoria para aislamiento perfecto en tests
        self.repo = RepositorioBibliotecaBD(connection_string=":memory:")
        self.sistema = SistemaBiblioteca(repo_bd=self.repo)

        # Crear usuarios base con RUTs válidos
        self.admin = Administradora(
            rut="19.876.543-0",
            nombre_completo="Camila Admin",
            telefono="+56911112222",
            email="admin@test.cl",
            username="admin",
            password="Password123*"
        )
        self.bibliotecaria = BibliotecariaAtencion(
            rut="17.654.321-3",
            nombre_completo="Valentina Biblio",
            telefono="+56933334444",
            email="biblio@test.cl",
            username="vbiblio",
            password="Password123*",
            turno="Mañana"
        )
        self.sistema.registrar_usuario(self.admin)
        self.sistema.registrar_usuario(self.bibliotecaria)

        # Inscribir socio con RUT válido
        self.socio = self.sistema.inscribir_socio(
            rut="18.234.567-9",
            nombre_completo="Juan Perez",
            telefono="+56955556666",
            email="juan@test.cl"
        )

        # Materiales
        self.libro = Libro(
            codigo="L001",
            titulo="Libro Test",
            autor_o_creador="Autor A",
            anio_publicacion=2021,
            precio_base_reposicion=20000.0,
            isbn="123-456",
            editorial="Planeta",
            numero_paginas=200
        )
        self.revista = Revista(
            codigo="R001",
            titulo="Revista Test",
            autor_o_creador="Varios",
            anio_publicacion=2024,
            precio_base_reposicion=10000.0,
            issn="789-012",
            numero_edicion=10,
            mes_publicacion="Enero"
        )
        self.dvd = MaterialMultimedia(
            codigo="M001",
            titulo="Multimedia Test",
            autor_o_creador="Director B",
            anio_publicacion=2023,
            precio_base_reposicion=15000.0,
            formato="DVD",
            duracion_minutos=90,
            clasificacion_edad="TE"
        )
        self.sistema.alta_nuevo_material(self.admin, self.libro)
        self.sistema.alta_nuevo_material(self.admin, self.revista)
        self.sistema.alta_nuevo_material(self.admin, self.dvd)

    def test_rut_modulo_11(self):
        """Valida el cálculo y validación de RUT chileno."""
        self.assertTrue(Persona.validar_rut("19.876.543-0"))
        self.assertTrue(Persona.validar_rut("17.654.321-3"))
        self.assertTrue(Persona.validar_rut("16.543.210-K"))
        self.assertFalse(Persona.validar_rut("11.111.111-2"))
        self.assertFalse(Persona.validar_rut("invalido"))
        with self.assertRaises(RutInvalidoError):
            self.sistema.inscribir_socio("11.111.111-2", "Error", "123", "err@test.cl")

    def test_autenticacion_sha256(self):
        """Valida la autenticación con hash SHA-256."""
        self.assertTrue(self.admin.autenticar("Password123*"))
        self.assertFalse(self.admin.autenticar("WrongPassword"))

    def test_politicas_duracion_materiales(self):
        """Valida los días de préstamo polimórficos de cada tipo de material."""
        self.assertEqual(self.libro.dias_prestamo(), 14)
        self.assertEqual(self.revista.dias_prestamo(), 7)
        self.assertEqual(self.dvd.dias_prestamo(), 3)

    def test_politicas_renovacion(self):
        """Valida que los libros se renueven hasta 1 vez y las revistas/DVDs 0 veces."""
        prestamo = self.sistema.crear_prestamo(
            rut_socio=self.socio.get_rut(),
            cods_materiales=["L001", "R001"],
            usuario_atencion=self.bibliotecaria
        )

        # 1ra renovación libro -> OK
        self.assertTrue(self.sistema.renovar_material_prestamo(prestamo.id_prestamo, "L001"))

        # 2da renovación libro -> Error
        with self.assertRaises(RenovacionNoPermitidaError):
            self.sistema.renovar_material_prestamo(prestamo.id_prestamo, "L001")

        # Renovación revista -> Error
        with self.assertRaises(RenovacionNoPermitidaError):
            self.sistema.renovar_material_prestamo(prestamo.id_prestamo, "R001")

    def test_bloqueo_socio_con_multa(self):
        """Regla 1: Bloqueo de préstamo a socios con multas pendientes."""
        self.socio.registrar_multa(1000.0)
        self.assertFalse(self.socio.puede_solicitar_prestamo())
        with self.assertRaises(SocioConMultaPendienteError):
            self.sistema.crear_prestamo(
                rut_socio=self.socio.get_rut(),
                cods_materiales=["M001"],
                usuario_atencion=self.bibliotecaria
            )

    def test_bloqueo_material_ya_prestado(self):
        """Regla 2: Bloqueo de préstamo de material que ya está prestado."""
        self.sistema.crear_prestamo(
            rut_socio=self.socio.get_rut(),
            cods_materiales=["L001"],
            usuario_atencion=self.bibliotecaria
        )
        socio2 = self.sistema.inscribir_socio("15.432.109-8", "Socio 2", "123", "s2@test.cl")
        with self.assertRaises(MaterialYaPrestadoError):
            self.sistema.crear_prestamo(
                rut_socio=socio2.get_rut(),
                cods_materiales=["L001"],
                usuario_atencion=self.bibliotecaria
            )

    def test_segregacion_permisos(self):
        """Regla 4: Bibliotecaria no puede dar de alta ni condonar multas."""
        nuevo_libro = Libro("L002", "L2", "Aut", 2020, 10000, "111", "Ed", 100)
        with self.assertRaises(PermisoInsuficienteError):
            self.sistema.alta_nuevo_material(self.bibliotecaria, nuevo_libro)

        with self.assertRaises(PermisoInsuficienteError):
            self.sistema.condonar_multa_socio(self.bibliotecaria, self.socio.get_rut(), "Motivo")

    def test_material_extranjero_dolar(self):
        """Cálculo de reposición en USD con 6% de arancel aduanero."""
        ext = MaterialExtranjero("E001", "AI Book", "Russell", 2020, precio_usd=100.0, recargo_aduanero_pct=0.06)
        # 100 * 1.06 * 950 = 100,700
        costo = ext.calcular_valor_reposicion(950.0)
        self.assertEqual(costo, 100700.0)


if __name__ == "__main__":
    unittest.main()
