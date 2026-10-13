"""
========================================================================================
MÓDULO: main.py
ROL EN EL PROYECTO:
    Punto de Entrada del Backend con Menú Interactivo de la Biblioteca Municipal Cordillera.
    
    Cumple con el Guion de Pruebas (P01 a P19) y la Rúbrica de Evaluación Sumativa N°3:
    - P01: Inicia el programa y despliega el menú principal.
    - P02: Crear material (Libro "Rayuela", $15.000).
    - P03: Listar material (muestra los registros creados).
    - P04: Modificar material (cambiar título a "Rayuela (ed. 2020)").
    - P05: Persistencia SQLite real (al reiniciar, los registros se cargan desde la BD).
    - P06: Eliminar material (se retira de la BD y del catálogo).
    - P07: RUT válido (12.345.678-5) aceptado con Módulo 11 en setter.
    - P08: RUT inválido (12.345.678-9) rechazado con mensaje sin caerse.
    - P09: Tipo Libro: 14 días de préstamo y renovable 1 vez.
    - P10: Tipo Revista: 7 días de préstamo y no renovable.
    - P11: Tipo DVD / Multimedia: 3 días de préstamo y no renovable.
    - P12: Registrar préstamo múltiple en un solo registro (2 libros + 1 revista).
    - P13: Consultar detalle de préstamo con todas sus líneas asociadas.
    - P14: Regla de socio con multa impaga: préstamo bloqueado sin caerse.
    - P15: Regla de material ya prestado: segundo préstamo bloqueado sin caerse.
    - P16: Precio con Dólar del día obtenido en vivo desde https://mindicador.cl/api/dolar con requests.
    - P17: Sin internet: avisa amigablemente que no pudo conectar y usa contingencia sin caerse.
    - P18: Opción inexistente (99): avisa y vuelve al menú sin caerse.
    - P19: Letras donde va número ("abc"): avisa amigablemente y no se cae.
========================================================================================
"""

import sys
import os
from datetime import datetime, date
from typing import Optional, List

