"""
========================================================================================
MÓDULO: main.py
ROL EN EL PROYECTO:
    Punto de Entrada del Backend con Menú Interactivo Enumerado de la Biblioteca Cordillera.
    
    Permite gestionar:
    - Agregar libros y materiales (Table-per-type DAO)
    - Inscribir socios (RUT Módulo 11)
    - Crear pedidos y préstamos múltiples (Cabecera - Detalle)
    - Generar boletas y órdenes de trabajo (Cálculos de mora, USD y reposición)
    - Consultar API Dólar en vivo
    - Persistir y cargar bases de datos en formato .JSON
========================================================================================
"""

import sys
import os
from datetime import datetime, date

# Aseguramos inclusión del path local
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import conectar
from model.excepciones import (
    BibliotecaError,
    SocioConMultaPendienteError,
    MaterialYaPrestadoError,
    RenovacionNoPermitidaError,
    RutInvalidoError,
    PermisoInsuficienteError
)
from model.socio import Socio
from model.bibliotecaria_atencion import BibliotecariaAtencion
from model.administradora import Administradora
from model.libro import Libro
from model.revista import Revista
from model.material_multimedia import MaterialMultimedia
from model.material_extranjero import MaterialExtranjero
from model.boleta import Boleta
from api.servicio_dolar import ServicioDolarAPI
from api.biblioteca_api import BibliotecaAPI
from sistema_biblioteca import SistemaBiblioteca


def imprimir_encabezado(titulo: str):
    print("\n" + "=" * 76)
    print(f"  {titulo.upper()}")
    print("=" * 76)


def inicializar_datos_semilla(sistema: SistemaBiblioteca):
    """Carga datos iniciales de prueba para operar de inmediato."""
    # 1. Usuarios
    admin = Administradora(
        rut="19.876.543-0",
        nombre_completo="Camila Valenzuela Pavez",
        telefono="+56911223344",
        email="cvalenzuela@cordillera.cl",
        username="admin",
        password="AdminSuper2026*",
        nivel_acceso="SUPERADMIN"
    )
    biblio1 = BibliotecariaAtencion(
        rut="17.654.321-3",
        nombre_completo="Valentina Rojas Morales",
        telefono="+56922334455",
        email="vrojas@cordillera.cl",
        username="vrojas",
        password="PasswordBiblio123!",
        turno="Mañana"
    )
    biblio2 = BibliotecariaAtencion(
        rut="16.543.210-K",
        nombre_completo="Ignacio Soto Silva",
        telefono="+56933445566",
        email="isoto@cordillera.cl",
        username="isoto",
        password="PasswordBiblio456!",
        turno="Tarde"
    )
    sistema.registrar_usuario(admin)
    sistema.registrar_usuario(biblio1)
    sistema.registrar_usuario(biblio2)

    # 2. Socios
    socio1 = sistema.inscribir_socio(
        rut="18.234.567-9",
        nombre_completo="Andrés Castro Morán",
        telefono="+56988776655",
        email="andres.castro@inacap.cl"
    )
    socio2 = sistema.inscribir_socio(
        rut="15.432.109-8",
        nombre_completo="Beatriz Fuentes Lara",
        telefono="+56977665544",
        email="beatriz.fuentes@gmail.com"
    )
    socio3 = sistema.inscribir_socio(
        rut="12.345.678-5",
        nombre_completo="Diego Morales Peña",
        telefono="+56966554433",
        email="diego.morales@empresa.cl"
    )
    socio3.registrar_multa(2500.0)

    # 3. Materiales de catálogo
    libro1 = Libro(
        codigo="LIB-001",
        titulo="Cien Años de Soledad",
        autor_o_creador="Gabriel García Márquez",
        anio_publicacion=1967,
        precio_base_reposicion=28000.0,
        isbn="978-0307474728",
        editorial="Sudamericana",
        numero_paginas=471
    )
    libro2 = Libro(
        codigo="LIB-002",
        titulo="El Quijote de la Mancha",
        autor_o_creador="Miguel de Cervantes",
        anio_publicacion=1605,
        precio_base_reposicion=32000.0,
        isbn="978-8420412146",
        editorial="Alfaguara",
        numero_paginas=863
    )
    revista1 = Revista(
        codigo="REV-001",
        titulo="National Geographic en Español",
        autor_o_creador="Varios Autores",
        anio_publicacion=2024,
        precio_base_reposicion=12000.0,
        issn="0027-9358",
        numero_edicion=145,
        mes_publicacion="Agosto 2024"
    )
    dvd1 = MaterialMultimedia(
        codigo="DVD-001",
        titulo="Interstellar (Edición Especial 4K)",
        autor_o_creador="Christopher Nolan",
        anio_publicacion=2014,
        precio_base_reposicion=35000.0,
        formato="DVD",
        duracion_minutos=169,
        clasificacion_edad="+14"
    )
    extranjero1 = MaterialExtranjero(
        codigo="EXT-001",
        titulo="Artificial Intelligence: A Modern Approach (4th Ed)",
        autor_o_creador="Stuart Russell & Peter Norvig",
        anio_publicacion=2020,
        precio_usd=120.00,
        pais_origen="Estados Unidos",
        recargo_aduanero_pct=0.06
    )

    sistema.alta_nuevo_material(admin, libro1)
    sistema.alta_nuevo_material(admin, libro2)
    sistema.alta_nuevo_material(admin, revista1)
    sistema.alta_nuevo_material(admin, dvd1)
    sistema.alta_nuevo_material(admin, extranjero1)

    # 4. Préstamo inicial
    sistema.crear_prestamo(
        rut_socio=socio1.get_rut(),
        cods_materiales=["LIB-001", "REV-001"],
        usuario_atencion=biblio1
    )

    # 5. Boleta inicial
    b1 = sistema.generar_boleta_cobro(
        rut_socio=socio1.get_rut(),
        username_usuario=biblio1.username,
        tipo="BOLETA_PRESTAMO",
        descripcion="Préstamo N°0001 en mesón de atención",
        prestamo_id=1
    )
    b1.agregar_cargo_prestamo(libro1, tarifa_base=0.0)
    b1.agregar_cargo_prestamo(revista1, tarifa_base=0.0)
    sistema.guardar_boleta(b1)


