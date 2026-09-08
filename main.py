"""
========================================================================================
MÓDULO: main.py
ROL EN EL PROYECTO:
    Punto de Entrada y Demostración Integral del Sistema de la Biblioteca Cordillera.
    
    Este programa ejecuta un guión guiado que recorre y pone a prueba cada componente
    del modelo UML y sus 4 Reglas Infranqueables de Negocio:
    
    Flujo de la Demostración:
    1. Inicialización de la Fachada y Conexión a SQLite.
    2. Registro de Personal, validación Módulo 11 de RUT y autenticación SHA-256.
    3. Inscripción de Socios y estado de multas iniciales.
    4. Carga de Catálogo Polimórfico (Libros, Revistas, DVDs, Extranjero en USD con API Dólar).
    5. Transacción de Préstamo Múltiple (Cabecera Prestamo con líneas DetallePrestamo).
    6. Verificación de Políticas Polimórficas de Renovación (Libros vs Revistas).
    7. Comprobación de Reglas Infranqueables y captura de Excepciones del Dominio:
       - Regla 1: SocioConMultaPendienteError al intentar prestar a un socio moroso.
       - Regla 2: MaterialYaPrestadoError al intentar prestar un ítem ya en préstamo.
       - Regla 3: RutInvalidoError al intentar registrar un RUT con DV adulterado.
       - Regla 4: PermisoInsuficienteError al intentar que una bibliotecaria condone multas.
    8. Devolución de materiales, cálculo automático de atraso ($500 CLP/día) y condonación.
    9. Reporte de Pérdida de Material Extranjero cotizado con la API en vivo y pago en caja.
    10. Inspección directa de la Persistencia en base de datos SQLite y Bitácora de Auditoría.
========================================================================================
"""

from datetime import date, timedelta
from excepciones import (
    BibliotecaError,
    SocioConMultaPendienteError,
    MaterialYaPrestadoError,
    RenovacionNoPermitidaError,
    RutInvalidoError,
    PermisoInsuficienteError
)
from socio import Socio
from bibliotecaria_atencion import BibliotecariaAtencion
from administradora import Administradora
from libro import Libro
from revista import Revista
from material_multimedia import MaterialMultimedia
from material_extranjero import MaterialExtranjero
from servicio_dolar import ServicioDolarAPI
from sistema_biblioteca import SistemaBiblioteca


def imprimir_separador(titulo: str = ""):
    """Imprime un encabezado formateado en consola para delimitar cada sección."""
    print("\n" + "=" * 78)
    if titulo:
        print(f"  {titulo.upper()}")
        print("=" * 78)


