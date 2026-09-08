"""
========================================================================================
MÓDULO: test_biblioteca.py
ROL EN EL PROYECTO:
    Suite de Pruebas Unitarias Automatizadas (Unit Testing) con el framework estándar unittest.
    
    Responsabilidades Principales:
    - Asegurar que las 4 Reglas Infranqueables del Dominio se cumplan rigurosamente.
    - Probar que las Excepciones de Negocio se disparen exactamente en los escenarios previstos:
      * RutInvalidoError: Si el dígito verificador es incorrecto.
      * SocioConMultaPendienteError: Si un socio con multa intenta pedir un préstamo.
      * MaterialYaPrestadoError: Si se intenta pedir un libro que ya está prestado.
      * RenovacionNoPermitidaError: Si se intenta renovar material no elegible o se excede el cupo.
      * PermisoInsuficienteError: Si una bibliotecaria intenta realizar acciones de administradora.
    - Validar el polimorfismo de duraciones y cálculos arancelarios en moneda extranjera.
    - Utilizar una base de datos SQLite en memoria (':memory:') para aislar cada test.
========================================================================================
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
    """
    Casos de prueba unitaria para validar integridad de datos, seguridad, polimorfismo y reglas.
    """

    def setUp(self):
        """
        Precondición de prueba:
        Crea una base de datos SQLite en memoria ':memory:' limpia antes de cada prueba,
        garantizando total independencia entre tests.
        """
        self.repo = RepositorioBibliotecaBD(connection_string=":memory:")
        self.sistema = SistemaBiblioteca(repo_bd=self.repo)

        # Usuarios de prueba con RUTs matemáticamente válidos
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

        # Socio habilitado de prueba
        self.socio = self.sistema.inscribir_socio(
            rut="18.234.567-9",
            nombre_completo="Juan Perez",
            telefono="+56955556666",
            email="juan@test.cl"
        )

        # Catálogo de prueba con las 3 subclases principales
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
        """
        Prueba de Regla N°3 (Validación de RUT y excepción RutInvalidoError):
        - Verifica que RUTs válidos sean aprobados sin importar formato.
        - Verifica que RUTs con DV adulterado fallen y disparen RutInvalidoError.
        """
        self.assertTrue(Persona.validar_rut("19.876.543-0"))
        self.assertTrue(Persona.validar_rut("17.654.321-3"))
        self.assertTrue(Persona.validar_rut("16.543.210-K"))
        self.assertFalse(Persona.validar_rut("11.111.111-2"))
        self.assertFalse(Persona.validar_rut("invalido"))
        
        # Debe disparar RutInvalidoError al intentar registrar una persona con RUT erróneo
        with self.assertRaises(RutInvalidoError):
            self.sistema.inscribir_socio("11.111.111-2", "Error", "123", "err@test.cl")

    def test_autenticacion_sha256(self):
        """
        Prueba de Seguridad de Acceso:
        Comprueba que la autenticación solo tenga éxito si el hash coincide con la clave original.
        """
        self.assertTrue(self.admin.autenticar("Password123*"))
        self.assertFalse(self.admin.autenticar("WrongPassword"))

    def test_politicas_duracion_materiales(self):
        """
        Prueba de Polimorfismo en Duración de Préstamo:
        Verifica que cada subclase devuelva su plazo reglamentario: Libros=14d, Revistas=7d, DVDs=3d.
        """
        self.assertEqual(self.libro.dias_prestamo(), 14)
        self.assertEqual(self.revista.dias_prestamo(), 7)
        self.assertEqual(self.dvd.dias_prestamo(), 3)

    def test_politicas_renovacion(self):
        """
        Prueba de Excepción RenovacionNoPermitidaError:
        - 1ra renovación de libro permitida.
        - 2da renovación de libro rechazada (supera cupo máximo de 1).
        - Renovación de revista rechazada inmediatamente (0 renovaciones permitidas).
        """
        prestamo = self.sistema.crear_prestamo(
            rut_socio=self.socio.get_rut(),
            cods_materiales=["L001", "R001"],
            usuario_atencion=self.bibliotecaria
        )

        # 1ra renovación libro -> OK
        self.assertTrue(self.sistema.renovar_material_prestamo(prestamo.id_prestamo, "L001"))

        # 2da renovación libro -> Dispara RenovacionNoPermitidaError
        with self.assertRaises(RenovacionNoPermitidaError):
            self.sistema.renovar_material_prestamo(prestamo.id_prestamo, "L001")

        # Renovación de revista -> Dispara RenovacionNoPermitidaError
        with self.assertRaises(RenovacionNoPermitidaError):
            self.sistema.renovar_material_prestamo(prestamo.id_prestamo, "R001")

    def test_bloqueo_socio_con_multa(self):
        """
        Prueba de Regla Infranqueable N°1 (SocioConMultaPendienteError):
        Verifica que un socio con multas impagas quede bloqueado para pedir nuevos libros.
        """
        self.socio.registrar_multa(1000.0)
        self.assertFalse(self.socio.puede_solicitar_prestamo())
        with self.assertRaises(SocioConMultaPendienteError):
            self.sistema.crear_prestamo(
                rut_socio=self.socio.get_rut(),
                cods_materiales=["M001"],
                usuario_atencion=self.bibliotecaria
            )

    def test_bloqueo_material_ya_prestado(self):
        """
        Prueba de Regla Infranqueable N°2 (MaterialYaPrestadoError):
        Verifica que no se pueda prestar un ejemplar que ya se encuentra prestado a otro socio.
        """
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
        """
        Prueba de Regla Infranqueable N°4 (PermisoInsuficienteError):
        Verifica que una bibliotecaria no pueda ejecutar atribuciones exclusivas de la administradora.
        """
        nuevo_libro = Libro("L002", "L2", "Aut", 2020, 10000, "111", "Ed", 100)
        with self.assertRaises(PermisoInsuficienteError):
            self.sistema.alta_nuevo_material(self.bibliotecaria, nuevo_libro)

        with self.assertRaises(PermisoInsuficienteError):
            self.sistema.condonar_multa_socio(self.bibliotecaria, self.socio.get_rut(), "Motivo")

    def test_material_extranjero_dolar(self):
        """
        Prueba de Cálculo Polimórfico de Reposición Arancelaria:
        Verifica la fórmula: Costo = USD * (1 + 0.06 Arancel) * Valor Dólar.
        $100 USD * 1.06 * $950 CLP/USD = $100,700 CLP.
        """
        ext = MaterialExtranjero("E001", "AI Book", "Russell", 2020, precio_usd=100.0, recargo_aduanero_pct=0.06)
        costo = ext.calcular_valor_reposicion(950.0)
        self.assertEqual(costo, 100700.0)


if __name__ == "__main__":
    unittest.main()