# ==================== SUB-FUNCIONES DEL MENÚ ====================
def menu_agregar_libro(sistema: SistemaBiblioteca):
    imprimir_encabezado("1. AGREGAR NUEVO LIBRO O MATERIAL AL CATÁLOGO")
    print("Tipos disponibles:")
    print("  [1] Libro impreso (14 días / Renovable)")
    print("  [2] Revista periódica (7 días / No renovable)")
    print("  [3] Material Multimedia DVD/Blu-Ray (3 días / No renovable)")
    print("  [4] Material Extranjero en USD (7 días / Renovable + API Dólar)")
    
    tipo = input("\nSeleccione el tipo de material [1-4]: ").strip()
    codigo = input("Código de inventario (ej: LIB-003): ").strip().upper()
    titulo = input("Título: ").strip()
    autor = input("Autor o Creador: ").strip()
    anio = int(input("Año de publicación: ").strip() or "2024")
    admin = sistema.usuarios_sistema.get("admin") or list(sistema.usuarios_sistema.values())[0]

    try:
        if tipo == "1":
            isbn = input("ISBN (ej: 978-0123456789): ").strip() or "978-0000000000"
            editorial = input("Editorial: ").strip() or "Editorial Universal"
            paginas = int(input("Número de páginas: ").strip() or "250")
            precio = float(input("Precio base de reposición CLP: ").strip() or "25000")
            item = Libro(codigo, titulo, autor, anio, precio, isbn, editorial, paginas)
        elif tipo == "2":
            issn = input("ISSN (ej: 1234-5679): ").strip() or "0000-0000"
            edicion = int(input("Número de edición: ").strip() or "1")
            mes = input("Mes de publicación: ").strip() or "Septiembre 2026"
            precio = float(input("Precio base reposición CLP: ").strip() or "10000")
            item = Revista(codigo, titulo, autor, anio, precio, issn, edicion, mes)
        elif tipo == "3":
            formato = input("Formato (DVD / Blu-Ray / CD): ").strip().upper() or "DVD"
            duracion = int(input("Duración en minutos: ").strip() or "120")
            censura = input("Clasificación de edad (TE / +14 / +18): ").strip() or "TE"
            precio = float(input("Precio base reposición CLP: ").strip() or "20000")
            item = MaterialMultimedia(codigo, titulo, autor, anio, precio, formato, duracion, censura)
        elif tipo == "4":
            precio_usd = float(input("Precio original en USD: ").strip() or "50.0")
            pais = input("País de origen: ").strip() or "Estados Unidos"
            recargo = float(input("Recargo aduanero decimal (ej 0.06 para 6%): ").strip() or "0.06")
            item = MaterialExtranjero(codigo, titulo, autor, anio, precio_usd, pais, recargo)
        else:
            print("[ERROR] Tipo de material no reconocido.")
            return

        sistema.alta_nuevo_material(admin, item)
        print(f"\n[OK] Material registrado exitosamente:")
        print(f"     {item}")
    except BibliotecaError as e:
        print(f"\n[ERROR DE DOMINIO] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_registrar_socio(sistema: SistemaBiblioteca):
    imprimir_encabezado("2. REGISTRAR / INSCRIBIR NUEVO SOCIO")
    rut = input("Ingrese RUT chileno (ej: 18.234.567-9 o 182345679): ").strip()
    nombre = input("Nombre completo: ").strip()
    telefono = input("Teléfono: ").strip() or "+56900000000"
    email = input("Email: ").strip() or "socio@correo.cl"

    try:
        socio = sistema.inscribir_socio(rut, nombre, telefono, email)
        print(f"\n[OK] Socio registrado exitosamente:")
        print(f"     {socio}")
    except RutInvalidoError as e:
        print(f"\n[ERROR DE RUT] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_registrar_usuario(sistema: SistemaBiblioteca):
    imprimir_encabezado("3. REGISTRAR PERSONAL DEL SISTEMA")
    print("  [1] Bibliotecaria de Atención (Mesón)")
    print("  [2] Administradora (SUPERADMIN)")
    tipo = input("Seleccione rol [1-2]: ").strip()
    rut = input("RUT: ").strip()
    nombre = input("Nombre completo: ").strip()
    telefono = input("Teléfono: ").strip()
    email = input("Email: ").strip()
    username = input("Nombre de usuario (login): ").strip().lower()
    password = input("Contraseña: ").strip()

    try:
        if tipo == "1":
            turno = input("Turno (Mañana / Tarde): ").strip() or "Mañana"
            user = BibliotecariaAtencion(rut, nombre, telefono, email, username, password, turno)
        else:
            user = Administradora(rut, nombre, telefono, email, username, password, "SUPERADMIN")

        sistema.registrar_usuario(user)
        print(f"\n[OK] Usuario registrado exitosamente:")
        print(f"     {user}")
    except BibliotecaError as e:
        print(f"\n[ERROR DE DOMINIO] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_crear_pedido(sistema: SistemaBiblioteca):
    imprimir_encabezado("4. CREAR PEDIDO / ORDEN DE PRÉSTAMO")
    rut = input("RUT del socio solicitante: ").strip()
    username_biblio = input("Usuario funcionario que atiende (ej: vrojas o admin): ").strip().lower() or "vrojas"
    cods_str = input("Códigos de materiales separados por coma (ej: LIB-002, DVD-001): ").strip()
    
    codigos = [c.strip().upper() for c in cods_str.split(",") if c.strip()]
    if not codigos:
        print("[ERROR] No especificó ningún código.")
        return

    try:
        user = sistema.usuarios_sistema.get(username_biblio) or list(sistema.usuarios_sistema.values())[0]
        prestamo = sistema.crear_prestamo(rut, codigos, user)
        print(f"\n[OK] Préstamo creado con éxito:")
        print(f"     {prestamo}")
        print("\n  Líneas asignadas:")
        for det in prestamo.items_prestamo:
            print(f"    - {det}")
    except BibliotecaError as e:
        print(f"\n[ERROR EN PRÉSTAMO] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_generar_boleta(sistema: SistemaBiblioteca):
    imprimir_encabezado("5. GENERAR BOLETA / ORDEN DE TRABAJO / COMPROBANTE DE COBRO")
    rut = input("RUT del socio: ").strip()
    username = input("Usuario funcionario (ej: vrojas o admin): ").strip().lower() or "vrojas"
    
    print("\nTipo de Documento:")
    print("  [1] Boleta de Atención y Préstamo (Tarifas / Comprobante de Entrega)")
    print("  [2] Orden de Trabajo Técnico (Taller de Restauración / Encuadernación)")
    print("  [3] Comprobante de Pago de Multas por Mora")
    print("  [4] Boleta de Reposición por Pérdida / Deterioro (Extranjero en USD/CLP)")
    opcion_tipo = input("Seleccione tipo [1-4]: ").strip()

    tipo_map = {
        "1": ("BOLETA_PRESTAMO", "Entrega y registro de material bibliográfico"),
        "2": ("ORDEN_TRABAJO_TALLER", "Servicios técnicos de taller y restauración de libros"),
        "3": ("COMPROBANTE_MULTA", "Cancelación de multas por entrega tardía"),
        "4": ("BOLETA_REPOSICION", "Cobro de indemnización y reposición de ejemplar")
    }
    tipo_doc, desc_def = tipo_map.get(opcion_tipo, ("BOLETA_GENERAL", "Servicios de biblioteca"))
    desc = input(f"Descripción [{desc_def}]: ").strip() or desc_def

    try:
        boleta = sistema.generar_boleta_cobro(
            rut_socio=rut,
            username_usuario=username,
            tipo=tipo_doc,
            descripcion=desc
        )

        if opcion_tipo == "1":
            cod = input("Código del material prestado: ").strip().upper()
            mat = sistema.buscar_material(cod)
            boleta.agregar_cargo_prestamo(mat, tarifa_base=0.0)
        elif opcion_tipo == "2":
            servicio = input("Servicio técnico (ej: Empastado de tomo, Reemplazo de lomo): ").strip()
            horas = int(input("Horas de mano de obra estimadas: ").strip() or "2")
            tarifa = float(input("Tarifa por hora CLP [3500]: ").strip() or "3500")
            boleta.agregar_orden_trabajo_taller(servicio, horas, tarifa)
        elif opcion_tipo == "3":
            dias = int(input("Días de atraso en mora: ").strip() or "5")
            tarifa = float(input("Tarifa diaria CLP [500]: ").strip() or "500")
            boleta.agregar_cargo_multa(dias, tarifa)
        elif opcion_tipo == "4":
            cod = input("Código del material extraviado: ").strip().upper()
            mat = sistema.buscar_material(cod)
            dolar_act = sistema.servicio_dolar.obtener_valor_dolar()
            costo = mat.calcular_costo_reposicion(dolar_act)
            boleta.agregar_cargo_reposicion(mat, costo)

        sistema.guardar_boleta(boleta)
        print("\n" + boleta.generar_recibo_texto())
        
        pagar = input("¿Desea marcar la boleta/orden como PAGADA en caja ahora? (s/n): ").strip().lower()
        if pagar == "s":
            boleta.pagar()
            sistema.guardar_boleta(boleta)
            print(f"[OK] Boleta N°{boleta.numero:06d} marcada como PAGADA.")
    except BibliotecaError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_devolucion_renovacion(sistema: SistemaBiblioteca):
    imprimir_encabezado("6. DEVOLUCIÓN O RENOVACIÓN DE MATERIALES")
    print("  [1] Devolver material")
    print("  [2] Renovar plazo de material")
    sub = input("Opción [1-2]: ").strip()
    id_p = int(input("ID del Préstamo (ej: 1): ").strip())
    cod = input("Código del material (ej: LIB-001): ").strip().upper()
    user = sistema.usuarios_sistema.get("vrojas") or list(sistema.usuarios_sistema.values())[0]

    try:
        if sub == "1":
            sistema.procesar_devolucion(id_p, cod, user)
            print(f"[OK] Material '{cod}' devuelto exitosamente. Inventario liberado.")
        else:
            sistema.renovar_material_prestamo(id_p, cod, user)
            print(f"[OK] Material '{cod}' renovado exitosamente.")
    except BibliotecaError as e:
        print(f"\n[REGLA DE NEGOCIO] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_consultar_dolar(sistema: SistemaBiblioteca):
    imprimir_encabezado("7. COTIZACIÓN DÓLAR OBSERVADO (API EN TIEMPO REAL)")
    dolar_api = ServicioDolarAPI()
    print("Consultando API mindicador.cl...")
    valor = dolar_api.obtener_valor_dolar()
    print(f"\n  [USD] Valor Dólar Actual : ${valor:,.2f} CLP")
    print(f"  [API] Endpoint REST     : {dolar_api.endpoint_url}")
    print(f"  [OK]  Mecanismo Fallback: Activo con caché de contingencia.")


def menu_guardar_json(sistema: SistemaBiblioteca):
    imprimir_encabezado("8. GUARDAR / EXPORTAR BASE DE DATOS EN ARCHIVO .JSON")
    ruta = input("Ruta de archivo .json [biblioteca_db.json]: ").strip() or "biblioteca_db.json"
    try:
        ruta_abs = sistema.exportar_a_json(ruta)
        print(f"\n[OK] Base de datos guardada y sincronizada exitosamente en:")
        print(f"     {ruta_abs}")
    except Exception as e:
        print(f"\n[ERROR AL GUARDAR JSON] {e}")


def menu_cargar_json(sistema: SistemaBiblioteca):
    imprimir_encabezado("9. CARGAR / IMPORTAR BASE DE DATOS DESDE ARCHIVO .JSON")
    ruta = input("Ruta de archivo .json [biblioteca_db.json]: ").strip() or "biblioteca_db.json"
    try:
        api = BibliotecaAPI(sistema)
        resp = api.cargar_desde_json(ruta)
        if resp.get("exito"):
            print(f"\n[OK] {resp['mensaje']}")
        else:
            print(f"\n[ERROR] {resp.get('error')}")
    except Exception as e:
        print(f"\n[ERROR AL CARGAR JSON] {e}")


def menu_listar_todo(sistema: SistemaBiblioteca):
    imprimir_encabezado("10. LISTADOS GENERALES DEL SISTEMA")
    dolar = sistema.servicio_dolar.obtener_valor_dolar()

    print("\n--- [CAT] CATÁLOGO DE MATERIALES ---")
    for m in sistema.catalogo_materiales.values():
        costo = m.calcular_costo_reposicion(dolar)
        print(f"  - [{m.codigo}] '{m.titulo}' | {m.__class__.__name__} | Reposición: ${costo:,.0f} CLP | {'PRESTADO' if m.esta_prestado() else 'DISPONIBLE'}")

    print("\n--- [SOC] REGISTRO DE SOCIOS ---")
    for s in sistema.registro_socios.values():
        estado = f"CON MULTA (${s.monto_multa_acumulada:,.0f} CLP)" if s.tiene_multa_pendiente else "HABILITADO"
        print(f"  - {s.get_nombre_completo()} (RUT: {s.get_rut()}) | Socio #{s.numero_socio} | Estado: {estado}")

    print("\n--- [PRE] PRÉSTAMOS REALIZADOS ---")
    for p in sistema.registro_prestamos:
        print(f"  - Préstamo #{p.id_prestamo:04d} [{p.estado}] - Socio: {p.socio.get_rut()} - Ítems: {len(p.items_prestamo)}")
        for it in p.items_prestamo:
            print(f"      * [{it.material.codigo}] {it.material.titulo} (Devuelto: {it.devuelto})")

    print("\n--- [BOL] BOLETAS Y ÓRDENES DE TRABAJO ---")
    if sistema.registro_boletas:
        for b in sistema.registro_boletas:
            print(f"  - Boleta N°{b.numero:06d} [{b.tipo}] - Socio: {b.socio.get_rut()} - Total: ${b.total():,.0f} CLP ({b.estado})")
    else:
        print("  (No hay boletas emitidas)")


def menu_inicializar_tablas(sistema: SistemaBiblioteca):
    imprimir_encabezado("11. INICIALIZAR / COMPROBAR TABLAS SQLITE (PATRÓN DAO)")
    print("Creando y verificando tablas con conexión SQLite...")
    conn = conectar.inicializar_base_datos()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name ASC")
    tablas = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
    
    print(f"\nTablas encontradas en la Base de Datos SQLite ({len(tablas)} tablas):")
    for t in tablas:
        print(f"  [OK] {t}")
    print("\n[OK] Todas las tablas inicializadas conforme al patrón DAO.")


# ==================== FUNCIÓN PRINCIPAL ====================
def main():
    print("=" * 76)
    print("       INICIANDO BACKEND - BIBLIOTECA MUNICIPAL CORDILLERA")
    print("=" * 76)

    # 1. Inicializar conexión SQLite y controlador Façade
    conn = conectar.inicializar_base_datos()
    sistema = SistemaBiblioteca(nombre_biblioteca="Biblioteca Municipal Cordillera")
    inicializar_datos_semilla(sistema)

    # Guardar estado inicial en JSON
    sistema.exportar_a_json("biblioteca_db.json")

    while True:
        print("\n" + "=" * 76)
        print("     SISTEMA DE GESTION BIBLIOTECA MUNICIPAL CORDILLERA (BACKEND)")
        print("=" * 76)
        print("  [1]  [LIB] Agregar Nuevo Libro o Material al Catálogo")
        print("  [2]  [SOC] Registrar / Inscribir Nuevo Socio (Validación Módulo 11)")
        print("  [3]  [USR] Registrar Personal del Sistema (Bibliotecaria / Admin)")
        print("  [4]  [PED] Crear Pedidos / Préstamos de Materiales (Ítems Múltiples)")
        print("  [5]  [BOL] Generar Boletas, Órdenes de Trabajo y Comprobantes")
        print("  [6]  [DEV] Registrar Devolución o Renovación de Material")
        print("  [7]  [USD] Consultar Cotización Dólar en Tiempo Real (API REST)")
        print("  [8]  [SAV] Guardar / Exportar Base de Datos en Archivo .JSON")
        print("  [9]  [LOD] Cargar / Importar Base de Datos desde Archivo .JSON")
        print("  [10] [LST] Listar Catálogo, Socios, Préstamos y Boletas")
        print("  [11] [DAO] Inicializar / Comprobar Tablas SQLite (Patrón DAO)")
        print("  [0]  [EXT] Salir")
        print("=" * 76)

        try:
            opcion = input("Seleccione una opción [0-11]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            break

        if opcion == "1":
            menu_agregar_libro(sistema)
        elif opcion == "2":
            menu_registrar_socio(sistema)
        elif opcion == "3":
            menu_registrar_usuario(sistema)
        elif opcion == "4":
            menu_crear_pedido(sistema)
        elif opcion == "5":
            menu_generar_boleta(sistema)
        elif opcion == "6":
            menu_devolucion_renovacion(sistema)
        elif opcion == "7":
            menu_consultar_dolar(sistema)
        elif opcion == "8":
            menu_guardar_json(sistema)
        elif opcion == "9":
            menu_cargar_json(sistema)
        elif opcion == "10":
            menu_listar_todo(sistema)
        elif opcion == "11":
            menu_inicializar_tablas(sistema)
        elif opcion == "0":
            # Auto-guardar en JSON al salir
            sistema.exportar_a_json("biblioteca_db.json")
            print("\n[OK] Datos guardados en 'biblioteca_db.json'. ¡Hasta luego!\n")
            break
        else:
            print("[AVISO] Opción inválida. Por favor seleccione una opción entre 0 y 11.")


if __name__ == "__main__":
    main()
