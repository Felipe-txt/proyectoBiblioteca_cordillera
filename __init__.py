"""
========================================================================================
PAQUETE: biblioteca_cordillera (__init__.py)
ROL EN EL PROYECTO:
    Punto de entrada de empaquetado para el sistema de la Biblioteca Cordillera.
    Permite importar cualquier entidad del dominio directamente desde el paquete:
    
        from biblioteca_cordillera import (
            SistemaBiblioteca,
            Libro,
            Socio,
            SocioConMultaPendienteError
        )
        
    Módulos y Jerarquías Exportadas:
    - Dominio de Personas: Persona, Socio, Usuario, BibliotecariaAtencion, Administradora.
    - Dominio de Materiales: Material, Libro, Revista, MaterialMultimedia, MaterialExtranjero.
    - Transacciones: DetallePrestamo, Prestamo.
    - Servicios y Persistencia: ServicioDolarAPI, RepositorioBibliotecaBD, SistemaBiblioteca.
    - Excepciones del Dominio: BibliotecaError y sus subclases especializadas.
========================================================================================
"""

from persona import Persona
from socio import Socio
from usuario import Usuario
from bibliotecaria_atencion import BibliotecariaAtencion
from administradora import Administradora
from material import Material
from libro import Libro
from revista import Revista
from material_multimedia import MaterialMultimedia
from material_extranjero import MaterialExtranjero
from detalle_prestamo import DetallePrestamo
from prestamo import Prestamo
from servicio_dolar import ServicioDolarAPI
from repositorio_bd import RepositorioBibliotecaBD
from sistema_biblioteca import SistemaBiblioteca
from excepciones import (
    BibliotecaError,
    SocioConMultaPendienteError,
    MaterialYaPrestadoError,
    RenovacionNoPermitidaError,
    RutInvalidoError,
    PermisoInsuficienteError,
    MaterialNoEncontradoError,
    SocioNoEncontradoError,
    PrestamoNoEncontradoError
)

__all__ = [
    "Persona",
    "Socio",
    "Usuario",
    "BibliotecariaAtencion",
    "Administradora",
    "Material",
    "Libro",
    "Revista",
    "MaterialMultimedia",
    "MaterialExtranjero",
    "DetallePrestamo",
    "Prestamo",
    "ServicioDolarAPI",
    "RepositorioBibliotecaBD",
    "SistemaBiblioteca",
    "BibliotecaError",
    "SocioConMultaPendienteError",
    "MaterialYaPrestadoError",
    "RenovacionNoPermitidaError",
    "RutInvalidoError",
    "PermisoInsuficienteError",
    "MaterialNoEncontradoError",
    "SocioNoEncontradoError",
    "PrestamoNoEncontradoError"
]
