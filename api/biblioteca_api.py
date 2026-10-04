"""
========================================================================================
PAQUETE: api
MÓDULO: biblioteca_api.py
ROL EN EL PROYECTO:
    API Backend / Service Layer para la Biblioteca Municipal Cordillera.
    Expone las operaciones de negocio procesando entradas y serializando respuestas en JSON.
========================================================================================
"""

from typing import Dict, Any, List, Optional
try:
    from model.excepciones import BibliotecaError
    from model.libro import Libro
    from model.revista import Revista
    from model.material_multimedia import MaterialMultimedia
    from model.material_extranjero import MaterialExtranjero
    from model.socio import Socio
    from model.bibliotecaria_atencion import BibliotecariaAtencion
    from model.administradora import Administradora
    from model.boleta import Boleta
    from api.servicio_dolar import ServicioDolarAPI
    from dao.json_dao import JsonDao
except ImportError:
    from excepciones import BibliotecaError
    from libro import Libro
    from revista import Revista
    from material_multimedia import MaterialMultimedia
    from material_extranjero import MaterialExtranjero
    from socio import Socio
    from bibliotecaria_atencion import BibliotecariaAtencion
    from administradora import Administradora
    from boleta import Boleta
    from servicio_dolar import ServicioDolarAPI
    from json_dao import JsonDao