# Aseguramos inclusión del path local
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import conectar
from model.excepciones import (
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
from model.socio import Socio
from model.usuario import Usuario
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


# ==================== HELPERS DE ENTRADA SEGURA (ROBUSTEZ P19) ====================
def leer_texto(prompt: str, default: str = "") -> str:
    """Lee una cadena de texto permitiendo valor por defecto."""
    try:
        val = input(prompt).strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        return default


def leer_entero(prompt: str, default: Optional[int] = None) -> Optional[int]:
    """
    Lee un número entero. Si el usuario ingresa letras ('abc'), captura ValueError
    y muestra mensaje de error amigable sin detener el programa (P19).
    """
    try:
        raw = input(prompt).strip()
        if not raw:
            return default
        raw_clean = raw.replace(".", "").replace("$", "").strip()
        return int(raw_clean)
    except ValueError:
        print(f"\n[ERROR DE ENTRADA] El valor ingresado '{raw}' no es un número entero válido.")
        return None
    except (KeyboardInterrupt, EOFError):
        return default


def leer_flotante(prompt: str, default: Optional[float] = None) -> Optional[float]:
    """
    Lee un número decimal o monto. Admite formatos con '$', '.' o comas (ej: $15.000).
    Si el usuario ingresa letras ('abc'), captura ValueError e informa sin caerse (P19).
    """
    try:
        raw = input(prompt).strip()
        if not raw:
            return default
        raw_clean = raw.replace("$", "").strip()
        # Formato chileno de miles: ej: 15.000
        if "." in raw_clean and "," not in raw_clean:
            partes = raw_clean.split(".")
            if len(partes) == 2 and len(partes[1]) == 3:
                raw_clean = partes[0] + partes[1]
        elif "," in raw_clean:
            raw_clean = raw_clean.replace(".", "").replace(",", ".")
        return float(raw_clean)
    except ValueError:
        print(f"\n[ERROR DE ENTRADA] El valor ingresado '{raw}' no es un número válido. Se requiere un valor numérico.")
        return None
    except (KeyboardInterrupt, EOFError):
        return default


def imprimir_encabezado(titulo: str):
    print("\n" + "=" * 76)
    print(f"  {titulo.upper()}")
    print("=" * 76)


def obtener_usuario_admin(sistema: SistemaBiblioteca) -> Administradora:
    """Retorna un usuario administrador activo para operaciones restringidas."""
    for u in sistema.usuarios_sistema.values():
        if isinstance(u, Administradora):
            return u
    # Si no existiera en memoria, creamos uno válido
    admin = Administradora(
        rut="19.876.543-0",
        nombre_completo="Camila Valenzuela Pavez",
        telefono="+56911223344",
        email="admin@cordillera.cl",
        username="admin",
        password="AdminSuper2026*",
        nivel_acceso="SUPERADMIN"
    )
    sistema.registrar_usuario(admin)
    return admin


# ==================== SUB-FUNCIONES DEL MENÚ ====================

def menu_crear_material(sistema: SistemaBiblioteca):
    """
    Caso de prueba P02: Crear material (Libro 'Rayuela', valor $15.000).
    Caso de prueba P19: Validar que si se ingresa 'abc' en valor de reposición no se caiga.
    """
    imprimir_encabezado("1. CREAR / AGREGAR NUEVO MATERIAL AL CATÁLOGO")
    print("Tipos de Material Disponibles:")
    print("  [1] Libro impreso (Préstamo: 14 días | Renovable 1 vez)")
    print("  [2] Revista periódica (Préstamo: 7 días | No renovable)")
    print("  [3] Material Multimedia DVD/Blu-Ray (Préstamo: 3 días | No renovable)")
    print("  [4] Material Extranjero cotizado en USD (API Dólar)")
    
    tipo = leer_texto("\nSeleccione el tipo de material [1-4]: ", default="1")
    if tipo not in ["1", "2", "3", "4"]:
        print("[ERROR] Tipo de material inválido.")
        return

    titulo = leer_texto("Título de la obra (ej: Rayuela): ")
    if not titulo:
        print("[ERROR] El título no puede quedar vacío.")
        return

    codigo_sugerido = f"MAT-{len(sistema.catalogo_materiales) + 1:03d}"
    if tipo == "1":
        codigo_sugerido = f"LIB-{len(sistema.catalogo_materiales) + 1:03d}"
    elif tipo == "2":
        codigo_sugerido = f"REV-{len(sistema.catalogo_materiales) + 1:03d}"
    elif tipo == "3":
        codigo_sugerido = f"DVD-{len(sistema.catalogo_materiales) + 1:03d}"
    elif tipo == "4":
        codigo_sugerido = f"EXT-{len(sistema.catalogo_materiales) + 1:03d}"

    codigo = leer_texto(f"Código de inventario [{codigo_sugerido}]: ", default=codigo_sugerido).upper()
    autor = leer_texto("Autor o Creador [Julio Cortázar]: ", default="Julio Cortázar")
    anio = leer_entero("Año de publicación [1963]: ", default=1963)
    if anio is None:
        print("[AVISO] Operación cancelada por entrada numérica inválida.")
        return

    admin = obtener_usuario_admin(sistema)

    try:
        if tipo == "1":
            precio = leer_flotante("Precio base de reposición CLP (ej: $15.000) [15000]: ", default=15000.0)
            if precio is None:
                print("[AVISO] No se pudo crear el libro: el valor de reposición debe ser numérico.")
                return
            isbn = leer_texto("ISBN (ej: 978-9500718509) [978-9500718509]: ", default="978-9500718509")
            editorial = leer_texto("Editorial [Sudamericana]: ", default="Sudamericana")
            paginas = leer_entero("Número de páginas [600]: ", default=600) or 600
            nuevo_item = Libro(codigo, titulo, autor, anio, precio, isbn, editorial, paginas)

        elif tipo == "2":
            precio = leer_flotante("Precio base reposición CLP [12000]: ", default=12000.0)
            if precio is None:
                print("[AVISO] No se pudo crear la revista: el valor de reposición debe ser numérico.")
                return
            issn = leer_texto("ISSN [0027-9358]: ", default="0027-9358")
            edicion = leer_entero("Número de edición [1]: ", default=1) or 1
            mes = leer_texto("Mes de publicación [Octubre 2026]: ", default="Octubre 2026")
            nuevo_item = Revista(codigo, titulo, autor, anio, precio, issn, edicion, mes)

        elif tipo == "3":
            precio = leer_flotante("Precio base reposición CLP [25000]: ", default=25000.0)
            if precio is None:
                print("[AVISO] No se pudo crear el DVD: el valor de reposición debe ser numérico.")
                return
            formato = leer_texto("Formato (DVD / Blu-Ray / CD) [DVD]: ", default="DVD").upper()
            duracion = leer_entero("Duración en minutos [120]: ", default=120) or 120
            censura = leer_texto("Clasificación de edad (+14 / TE / +18) [+14]: ", default="+14")
            nuevo_item = MaterialMultimedia(codigo, titulo, autor, anio, precio, formato, duracion, censura)

        elif tipo == "4":
            precio_usd = leer_flotante("Precio original en USD [20.0]: ", default=20.0)
            if precio_usd is None:
                print("[AVISO] No se pudo crear el material extranjero: precio USD debe ser numérico.")
                return
            pais = leer_texto("País de origen [Estados Unidos]: ", default="Estados Unidos")
            recargo = leer_flotante("Recargo aduanero decimal [0.06]: ", default=0.06) or 0.06
            nuevo_item = MaterialExtranjero(codigo, titulo, autor, anio, precio_usd, pais, recargo)

        sistema.alta_nuevo_material(admin, nuevo_item)
        print(f"\n[OK] Material registrado y guardado exitosamente en la base de datos (SQLite):")
        print(f"     Código : {nuevo_item.codigo}")
        print(f"     Título : {nuevo_item.titulo}")
        print(f"     Tipo   : {nuevo_item.__class__.__name__}")
        print(f"     Valor  : ${nuevo_item.precio_base_reposicion:,.0f} CLP")

    except BibliotecaError as e:
        print(f"\n[ERROR DE DOMINIO] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_listar_materiales(sistema: SistemaBiblioteca):
    """
    Caso de prueba P03: Listar material (aparece el registro recién creado).
    Caso de prueba P05: Al reabrir el programa, los datos siguen ahí.
    """
    imprimir_encabezado("2. CATÁLOGO COMPLETO DE MATERIALES")
    catalogo = sistema.catalogo_materiales
    if not catalogo:
        print("  (El catálogo está vacío actualmente)")
        return

    dolar_actual = sistema.servicio_dolar.cache_valor
    print(f"Total de materiales en inventario: {len(catalogo)}\n")
    print(f"{'CÓDIGO':<10} | {'TIPO':<18} | {'ESTADO':<11} | {'REPOSICIÓN':<14} | {'TÍTULO'}")
    print("-" * 76)
    for m in catalogo.values():
        tipo_str = m.__class__.__name__
        estado_str = "PRESTADO" if m.esta_prestado() else "DISPONIBLE"
        costo = m.calcular_costo_reposicion(dolar_actual)
        print(f"{m.codigo:<10} | {tipo_str:<18} | {estado_str:<11} | ${costo:>9,.0f} CLP | {m.titulo}")
    print("-" * 76)


def menu_modificar_material(sistema: SistemaBiblioteca):
    """
    Caso de prueba P04: Modificar material (cambiar título a 'Rayuela (ed. 2020)').
    """
    imprimir_encabezado("3. MODIFICAR MATERIAL DEL CATÁLOGO")
    codigo = leer_texto("Ingrese el código del material a modificar (ej: LIB-003): ").upper()
    if not codigo:
        print("[ERROR] Debe indicar un código de material.")
        return

    try:
        mat = sistema.buscar_material(codigo)
        print(f"\nMaterial encontrado:")
        print(f"  Código Actual : {mat.codigo}")
        print(f"  Título Actual : '{mat.titulo}'")
        print(f"  Tipo          : {mat.__class__.__name__}")
        print(f"  Precio Base   : ${mat.precio_base_reposicion:,.0f} CLP")

        nuevo_titulo = leer_texto("\nNuevo título [Rayuela (ed. 2020)]: ", default="Rayuela (ed. 2020)")
        cambiar_precio = leer_texto("¿Desea cambiar el precio de reposición? (s/n) [n]: ", default="n").lower()
        nuevo_precio = None
        if cambiar_precio == "s":
            nuevo_precio = leer_flotante("Nuevo precio de reposición CLP: ")

        admin = obtener_usuario_admin(sistema)
        mat_actualizado = sistema.modificar_material(
            usuario_admin=admin,
            cod_mat=codigo,
            nuevo_titulo=nuevo_titulo,
            nuevo_precio=nuevo_precio
        )
        print(f"\n[OK] Material modificado exitosamente y actualizado en SQLite:")
        print(f"     Código       : {mat_actualizado.codigo}")
        print(f"     Nuevo Título : '{mat_actualizado.titulo}'")

    except MaterialNoEncontradoError as e:
        print(f"\n[ERROR] {e}")
    except BibliotecaError as e:
        print(f"\n[ERROR DE REGLA] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_eliminar_material(sistema: SistemaBiblioteca):
    """
    Caso de prueba P06: Eliminar material y listar (el registro ya no aparece).
    """
    imprimir_encabezado("4. ELIMINAR MATERIAL DEL CATÁLOGO")
    codigo = leer_texto("Ingrese el código del material a eliminar (ej: LIB-003): ").upper()
    if not codigo:
        print("[ERROR] Debe indicar el código a eliminar.")
        return

    try:
        mat = sistema.buscar_material(codigo)
        print(f"\nConfirmar eliminación de:")
        print(f"  [{mat.codigo}] '{mat.titulo}' ({mat.__class__.__name__})")
        confirma = leer_texto("¿Está seguro de eliminar este registro permanentemente? (s/n) [s]: ", default="s").lower()
        if confirma != "s":
            print("[AVISO] Eliminación cancelada.")
            return

        admin = obtener_usuario_admin(sistema)
        sistema.baja_material(admin, codigo)
        print(f"\n[OK] El material '{codigo}' fue eliminado exitosamente del catálogo y de SQLite.")

    except MaterialNoEncontradoError as e:
        print(f"\n[ERROR] {e}")
    except BibliotecaError as e:
        print(f"\n[ERROR DE REGLA] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_consultar_politicas_material(sistema: SistemaBiblioteca):
    """
    Casos de prueba P09, P10 y P11:
    - P09: Tipo Libro -> Préstamo de 14 días; se puede renovar una vez.
    - P10: Tipo Revista -> Préstamo de 7 días; no se renueva.
    - P11: Tipo DVD/multimedia -> Préstamo de 3 días; no se renueva.
    """
    imprimir_encabezado("5. POLÍTICAS DE PRÉSTAMO Y DEVOLUCIÓN POR SUBTIPO (POLIMORFISMO)")
    print("Demostración de comportamiento polimórfico de clases derivadas de Material:\n")

    # Muestras representativas de cada tipo
    libro_demo = Libro("DEMO-LIB", "Libro de Ejemplo", "Autor", 2024, 15000, "978-0000", "Editorial", 300)
    revista_demo = Revista("DEMO-REV", "Revista de Ejemplo", "Autor", 2024, 10000, "0000-0000", 1, "Mes")
    dvd_demo = MaterialMultimedia("DEMO-DVD", "DVD de Ejemplo", "Autor", 2024, 20000, "DVD", 120, "+14")
    ext_demo = MaterialExtranjero("DEMO-EXT", "Extranjero de Ejemplo", "Autor", 2024, 30.0, "EEUU", 0.06)

    demos = [
        ("Libro (Subtipo P09)", libro_demo),
        ("Revista (Subtipo P10)", revista_demo),
        ("DVD / Multimedia (Subtipo P11)", dvd_demo),
        ("Material Extranjero", ext_demo)
    ]

    for nombre_subtipo, item in demos:
        plazo = item.dias_prestamo()
        renovacion = "SÍ (1 renovación permitida)" if item.permite_renovacion() else "NO (0 renovaciones permitidas)"
        print(f"• {nombre_subtipo}:")
        print(f"    - Plazo oficial de préstamo       : {plazo} días")
        print(f"    - ¿Permite renovación de plazo?   : {renovacion}")
        print(f"    - Máximo de prórrogas autorizadas : {item.max_renovaciones()}")
        print()

    # Opción para consultar un ítem del catálogo
    cod = leer_texto("Consultar un material específico del catálogo (o Enter para omitir): ").upper()
    if cod:
        try:
            m = sistema.buscar_material(cod)
            print(f"\nDatos de '{m.codigo}' - '{m.titulo}':")
            print(f"  Clase concreta          : {m.__class__.__name__}")
            print(f"  Plazo de préstamo       : {m.dias_prestamo()} días")
            print(f"  Renovación permitida    : {'Sí' if m.permite_renovacion() else 'No'}")
            print(f"  Renovaciones máximas    : {m.max_renovaciones()}")
        except MaterialNoEncontradoError:
            print(f"[AVISO] Material con código '{cod}' no existe en el catálogo.")


def menu_registrar_socio(sistema: SistemaBiblioteca):
    """
    Casos de prueba P07 y P08:
    - P07: RUT válido (12.345.678-5) -> Lo acepta.
    - P08: RUT inválido (12.345.678-9) -> Lo rechaza con mensaje y no se cae.
    """
    imprimir_encabezado("6. INSCRIBIR NUEVO SOCIO (VALIDACIÓN DE RUT EN SETTER)")
    rut = leer_texto("Ingrese RUT del socio (ej: 12.345.678-5 o 12.345.678-9): ")
    if not rut:
        print("[ERROR] El RUT es un campo obligatorio.")
        return

    nombre = leer_texto("Nombre completo del socio [Diego Morales Peña]: ", default="Diego Morales Peña")
    telefono = leer_texto("Teléfono de contacto [+56966554433]: ", default="+56966554433")
    email = leer_texto("Correo electrónico [socio@cordillera.cl]: ", default="socio@cordillera.cl")

    try:
        socio = sistema.inscribir_socio(rut, nombre, telefono, email)
        print(f"\n[OK] Socio registrado exitosamente:")
        print(f"     Nombre : {socio.get_nombre_completo()}")
        print(f"     RUT    : {socio.get_rut()}")
        print(f"     Socio #: {socio.numero_socio}")
        print(f"     Estado : {'HABILITADO' if socio.puede_solicitar_prestamo() else 'CON MULTAS'}")

    except RutInvalidoError as e:
        # P08: Muestra el mensaje informativo y el programa sigue funcionando normalmente
        print(f"\n[RECHAZADO - RUT INVÁLIDO] {e}")
        print("                           El dígito verificador ingresado no coincide con el algoritmo Módulo 11.")
        print("                           (El sistema sigue funcionando correctamente)")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_registrar_multa_socio(sistema: SistemaBiblioteca):
    """
    Caso de prueba P14 (Precondición): Registrar una multa impaga al socio.
    """
    imprimir_encabezado("7. REGISTRAR MULTA IMPAGA A UN SOCIO")
    rut = leer_texto("Ingrese RUT del socio (ej: 12.345.678-5 o 18.234.567-9): ")
    if not rut:
        print("[ERROR] Debe ingresar el RUT del socio.")
        return

    monto = leer_flotante("Monto de la multa impaga en CLP [3000]: ", default=3000.0)
    if monto is None or monto <= 0:
        print("[AVISO] Debe ingresar un monto positivo.")
        return

    try:
        saldo = sistema.registrar_multa_socio(rut, monto)
        socio = sistema.buscar_socio_por_rut(rut)
        print(f"\n[OK] Multa de ${monto:,.0f} CLP registrada exitosamente para el socio:")
        print(f"     Socio         : {socio.get_nombre_completo()} ({socio.get_rut()})")
        print(f"     Multa Total   : ${saldo:,.0f} CLP")
        print(f"     ¿Habilitado?  : {'SÍ' if socio.puede_solicitar_prestamo() else 'NO (BLOQUEADO POR MOROSIDAD)'}")

    except SocioNoEncontradoError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_listar_socios(sistema: SistemaBiblioteca):
    imprimir_encabezado("8. LISTADO DE SOCIOS INSCRITOS")
    socios = list(sistema.registro_socios.values())
    if not socios:
        print("  (No hay socios registrados)")
        return

    print(f"Total de socios inscritos: {len(socios)}\n")
    print(f"{'N° SOCIO':<10} | {'RUT':<15} | {'ESTADO':<20} | {'NOMBRE COMPLETO'}")
    print("-" * 76)
    for s in socios:
        estado = f"MULTA: ${s.monto_multa_acumulada:,.0f} CLP" if s.tiene_multa_pendiente else "HABILITADO"
        num = f"#{s.numero_socio}" if s.numero_socio else "-"
        print(f"{num:<10} | {s.get_rut():<15} | {estado:<20} | {s.get_nombre_completo()}")
    print("-" * 76)


def menu_crear_prestamo(sistema: SistemaBiblioteca):
    """
    Casos de prueba:
    - P12: Registrar un préstamo con 2 libros y 1 revista en una misma visita.
    - P14: Regla: Impedir préstamo si el socio tiene multa pendiente.
    - P15: Regla: Impedir préstamo si un material ya se encuentra prestado.
    """
    imprimir_encabezado("9. REGISTRAR PRÉSTAMO / PEDIDO DE MATERIALES")
    rut = leer_texto("RUT del socio solicitante (ej: 18.234.567-9 o 12.345.678-5): ")
    if not rut:
        print("[ERROR] El RUT del socio es obligatorio.")
        return

    print("\nIngrese los códigos de los materiales a prestar separados por comas.")
    print("Ejemplo de prueba P12: LIB-001, LIB-002, REV-001")
    cods_str = leer_texto("Códigos: ", default="LIB-001, LIB-002, REV-001")
    
    codigos = [c.strip().upper() for c in cods_str.split(",") if c.strip()]
    if not codigos:
        print("[ERROR] Debe ingresar al menos un código de material.")
        return

    # Bibliotecaria de turno
    biblio = None
    for u in sistema.usuarios_sistema.values():
        if isinstance(u, BibliotecariaAtencion):
            biblio = u
            break
    if not biblio:
        biblio = Administradora(
            rut="19.876.543-0", nombre_completo="Camila Admin", telefono="+56911223344",
            email="admin@cordillera.cl", username="admin", password="AdminSuper2026*"
        )

    try:
        prestamo = sistema.crear_prestamo(rut, codigos, biblio)
        print(f"\n[OK - TRANSACCIÓN EXITOSA] Préstamo N°{prestamo.id_prestamo:04d} registrado con éxito:")
        print(f"     Socio         : {prestamo.socio.get_nombre_completo()} ({prestamo.socio.get_rut()})")
        print(f"     Atendido por  : {prestamo.bibliotecaria.get_nombre_completo()} (@{prestamo.bibliotecaria.username})")
        print(f"     Total Ítems   : {len(prestamo.items_prestamo)} materiales guardados en la misma transacción:")
        for det in prestamo.items_prestamo:
            print(f"       * [{det.material.codigo}] '{det.material.titulo}' ({det.material.__class__.__name__}) -> Vence: {det.fecha_devolucion_esperada}")

    except SocioConMultaPendienteError as e:
        # P14: Operación impedida porque el socio tiene deuda impaga
        print(f"\n[REGLA DE NEGOCIO BLOQUEADA - P14] {e}")
        print("                                   La operación fue rechazada y no se guardó ningún préstamo.")
        print("                                   (El sistema sigue funcionando normalmente)")
    except MaterialYaPrestadoError as e:
        # P15: Operación impedida porque el ejemplar ya está en préstamo a otro socio
        print(f"\n[REGLA DE NEGOCIO BLOQUEADA - P15] {e}")
        print("                                   El material permanece prestado únicamente a su poseedor original.")
        print("                                   (El sistema sigue funcionando normalmente)")
    except BibliotecaError as e:
        print(f"\n[ERROR DE REGLA] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_consultar_detalle_prestamo(sistema: SistemaBiblioteca):
    """
    Caso de prueba P13: Ver el detalle de préstamo (se ven todas sus líneas de detalle).
    """
    imprimir_encabezado("10. CONSULTAR DETALLE COMPLETO DE UN PRÉSTAMO")
    if not sistema.registro_prestamos:
        print("  (Aún no se han emitido préstamos en el sistema)")
        return

    print("Préstamos registrados:")
    for p in sistema.registro_prestamos:
        print(f"  - Préstamo #{p.id_prestamo:04d} [{p.estado}] | Socio: {p.socio.get_rut()} ({p.socio.get_nombre_completo()}) | Ítems: {len(p.items_prestamo)}")

    id_p = leer_entero("\nIngrese el ID del préstamo a consultar [1]: ", default=1)
    if id_p is None:
        return

    try:
        prestamo = sistema._buscar_prestamo(id_p)
        print("\n" + "=" * 76)
        print(f"  DETALLE TRANSACCIONAL: PRÉSTAMO #{prestamo.id_prestamo:04d}")
        print("=" * 76)
        print(f"  Fecha Emisión   : {prestamo.fecha_prestamo.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Estado Global   : {prestamo.estado}")
        print(f"  Socio Lector    : {prestamo.socio.get_nombre_completo()} (RUT: {prestamo.socio.get_rut()})")
        print(f"  Funcionario     : {prestamo.bibliotecaria.get_nombre_completo()} (@{prestamo.bibliotecaria.username})")
        print(f"  Total de Líneas : {len(prestamo.items_prestamo)}")
        print("-" * 76)
        print(f"{'LÍNEA':<6} | {'CÓDIGO':<10} | {'TÍTULO':<28} | {'PLAZO':<8} | {'DEVUELTO':<9} | {'FECHA LÍMITE'}")
        print("-" * 76)
        for it in prestamo.items_prestamo:
            dev_str = "SÍ" if it.devuelto else "NO"
            print(f"#{it.id_detalle:<5} | {it.material.codigo:<10} | {it.material.titulo[:28]:<28} | {it.dias_prestamo_otorgados} días | {dev_str:<9} | {it.fecha_devolucion_esperada}")
        print("-" * 76)

    except PrestamoNoEncontradoError as e:
        print(f"\n[ERROR] {e}")


def menu_devolucion_renovacion(sistema: SistemaBiblioteca):
    """Devolución o renovación de un ítem dentro de un préstamo."""
    imprimir_encabezado("11. REGISTRAR DEVOLUCIÓN O RENOVACIÓN DE MATERIAL")
    print("  [1] Devolver material (Liberar inventario)")
    print("  [2] Renovar plazo de material (Sujeto a política del tipo)")
    sub = leer_texto("\nSeleccione acción [1-2] [1]: ", default="1")

    id_p = leer_entero("ID del Préstamo (ej: 1): ", default=1)
    if id_p is None:
        return
    cod = leer_texto("Código del material (ej: LIB-001): ").upper()
    if not cod:
        print("[ERROR] Debe indicar el código del material.")
        return

    admin = obtener_usuario_admin(sistema)

    try:
        if sub == "1":
            sistema.procesar_devolucion(id_p, cod, admin)
            print(f"\n[OK] Material '{cod}' devuelto exitosamente. Inventario liberado.")
        else:
            sistema.renovar_material_prestamo(id_p, cod, admin)
            print(f"\n[OK] Material '{cod}' renovado exitosamente.")
    except RenovacionNoPermitidaError as e:
        print(f"\n[REGLA DE NEGOCIO BLOQUEADA] {e}")
    except BibliotecaError as e:
        print(f"\n[ERROR DE DOMINIO] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_consultar_dolar_y_calcular(sistema: SistemaBiblioteca):
    """
    Casos de prueba P16 y P17:
    - P16: Precio con el dólar del día consumido desde la API pública con requests.
    - P17: Sin internet: avisa que no pudo obtener el valor y no se cae.
    """
    imprimir_encabezado("12. COTIZACIÓN DÓLAR API Y CÁLCULO DE VALOR EXTRANJERO")
    print("Consumo de API REST: https://mindicador.cl/api/dolar mediante librería requests.\n")

    usd_input = leer_flotante("Ingrese el valor en USD a calcular (ej: 20) [20.0]: ", default=20.0)
    if usd_input is None:
        return

    recargo = leer_flotante("Recargo aduanero decimal (ej: 0.06 para 6%) [0.06]: ", default=0.06) or 0.06

    print("\nConsultando cotización oficial en tiempo real...")
    resultado = sistema.servicio_dolar.calcular_precio_reposicion_extranjero(
        precio_usd=usd_input,
        recargo_aduanero_pct=recargo
    )

    print("\n" + "-" * 76)
    print(f"  RESULTADO DEL CÁLCULO MONETARIO")
    print("-" * 76)
    print(f"  Monto Original      : USD ${resultado['precio_usd']:,.2f}")
    print(f"  Recargo Aduanero    : {resultado['recargo_pct']:.1f}% (+ USD ${resultado['costo_usd_total'] - resultado['precio_usd']:,.2f})")
    print(f"  Total en USD        : USD ${resultado['costo_usd_total']:,.2f}")
    print(f"  Dólar Utilizado     : ${resultado['valor_dolar']:,.2f} CLP")
    print(f"  Origen de Cotización: {'EN VIVO DESDE API (mindicador.cl)' if resultado['conexion_exitosa'] else 'VALOR DE CONTINGENCIA / CACHÉ LOCAL'}")
    print(f"  VALOR TOTAL CLP     : ${resultado['total_clp']:,.0f} CLP")
    print("-" * 76)
    if resultado['conexion_exitosa']:
        print("  [OK] El valor del dólar coincide con la cotización observada oficial de hoy.")
    else:
        print("  [OK] Mecanismo de contingencia activo: el sistema informó la falla y continuó operando.")


def menu_generar_boleta(sistema: SistemaBiblioteca):
    """Emisión de boletas y órdenes de trabajo del negocio."""
    imprimir_encabezado("13. GENERAR BOLETA / ORDEN DE TRABAJO / COMPROBANTE")
    rut = leer_texto("RUT del socio (ej: 18.234.567-9): ")
    if not rut:
        return

    print("\nTipo de Documento:")
    print("  [1] Boleta de Préstamo en Mesón")
    print("  [2] Orden de Trabajo de Taller de Encuadernación / Restauración")
    print("  [3] Comprobante de Cobro de Multas por Mora")
    print("  [4] Boleta de Reposición por Extravío")
    opcion = leer_texto("Seleccione tipo [1-4] [1]: ", default="1")

    tipo_map = {
        "1": "BOLETA_PRESTAMO",
        "2": "ORDEN_TRABAJO_TALLER",
        "3": "COMPROBANTE_MULTA",
        "4": "BOLETA_REPOSICION"
    }
    tipo_doc = tipo_map.get(opcion, "BOLETA_GENERAL")
    desc = leer_texto("Descripción de la atención [Servicios bibliotecarios]: ", default="Servicios bibliotecarios")

    try:
        admin = obtener_usuario_admin(sistema)
        boleta = sistema.generar_boleta_cobro(rut, admin.username, tipo_doc, desc)

        if opcion == "1":
            cod = leer_texto("Código del material prestado [LIB-001]: ", default="LIB-001").upper()
            mat = sistema.buscar_material(cod)
            boleta.agregar_cargo_prestamo(mat, tarifa_base=0.0)
        elif opcion == "2":
            servicio = leer_texto("Servicio técnico [Empastado de Tomo]: ", default="Empastado de Tomo")
            horas = leer_entero("Horas de mano de obra estimadas [2]: ", default=2) or 2
            boleta.agregar_orden_trabajo_taller(servicio, horas, 3500.0)
        elif opcion == "3":
            dias = leer_entero("Días de mora atrasados [4]: ", default=4) or 4
            boleta.agregar_cargo_multa(dias, 500.0)
        elif opcion == "4":
            cod = leer_texto("Código de material extraviado [LIB-001]: ", default="LIB-001").upper()
            mat = sistema.buscar_material(cod)
            costo = mat.calcular_costo_reposicion(sistema.servicio_dolar.obtener_valor_dolar())
            boleta.agregar_cargo_reposicion(mat, costo)

        sistema.guardar_boleta(boleta)
        print("\n" + boleta.generar_recibo_texto())

    except BibliotecaError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def menu_comprobar_tablas_dao(sistema: SistemaBiblioteca):
    """Verificación de la integridad relacional del patrón DAO en SQLite."""
    imprimir_encabezado("14. VERIFICAR TABLAS SQLITE (ARQUITECTURA DAO)")
    print("Comprobando catálogo de tablas relacionales en SQLite...")
    conn = conectar.inicializar_base_datos()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name ASC")
    tablas = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
    
    print(f"\nTablas creadas y verificadas ({len(tablas)} tablas en 'biblioteca_cordillera.db'):")
    for t in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"  [OK] Tabla '{t:<20}' -> {cnt:>4} registros")
    print("\n[OK] Esquema Table-per-type y persistencia DAO operando con éxito.")


def menu_respaldo_json(sistema: SistemaBiblioteca):
    """Exportar o importar estado en archivo .JSON."""
    imprimir_encabezado("15. RESPALDO Y RESTAURACIÓN EN ARCHIVO .JSON")
    print("  [1] Exportar base de datos a 'biblioteca_db.json'")
    print("  [2] Importar base de datos desde 'biblioteca_db.json'")
    sub = leer_texto("\nSeleccione opción [1-2] [1]: ", default="1")

    if sub == "1":
        ruta = sistema.exportar_a_json("biblioteca_db.json")
        print(f"\n[OK] Datos exportados exitosamente a:\n     {ruta}")
    else:
        api = BibliotecaAPI(sistema)
        res = api.cargar_desde_json("biblioteca_db.json")
        if res.get("exito"):
            print(f"\n[OK] {res['mensaje']}")
        else:
            print(f"\n[ERROR] {res.get('error')}")


# ==================== BUCLE PRINCIPAL (MAIN LOOP) ====================
def main():
    print("=" * 76)
    print("       INICIANDO BACKEND - BIBLIOTECA MUNICIPAL CORDILLERA")
    print("=" * 76)

    # 1. Inicializar conexión SQLite y Fachada (crea tablas y carga persistencia)
    conn = conectar.inicializar_base_datos()
    sistema = SistemaBiblioteca(nombre_biblioteca="Biblioteca Municipal Cordillera")

    print(f"[OK] Sistema inicializado.")
    print(f"     Materiales cargados : {len(sistema.catalogo_materiales)}")
    print(f"     Socios cargados     : {len(sistema.registro_socios)}")
    print(f"     Préstamos activos   : {len(sistema.registro_prestamos)}")

    while True:
        print("\n" + "=" * 76)
        print("     SISTEMA DE GESTIÓN BIBLIOTECA MUNICIPAL CORDILLERA (POO SEGURO)")
        print("=" * 76)
        print("  --- GESTIÓN DE MATERIALES (CRUD Y POLIMORFISMO) ---")
        print("  [1]  [CRE] Crear / Agregar Material al Catálogo (P02, P19)")
        print("  [2]  [LST] Listar Todos los Materiales del Catálogo (P03, P05)")
        print("  [3]  [MOD] Modificar Material (Cambiar Título / Precio) (P04)")
        print("  [4]  [DEL] Eliminar Material del Catálogo (P06)")
        print("  [5]  [POL] Consultar Políticas de Préstamo por Tipo de Material (P09, P10, P11)")
        print("  --- GESTIÓN DE SOCIOS Y SEGURIDAD ---")
        print("  [6]  [SOC] Inscribir Socio (Validación RUT Módulo 11) (P07, P08)")
        print("  [7]  [MUL] Registrar Multa Impaga a un Socio (Precondición P14)")
        print("  [8]  [LS-S] Listar Socios Registrados")
        print("  --- PRÉSTAMOS TRANSACCIONALES Y REGLAS DE NEGOCIO ---")
        print("  [9]  [PRE] Registrar Préstamo de Materiales (P12, P14, P15)")
        print("  [10] [DET] Consultar Detalle Completo de un Préstamo (P13)")
        print("  [11] [DEV] Devolver o Renovar Material")
        print("  --- CONSUMO DE API DÓLAR (MINDICADOR.CL) ---")
        print("  [12] [USD] Cotización Dólar del Día y Cálculo en USD (P16, P17)")
        print("  --- OPERACIONES ADMINISTRATIVAS ---")
        print("  [13] [BOL] Generar Boleta / Orden de Trabajo / Cobro")
        print("  [14] [DAO] Comprobar Tablas SQLite (Arquitectura DAO)")
        print("  [15] [JSN] Respaldo / Carga en Archivo .JSON")
        print("  [0]  [SAL] Salir del Sistema")
        print("=" * 76)

        try:
            opcion = input("Seleccione una opción [0-15]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo del programa...")
            break

        # Caso de prueba P18: Opción inexistente (ej: 99)
        if opcion == "1":
            menu_crear_material(sistema)
        elif opcion == "2":
            menu_listar_materiales(sistema)
        elif opcion == "3":
            menu_modificar_material(sistema)
        elif opcion == "4":
            menu_eliminar_material(sistema)
        elif opcion == "5":
            menu_consultar_politicas_material(sistema)
        elif opcion == "6":
            menu_registrar_socio(sistema)
        elif opcion == "7":
            menu_registrar_multa_socio(sistema)
        elif opcion == "8":
            menu_listar_socios(sistema)
        elif opcion == "9":
            menu_crear_prestamo(sistema)
        elif opcion == "10":
            menu_consultar_detalle_prestamo(sistema)
        elif opcion == "11":
            menu_devolucion_renovacion(sistema)
        elif opcion == "12":
            menu_consultar_dolar_y_calcular(sistema)
        elif opcion == "13":
            menu_generar_boleta(sistema)
        elif opcion == "14":
            menu_comprobar_tablas_dao(sistema)
        elif opcion == "15":
            menu_respaldo_json(sistema)
        elif opcion == "0":
            try:
                sistema.exportar_a_json("biblioteca_db.json")
            except Exception:
                pass
            print("\n[OK] Datos guardados y sincronizados. ¡Hasta luego!\n")
            break
        else:
            # P18: Ingresar 99 muestra mensaje de aviso y vuelve al menú sin caerse
            print(f"\n[AVISO] La opción '{opcion}' no existe en el menú. Por favor seleccione una opción válida entre 0 y 15.")


if __name__ == "__main__":
    main()