def main():
    imprimir_separador("INICIANDO SISTEMA BIBLIOTECA MUNICIPAL CORDILLERA (POO PYTHON)")
    
    # -------------------------------------------------------------------------
    # 1. INICIALIZACIÓN DEL CONTROLADOR PRINCIPAL (FAÇADE)
    # -------------------------------------------------------------------------
    # Se instancia SistemaBiblioteca, que a su vez inicializa el Repositorio BD
    # creando automáticamente las tablas SQLite si no existían.
    sistema = SistemaBiblioteca(nombre_biblioteca="Biblioteca Municipal Cordillera")
    print(f"[INIT] Sistema inicializado exitosamente: '{sistema.nombre_biblioteca}'")
    print(f"[INIT] Base de datos conectada: 'biblioteca_cordillera.db'")

    # -------------------------------------------------------------------------
    # 2. REGISTRO DE PERSONAL & SEGURIDAD (RUT MÓDULO 11 + HASHING SHA-256)
    # -------------------------------------------------------------------------
    imprimir_separador("1. REGISTRO DE PERSONAL & SEGURIDAD (RUT MODULO 11 + SHA-256)")
    # Administradora con rol SUPERADMIN para dar de alta catálogo y condonar
    admin = Administradora(
        rut="19.876.543-0",
        nombre_completo="Camila Valenzuela Pavez",
        telefono="+56911223344",
        email="cvalenzuela@cordillera.cl",
        username="cvalenzuela",
        password="AdminSuper2026*",
        nivel_acceso="SUPERADMIN"
    )
    # Bibliotecarias de atención para mesón y préstamos
    bibliotecaria1 = BibliotecariaAtencion(
        rut="17.654.321-3",
        nombre_completo="Valentina Rojas Morales",
        telefono="+56922334455",
        email="vrojas@cordillera.cl",
        username="vrojas",
        password="PasswordBiblio123!",
        turno="Manana"
    )
    bibliotecaria2 = BibliotecariaAtencion(
        rut="16.543.210-K",
        nombre_completo="Ignacio Soto Silva",
        telefono="+56933445566",
        email="isoto@cordillera.cl",
        username="isoto",
        password="PasswordBiblio456!",
        turno="Tarde"
    )

    sistema.registrar_usuario(admin)
    sistema.registrar_usuario(bibliotecaria1)
    sistema.registrar_usuario(bibliotecaria2)

    print(f"[OK] {admin}")
    print(f"[OK] {bibliotecaria1}")
    print(f"[OK] {bibliotecaria2}")

    # Comprobación del mecanismo criptográfico de autenticación
    auth_ok = bibliotecaria1.autenticar("PasswordBiblio123!")
    auth_fail = bibliotecaria1.autenticar("clave_incorrecta")
    print(f"[AUTH] Autenticacion de @{bibliotecaria1.username} con clave correcta: {'EXITOSA' if auth_ok else 'FALLIDA'}")
    print(f"[AUTH] Autenticacion de @{bibliotecaria1.username} con clave erronea: {'FALLIDA (Correcto)' if not auth_fail else 'ERROR'}")

    # -------------------------------------------------------------------------
    # 3. INSCRIPCIÓN DE SOCIOS (VALIDACIÓN ESTRICTA DE RUT)
    # -------------------------------------------------------------------------
    imprimir_separador("2. INSCRIPCION DE SOCIOS (VALIDACION ESTRICTA DE RUT)")
    socio1 = sistema.inscribir_socio(
        rut="18.234.567-9",
        nombre_completo="Andres Castro Moran",
        telefono="+56988776655",
        email="andres.castro@inacap.cl"
    )
    socio2 = sistema.inscribir_socio(
        rut="15.432.109-8",
        nombre_completo="Beatriz Fuentes Lara",
        telefono="+56977665544",
        email="beatriz.fuentes@gmail.com"
    )
    # Socio 3: Registramos intencionalmente una multa inicial ($2,500 CLP) para
    # demostrar el bloqueo automático que impide solicitar préstamos
    socio3 = sistema.inscribir_socio(
        rut="12.345.678-5",
        nombre_completo="Diego Morales Pena",
        telefono="+56966554433",
        email="diego.morales@empresa.cl"
    )
    socio3.registrar_multa(2500.0)
    sistema.repositorio_bd.guardar_socio(socio3)

    print(f"[OK] {socio1}")
    print(f"[OK] {socio2}")
    print(f"[OK] {socio3} (Estado Multa: {socio3.tiene_multa_pendiente})")

    # -------------------------------------------------------------------------
    # 4. CATÁLOGO DE MATERIALES & CONSUMO DE API DÓLAR
    # -------------------------------------------------------------------------
    imprimir_separador("3. ALTA DE MATERIALES EN CATALOGO & API DOLAR EN TIEMPO REAL")
    dolar_api = ServicioDolarAPI()
    valor_dolar = dolar_api.obtener_valor_dolar()
    print(f"[API] Cotizacion actual Dolar Observado: ${valor_dolar:,.2f} CLP (Fuente: mindicador.cl / Cache)")

    # Instanciación polimórfica de los 4 tipos de material
    libro1 = Libro(
        codigo="LIB-001",
        titulo="Cien Anos de Soledad",
        autor_o_creador="Gabriel Garcia Marquez",
        anio_publicacion=1967,
        precio_base_reposicion=28000.0,
        isbn="978-0307474728",
        editorial="Sudamericana",
        numero_paginas=471
    )
    revista1 = Revista(
        codigo="REV-001",
        titulo="National Geographic en Espanol",
        autor_o_creador="Varios Autores",
        anio_publicacion=2024,
        precio_base_reposicion=12000.0,
        issn="0027-9358",
        numero_edicion=145,
        mes_publicacion="Agosto 2024"
    )
    dvd1 = MaterialMultimedia(
        codigo="DVD-001",
        titulo="Interstellar (Edicion Especial 4K)",
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

    # Alta en el catálogo realizada legítimamente por la Administradora
    sistema.alta_nuevo_material(admin, libro1)
    sistema.alta_nuevo_material(admin, revista1)
    sistema.alta_nuevo_material(admin, dvd1)
    sistema.alta_nuevo_material(admin, extranjero1)

    print(f"[OK] {libro1}")
    print(f"[OK] {revista1}")
    print(f"[OK] {dvd1}")
    print(f"[OK] {extranjero1} -> Reposicion calculada en CLP: ${extranjero1.calcular_valor_reposicion(valor_dolar):,.0f} CLP")

    # -------------------------------------------------------------------------
    # 5. TRANSACCIÓN DE PRÉSTAMO MÚLTIPLE (CABECERA & DETALLE)
    # -------------------------------------------------------------------------
    imprimir_separador("4. CREACION DE PRESTAMO MULTIPLE (CABECERA - DETALLE)")
    # Socio 1 solicita dos ítems distintos (un Libro y una Revista)
    prestamo1 = sistema.crear_prestamo(
        rut_socio="18.234.567-9",
        cods_materiales=["LIB-001", "REV-001"],
        usuario_atencion=bibliotecaria1
    )
    print(f"[OK] Prestamo generado exitosamente:")
    print(f"     {prestamo1}")
    for item in prestamo1.items_prestamo:
        print(f"     -> {item}")

    # -------------------------------------------------------------------------
    # 6. POLÍTICAS POLIMÓRFICAS DE RENOVACIÓN DE PLAZOS
    # -------------------------------------------------------------------------
    imprimir_separador("5. POLITICAS POLIMORFICAS DE RENOVACION DE PLAZO")
    
    # 1ra renovación de libro: Válida según reglamento (máx. 1 prórroga de 14 días)
    print(f"[*] Solicitando 1ra renovacion para Libro '{libro1.codigo}' (Permite hasta 1):")
    sistema.renovar_material_prestamo(prestamo1.id_prestamo, "LIB-001", bibliotecaria1)
    det_libro = prestamo1.buscar_detalle_por_codigo("LIB-001")
    print(f"    [OK] Renovado exitosamente. Nueva fecha esperada: {det_libro.fecha_devolucion_esperada.isoformat()}")

    # 2da renovación de libro: Debe ser rechazada con RenovacionNoPermitidaError
    print(f"\n[*] Solicitando 2da renovacion para Libro '{libro1.codigo}' (Supera limite):")
    try:
        sistema.renovar_material_prestamo(prestamo1.id_prestamo, "LIB-001", bibliotecaria1)
    except RenovacionNoPermitidaError as e:
        print(f"    [RECHAZO ESPERADO] {e}")

    # Intento de renovación en Revista: Debe ser rechazada de inmediato (0 renovaciones)
    print(f"\n[*] Solicitando renovacion para Revista '{revista1.codigo}' (Reglamento: 0 renovaciones):")
    try:
        sistema.renovar_material_prestamo(prestamo1.id_prestamo, "REV-001", bibliotecaria1)
    except RenovacionNoPermitidaError as e:
        print(f"    [RECHAZO ESPERADO] {e}")

    # -------------------------------------------------------------------------
    # 7. PRUEBA DE LAS 4 REGLAS INFRANQUEABLES & CAPTURA DE EXCEPCIONES
    # -------------------------------------------------------------------------
    imprimir_separador("6. COMPROBACION DE REGLAS INFRANQUEABLES Y EXCEPCIONES")

    # Regla 1 (Bloqueante): PROHIBIDO prestar a socios morosos con multas impagas
    print(f"[*] Intento de prestamo a socio moroso (Socio 3: {socio3.get_rut()}):")
    try:
        sistema.crear_prestamo(
            rut_socio=socio3.get_rut(),
            cods_materiales=["DVD-001"],
            usuario_atencion=bibliotecaria1
        )
    except SocioConMultaPendienteError as e:
        print(f"    [BLOQUEO EXITOSO REGLA 1] {e}")

    # Regla 2 (Bloqueante): PROHIBIDO prestar material que ya está en poder de otro socio
    print(f"\n[*] Intento de prestar material ya prestado ('LIB-001') a Socio 2:")
    try:
        sistema.crear_prestamo(
            rut_socio=socio2.get_rut(),
            cods_materiales=["LIB-001"],
            usuario_atencion=bibliotecaria1
        )
    except MaterialYaPrestadoError as e:
        print(f"    [BLOQUEO EXITOSO REGLA 2] {e}")

    # Regla 3 (Integridad): Validación estricta de RUT con algoritmo Módulo 11
    print(f"\n[*] Intento de registrar socio con RUT invalido ('12.345.678-9'):")
    try:
        sistema.inscribir_socio(
            rut="12.345.678-9",
            nombre_completo="Usuario RUT Malo",
            telefono="+56900000000",
            email="malo@correo.cl"
        )
    except RutInvalidoError as e:
        print(f"    [BLOQUEO EXITOSO REGLA 3] {e}")

    # Regla 4 (Segregación de Roles): Solo Administradora puede condonar multas o alterar catálogo
    print(f"\n[*] Intento de Bibliotecaria de condonar multas (Atribucion de Administradora):")
    try:
        sistema.condonar_multa_socio(
            usuario_admin=bibliotecaria1,
            rut_socio=socio3.get_rut(),
            motivo="Intento no autorizado"
        )
    except PermisoInsuficienteError as e:
        print(f"    [SEGREGACION EXITOSA REGLA 4] {e}")

    # -------------------------------------------------------------------------
    # 8. DEVOLUCIONES, CÁLCULO DE MULTAS Y CONDONACIÓN DE DEUDA
    # -------------------------------------------------------------------------
    imprimir_separador("7. DEVOLUCION, CALCULO DE MULTAS Y CONDONACION DE DEUDA")
    
    # 1. Devolución a tiempo de la Revista
    print(f"[*] Devolviendo Revista '{revista1.codigo}' de Prestamo N°{prestamo1.id_prestamo:04d}:")
    sistema.procesar_devolucion(
        id_prestamo=prestamo1.id_prestamo,
        cod_mat="REV-001",
        usuario_atencion=bibliotecaria1,
        fecha_devolucion=date.today()
    )
    print(f"    [OK] Revista devuelta y disponible en inventario: {not revista1.esta_prestado()}")

    # 2. Devolución con atraso simulado de 4 días en Libro ($500 CLP/día = $2,000 CLP de multa)
    fecha_con_atraso = det_libro.fecha_devolucion_esperada + timedelta(days=4)
    print(f"\n[*] Devolviendo Libro '{libro1.codigo}' con 4 dias de retraso simulado:")
    sistema.procesar_devolucion(
        id_prestamo=prestamo1.id_prestamo,
        cod_mat="LIB-001",
        usuario_atencion=bibliotecaria1,
        fecha_devolucion=fecha_con_atraso
    )
    print(f"    [MULTA GENERADA] Socio {socio1.get_rut()} acumulo: ${socio1.monto_multa_acumulada:,.0f} CLP")

    # 3. Condonación de multa por la Administradora
    print(f"\n[*] Administradora procede a condonar la multa del Socio 1 por motivo justificado:")
    sistema.condonar_multa_socio(
        usuario_admin=admin,
        rut_socio=socio1.get_rut(),
        motivo="Licencia medica acreditada"
    )
    print(f"    [OK] Saldo del socio tras condonacion: ${socio1.monto_multa_acumulada:,.0f} CLP | Habilitado: {socio1.puede_solicitar_prestamo()}")

    # -------------------------------------------------------------------------
    # 9. REPORTE DE EXTRAVÍO DE MATERIAL EXTRANJERO EN USD
    # -------------------------------------------------------------------------
    imprimir_separador("8. REPORTE DE EXTRAVIO DE MATERIAL EXTRANJERO EN USD")
    print(f"[*] Socio 2 ('{socio2.get_nombre()}') extravio el libro importado '{extranjero1.titulo}':")
    cargo_perdida = sistema.registrar_perdida_material(socio2.get_rut(), "EXT-001")
    print(f"    [CARGO APLICADO] ${cargo_perdida:,.0f} CLP (Precio: ${extranjero1.precio_usd} USD + 6% Aduana @ ${valor_dolar:,.2f} CLP/USD)")
    print(f"    [ESTADO SOCIO 2] Deuda: ${socio2.monto_multa_acumulada:,.0f} CLP | Puede pedir prestamos: {socio2.puede_solicitar_prestamo()}")

    # Pago formal en mesón de caja
    print(f"\n[*] Socio 2 paga ${cargo_perdida + 5000:,.0f} CLP en efectivo:")
    vuelto = sistema.pagar_multa_socio(socio2.get_rut(), cargo_perdida + 5000)
    print(f"    [PAGO REGISTRADO] Deuda actual: ${socio2.monto_multa_acumulada:,.0f} CLP | Vuelto entregado: ${vuelto:,.0f} CLP")

    # -------------------------------------------------------------------------
    # 10. INSPECCIÓN DE PERSISTENCIA EN SQLITE Y BITÁCORA DE AUDITORÍA
    # -------------------------------------------------------------------------
    imprimir_separador("9. PERSISTENCIA EN BD SQLITE & BITACORA DE AUDITORIA")
    repo = sistema.repositorio_bd
    
    socios_bd = repo.listar_socios()
    print(f"[BD] Total Socios persistidos: {len(socios_bd)}")
    for s in socios_bd:
        print(f"     - N°{s['numero_socio']:04d} | {s['nombre_completo']} ({s['rut']}) | Multa: ${s['monto_multa_acumulada']:,.0f}")

    materiales_bd = repo.listar_materiales()
    print(f"\n[BD] Total Materiales en catalogo: {len(materiales_bd)}")
    for m in materiales_bd:
        estado_mat = "Prestado" if m['prestado'] else "Disponible"
        print(f"     - {m['codigo']} [{m['tipo_material']}] '{m['titulo']}' - {estado_mat}")

    prestamos_bd = repo.listar_prestamos()
    print(f"\n[BD] Total Prestamos registrados: {len(prestamos_bd)}")
    for p in prestamos_bd:
        print(f"     - Prestamo N°{p['id_prestamo']:04d} [{p['estado']}] | Socio: {p['rut_socio']} | Items: {p['total_items']}")

    logs_bd = repo.obtener_logs_auditoria(limite=8)
    print(f"\n[BD] Ultimos registros de Auditoria (Total mostrados: {len(logs_bd)}):")
    for log in logs_bd:
        print(f"     [{log['fecha']}] [@{log['usuario']}] -> {log['accion']}")

    imprimir_separador("EJECUCION DEL SISTEMA BIBLIOTECA CORDILLERA FINALIZADA CON EXITO")


if __name__ == "__main__":
    main()