class BibliotecaAPI:
    """
    API Backend que centraliza las operaciones del sistema y expone interfaces estandarizadas.
    """

    def __init__(self, sistema):
        self.sistema = sistema
        self.servicio_dolar = ServicioDolarAPI()
        self.json_dao = JsonDao("biblioteca_db.json")

    # ==================== ENDPOINTS: CATÁLOGO ====================
    def agregar_libro(self, datos: Dict[str, Any], username_admin: str) -> Dict[str, Any]:
        """Agrega un libro al catálogo validando privilegios."""
        try:
            admin = self.sistema.usuarios_sistema.get(username_admin.strip().lower())
            if not admin:
                return {"exito": False, "mensaje": f"Usuario admin '{username_admin}' no encontrado."}
                
            libro = Libro(
                codigo=datos["codigo"],
                titulo=datos["titulo"],
                autor_o_creador=datos["autor"],
                anio_publicacion=int(datos["anio"]),
                precio_base_reposicion=float(datos.get("precio_reposicion", 25000.0)),
                isbn=datos["isbn"],
                editorial=datos["editorial"],
                numero_paginas=int(datos["paginas"])
            )
            self.sistema.alta_nuevo_material(admin, libro)
            return {"exito": True, "mensaje": f"Libro '{libro.titulo}' registrado con éxito.", "codigo": libro.codigo}
        except BibliotecaError as e:
            return {"exito": False, "error": str(e)}
        except Exception as e:
            return {"exito": False, "error": f"Error inesperado: {str(e)}"}

    def listar_catalogo(self) -> List[Dict[str, Any]]:
        """Retorna todos los ítems del catálogo."""
        catalogo = []
        dolar_actual = self.servicio_dolar.obtener_valor_dolar()
        for m in self.sistema.catalogo_materiales.values():
            item = {
                "codigo": m.codigo,
                "titulo": m.titulo,
                "autor": m.autor_o_creador,
                "anio": m.anio_publicacion,
                "tipo": m.__class__.__name__,
                "prestado": m.esta_prestado(),
                "costo_reposicion_clp": m.calcular_costo_reposicion(dolar_actual)
            }
            catalogo.append(item)
        return catalogo

    # ==================== ENDPOINTS: SOCIOS ====================
    def registrar_socio(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Registra e inscribe un nuevo socio."""
        try:
            socio = self.sistema.inscribir_socio(
                rut=datos["rut"],
                nombre_completo=datos["nombre_completo"],
                telefono=datos.get("telefono", ""),
                email=datos.get("email", "")
            )
            return {
                "exito": True,
                "mensaje": f"Socio {socio.get_nombre()} inscrito correctamente.",
                "rut": socio.get_rut(),
                "numero_socio": socio.numero_socio
            }
        except BibliotecaError as e:
            return {"exito": False, "error": str(e)}
        except Exception as e:
            return {"exito": False, "error": f"Error: {str(e)}"}

    def listar_socios(self) -> List[Dict[str, Any]]:
        """Lista todos los socios."""
        return [
            {
                "rut": s.get_rut(),
                "nombre_completo": s.get_nombre_completo(),
                "telefono": s.get_telefono(),
                "email": s.get_email(),
                "numero_socio": s.numero_socio,
                "tiene_multa": s.tiene_multa_pendiente,
                "monto_multa": s.monto_multa_acumulada,
                "habilitado": s.puede_solicitar_prestamo()
            }
            for s in self.sistema.registro_socios.values()
        ]

    # ==================== ENDPOINTS: PEDIDOS Y PRÉSTAMOS ====================
    def crear_pedido_prestamo(self, rut_socio: str, username_biblio: str, codigos_materiales: List[str]) -> Dict[str, Any]:
        """Crea una orden de préstamo múltiple."""
        try:
            prestamo = self.sistema.crear_prestamo_multiple(
                rut_socio=rut_socio,
                username_bibliotecaria=username_biblio,
                codigos_materiales=codigos_materiales
            )
            return {
                "exito": True,
                "mensaje": f"Pedido/Préstamo #{prestamo.id_prestamo} generado exitosamente.",
                "id_prestamo": prestamo.id_prestamo,
                "total_items": len(prestamo.items_prestamo)
            }
        except BibliotecaError as e:
            return {"exito": False, "error": str(e)}
        except Exception as e:
            return {"exito": False, "error": f"Error al generar préstamo: {str(e)}"}

    # ==================== ENDPOINTS: BOLETAS Y ÓRDENES DE TRABAJO ====================
    def generar_boleta(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Genera una boleta u orden de cobro/servicio."""
        try:
            boleta = self.sistema.generar_boleta_cobro(
                rut_socio=datos["rut_socio"],
                username_usuario=datos["username_usuario"],
                tipo=datos.get("tipo", "BOLETA_PRESTAMO"),
                descripcion=datos.get("descripcion", "Servicios de biblioteca"),
                prestamo_id=datos.get("prestamo_id"),
                iva_pct=float(datos.get("iva_pct", 0.0)),
                descuento=float(datos.get("descuento", 0.0))
            )
            
            # Añadir líneas
            for linea_datos in datos.get("lineas", []):
                boleta.agregar_linea(
                    concepto=linea_datos["concepto"],
                    cantidad=int(linea_datos.get("cantidad", 1)),
                    precio_unitario=float(linea_datos.get("precio_unitario", 0.0)),
                    codigo_referencia=linea_datos.get("codigo_referencia", ""),
                    tipo_item=linea_datos.get("tipo_item", "SERVICIO")
                )
                
            self.sistema.guardar_boleta(boleta)
            return {
                "exito": True,
                "mensaje": f"Boleta #{boleta.numero} emitida.",
                "numero": boleta.numero,
                "total": boleta.total(),
                "recibo": boleta.generar_recibo_texto()
            }
        except Exception as e:
            return {"exito": False, "error": f"Error al generar boleta: {str(e)}"}

    # ==================== ENDPOINTS: PERSISTENCIA JSON ====================
    def guardar_en_json(self, ruta_archivo: Optional[str] = None) -> Dict[str, Any]:
        """Guarda la base de datos completa en JSON."""
        try:
            dao = JsonDao(ruta_archivo) if ruta_archivo else self.json_dao
            ruta_guardada = dao.exportar_desde_sistema(self.sistema)
            return {"exito": True, "mensaje": "Base de datos exportada a JSON con éxito.", "ruta": ruta_guardada}
        except Exception as e:
            return {"exito": False, "error": f"Error al exportar JSON: {str(e)}"}

    def cargar_desde_json(self, ruta_archivo: Optional[str] = None) -> Dict[str, Any]:
        """Importa y recarga la base de datos desde un archivo JSON."""
        try:
            dao = JsonDao(ruta_archivo) if ruta_archivo else self.json_dao
            datos = dao.cargar_base_datos()
            if not datos:
                return {"exito": False, "error": "El archivo JSON no existe o está vacío."}
                
            self.sistema.hidratar_desde_json(datos)
            return {"exito": True, "mensaje": "Base de datos recargada desde JSON exitosamente."}
        except Exception as e:
            return {"exito": False, "error": f"Error al cargar JSON: {str(e)}"}

    def consultar_dolar(self) -> Dict[str, Any]:
        """Retorna el valor actual del dólar observado."""
        valor = self.servicio_dolar.obtener_valor_dolar()
        return {
            "moneda": "USD",
            "valor_clp": valor,
            "fuente": "mindicador.cl / cache",
            "fecha": self.servicio_dolar.ultima_act.isoformat() if self.servicio_dolar.ultima_act else None
        }
