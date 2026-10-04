"""
========================================================================================
PAQUETE: dao
MÓDULO: json_dao.py
ROL EN EL PROYECTO:
    Data Access Object para persistencia y exportación/importación en archivos .JSON.
    Permite almacenar todas las colecciones (Socios, Usuarios, Catálogo, Préstamos, Boletas)
    en formato JSON legible y recargable.
========================================================================================
"""

import os
import json
from datetime import date, datetime
from typing import Dict, Any, Optional, List


class CustomJSONEncoder(json.JSONEncoder):
    """Codificador JSON personalizado para tipos de fecha y objetos de dominio."""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class JsonDao:
    """
    Gestor de persistencia en base de datos JSON (.json).
    """

    def __init__(self, ruta_archivo: str = "biblioteca_db.json"):
        self.ruta_archivo = ruta_archivo

    def guardar_base_datos(self, datos: Dict[str, Any]) -> str:
        """
        Escribe la estructura completa de datos en el archivo .json.
        """
        # Aseguramos timestamp de exportación
        datos["_metadatos"] = {
            "version": "2.0.0",
            "sistema": "Biblioteca Municipal Cordillera",
            "fecha_guardado": datetime.now().isoformat()
        }
        
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4, cls=CustomJSONEncoder)
            
        return os.path.abspath(self.ruta_archivo)

    def cargar_base_datos(self) -> Optional[Dict[str, Any]]:
        """
        Lee la estructura de datos desde el archivo .json si existe.
        """
        if not os.path.exists(self.ruta_archivo):
            return None
            
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR JSON_DAO] Error al leer archivo {self.ruta_archivo}: {e}")
            return None

    def exportar_desde_sistema(self, sistema) -> str:
        """
        Serializa en memoria todos los objetos del controlador SistemaBiblioteca a JSON.
        """
        socios_lista = []
        for s in sistema.registro_socios.values():
            socios_lista.append({
                "rut": s.get_rut(),
                "nombre_completo": s.get_nombre_completo(),
                "telefono": s.get_telefono(),
                "email": s.get_email(),
                "numero_socio": s.numero_socio,
                "fecha_inscripcion": s.fecha_inscripcion.isoformat() if s.fecha_inscripcion else None,
                "tiene_multa_pendiente": s.tiene_multa_pendiente,
                "monto_multa_acumulada": s.monto_multa_acumulada,
                "activo": s.activo
            })

        usuarios_lista = []
        for u in sistema.usuarios_sistema.values():
            usuarios_lista.append({
                "username": u.username,
                "rut": u.get_rut(),
                "nombre_completo": u.get_nombre_completo(),
                "telefono": u.get_telefono(),
                "email": u.get_email(),
                "password_hash": u.password_hash,
                "rol": u.obtener_rol(),
                "turno": getattr(u, "turno", None),
                "nivel_acceso": getattr(u, "nivel_acceso", None)
            })

        catalogo_lista = []
        for m in sistema.catalogo_materiales.values():
            item_data = {
                "codigo": m.codigo,
                "titulo": m.titulo,
                "autor_o_creador": m.autor_o_creador,
                "anio_publicacion": m.anio_publicacion,
                "precio_base_reposicion": m.precio_base_reposicion,
                "tipo_material": m.__class__.__name__.upper(),
                "prestado": m.esta_prestado()
            }
            # Atributos específicos
            if hasattr(m, "isbn"):
                item_data["isbn"] = m.isbn
                item_data["editorial"] = m.editorial
                item_data["numero_paginas"] = m.numero_paginas
            elif hasattr(m, "issn"):
                item_data["issn"] = m.issn
                item_data["numero_edicion"] = m.numero_edicion
                item_data["mes_publicacion"] = m.mes_publicacion
            elif hasattr(m, "formato"):
                item_data["formato"] = m.formato
                item_data["duracion_minutos"] = m.duracion_minutos
                item_data["clasificacion_edad"] = m.clasificacion_edad
            elif hasattr(m, "precio_usd"):
                item_data["precio_usd"] = m.precio_usd
                item_data["pais_origen"] = m.pais_origen
                item_data["recargo_aduanero_pct"] = m.recargo_aduanero_pct
                
            catalogo_lista.append(item_data)

        prestamos_lista = []
        for p in sistema.registro_prestamos:
            detalles_data = []
            for d in p.items_prestamo:
                detalles_data.append({
                    "id_detalle": d.id_detalle,
                    "material_codigo": d.material.codigo,
                    "fecha_inicio": d.fecha_inicio.isoformat() if d.fecha_inicio else None,
                    "dias_prestamo_otorgados": d.dias_prestamo_otorgados,
                    "fecha_devolucion_esperada": d.fecha_devolucion_esperada.isoformat() if d.fecha_devolucion_esperada else None,
                    "fecha_devolucion_real": d.fecha_devolucion_real.isoformat() if d.fecha_devolucion_real else None,
                    "cantidad_renovaciones": d.cantidad_renovaciones,
                    "devuelto": d.devuelto
                })
            prestamos_lista.append({
                "id_prestamo": p.id_prestamo,
                "socio_rut": p.socio.get_rut(),
                "bibliotecaria_username": p.bibliotecaria.username,
                "fecha_prestamo": p.fecha_prestamo.isoformat(),
                "estado": p.estado,
                "detalles": detalles_data
            })

        boletas_lista = []
        if hasattr(sistema, "registro_boletas"):
            for b in sistema.registro_boletas:
                boletas_lista.append(b.a_diccionario())

        datos_completos = {
            "socios": socios_lista,
            "usuarios": usuarios_lista,
            "catalogo": catalogo_lista,
            "prestamos": prestamos_lista,
            "boletas": boletas_lista
        }

        return self.guardar_base_datos(datos_completos)
