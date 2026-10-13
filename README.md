# 📚 Sistema de Gestión - Biblioteca Municipal Cordillera

Proyecto desarrollado para la asignatura **Programación Orientada a Objeto Seguro (TI3V21)** - **Evaluación Sumativa N°3**.

---

## 1. Integrantes y Negocio

- **Integrantes**:
  - **César Palma**
  - **Mattias Ubilla**
- **Sección**: 114-2B-F1
- **Carrera**: Ingeniería Informática
- **Sede**: Puente Alto, INACAP
- **Docente**: Michael Arjel
- **Negocio Asignado**: **Biblioteca Municipal Cordillera**

### Descripción del Negocio
Sistema integral de gestión bibliotecaria bajo el paradigma de **Programación Orientada a Objetos Segura (POO)** en Python. Permite administrar el catálogo de recursos bibliográficos (Libros, Revistas periódicas, DVDs/Multimedia y Obras Extranjeras en USD), inscripción de socios con validación chilena, control de morosidad, transacciones de préstamos compuestas por múltiples líneas de detalle, facturación/órdenes de trabajo técnico y cotización de divisas en tiempo real.

---

## 2. Cómo Instalar y Ejecutar el Programa (Paso a Paso)

Para ejecutar este sistema en cualquier computador que solo posea **Python 3.10 o superior**, siga estas instrucciones:

### Paso 1: Clonar o descargar el repositorio
Clone el repositorio público desde GitHub o descargue el archivo comprimido y extraiga su contenido:
```bash
git clone <URL_DEL_REPOSITORIO_GITHUB>
cd "Biblioteca Cordillera"
```

### Paso 2: Instalar las dependencias oficiales
El proyecto consume la API económica oficial mediante la librería oficial `requests`:
```bash
pip install -r requirements.txt
```

### Paso 3: Ejecutar el programa interactivo (Backend)
Inicie el menú principal ejecutando:
```bash
python main.py
```
*El sistema creará e inicializará automáticamente todas las tablas relacionales SQLite (`biblioteca_cordillera.db`) y sembrará los registros iniciales si la base de datos es nueva.*

### Paso 4: Ejecutar la suite de pruebas automatizadas
Para comprobar el cumplimiento estricto de las reglas del negocio, validaciones y polimorfismo:
```bash
python test_biblioteca.py
python test_backend.py
```

---

## 3. Decisiones de Seguridad

### A. Prevención Rigurosa de Inyección SQL (SQL Injection)
- **Cero concatenación de cadenas**: Ninguna consulta SQL (`INSERT`, `SELECT`, `UPDATE`, `DELETE`) en el sistema concatena ni interpola texto ingresado por el usuario con operadores como `+` o `f-strings`.
- **Consultas 100% Parametrizadas**: Todas las operaciones hacia SQLite emplean marcadores de posición posicionales (`?`) a través del protocolo del DB-API de Python (`cursor.execute(sql, (param1, param2, ...))`). Esto garantiza que los valores ingresados por el usuario sean tratados exclusivamente como datos atómicos por el motor de base de datos y nunca como código SQL ejecutable.
- **Arquitectura de Persistencia DAO (Data Access Object)**:
  - La capa `dao/` está completamente aislada de la capa `model/` (sin lógica de acceso a datos dentro de las clases de negocio).
  - Implementación del patrón jerárquico **Table-per-type**: la tabla base `materiales` se vincula mediante Claves Primarias y Foráneas con restricción referencial activa (`PRAGMA foreign_keys = ON;`) hacia sus tablas hijas `libros`, `revistas`, `multimedia` y `extranjeros`.
  - La transacción de préstamo se almacena de forma íntegra uniendo la cabecera transaccional (`prestamos`) con sus líneas dependientes (`detalles_prestamo`).

### B. Validación de Entradas en Setters y Reglas Infranqueables
1. **Validación de Identidad Chilena en el Setter de la Clase (`Persona` / `Socio`)**:
   - El atributo `_rut` se valida y formatea en el `@rut.setter` de la clase abstracta `Persona` mediante el algoritmo matemático de comprobación **Módulo 11** (calculando sumatoria con serie ponderada 2 a 7).
   - Si se ingresa un RUT con formato corrupto o dígito verificador falso (ejemplo: `12.345.678-9`), el setter dispara inmediatamente una excepción específica `RutInvalidoError`, la cual es capturada en la interfaz rechazando la entrada con un mensaje claro y manteniendo el sistema en ejecución sin caídas.
2. **Validación de Tipos y Rangos Numéricos (Anti-Crash)**:
   - Los campos cuantitativos (precios de reposición, años de publicación, duraciones) se filtran con funciones controladas que interceptan `ValueError`. Si se ingresan caracteres alfanuméricos donde se espera un valor monetario (ejemplo: `abc`), se informa al usuario y el sistema se recupera de inmediato.
3. **Regla de Bloqueo por Morosidad**:
   - `Socio.puede_solicitar_prestamo()` verifica que el socio esté activo y con `monto_multa_acumulada == 0.0`. Si un usuario moroso intenta pedir un libro, `SistemaBiblioteca.crear_prestamo()` lanza `SocioConMultaPendienteError` impidiendo la creación del registro.
4. **Regla de Disponibilidad Física de Inventario**:
   - Un material con `prestado == True` no puede ser prestado a otro socio simultáneamente. Si se intenta prestar, se lanza `MaterialYaPrestadoError`.
5. **Autenticación y Credenciales Criptográficas**:
   - Las contraseñas del personal se almacenan hasheadas de manera irreversible en **SHA-256** (`hashlib.sha256`), evitando el almacenamiento de claves en texto plano.

---

## 4. Uso de Inteligencia Artificial

Durante el desarrollo de la solución se utilizó asistencia de Inteligencia Artificial. A continuación se documentan decisiones técnicas concretas respecto a recomendaciones de la IA:

### Caso 1: Mecanismo de Consumo de API Externa y Resiliencia de Red (MODIFICADO Y AJUSTADO)
- **Código sugerido inicialmente por la IA**:
  La IA sugirió una función genérica basada en la librería estándar `urllib.request` con un bloque de captura silencioso:
  ```python
  # Sugerencia inicial de la IA
  try:
      response = urllib.request.urlopen("https://mindicador.cl/api/dolar")
      data = json.loads(response.read().decode())
      return data["dolar"]["valor"]
  except Exception:
      return 950.0  # Silencioso, oculta cualquier fallo
  ```
- **Decisión Técnica Adoptada (Modificación)**:
  Se descartó el uso de `urllib` y la captura genérica silenciosa. En su lugar:
  1. Se implementó la librería oficial `requests` conforme a los requerimientos de la asignatura.
  2. Se configuró un **tiempo máximo de espera explícito (`timeout=5`)**.
  3. Se desagregaron las excepciones de red (`requests.exceptions.Timeout`, `requests.exceptions.ConnectionError`, `requests.exceptions.HTTPError`) para emitir una alerta explícita en pantalla informando la contingencia al operador (cumpliendo con la prueba sin internet P17) antes de activar el valor de contingencia de respaldo, garantizando transparencia operativa y resiliencia.

### Caso 2: Persistencia Plana vs. Patrón DAO con Herencia Table-per-Type (DESCARTADO Y REESTRUCTURADO)
- **Código sugerido inicialmente por la IA**:
  La IA sugirió almacenar todo el catálogo en una única tabla SQLite con múltiples columnas opcionales en blanco (`NULL`), o simplemente volcar la información a un archivo plano `JSON` al momento de operar.
- **Decisión Técnica Adoptada (Descartado y Refactorizado)**:
  Se descartó la persistencia plana o el modelo monolítico debido a que vulneraba los principios de normalización relacional y el patrón DAO solicitado en la rúbrica. Se diseñó la estructura de persistencia orientada a objetos:
  - DAO base `MaterialDao` para atributos universales (`codigo`, `titulo`, `autor_o_creador`, `anio_publicacion`, `precio_base_reposicion`, `prestado`).
  - DAOs específicos por herencia (`LibroDao`, `RevistaDao`, `MultimediaDao`, `ExtranjeroDao`) que gestionan tablas relacionales hijas vinculadas por `FOREIGN KEY` con `ON DELETE CASCADE`, garantizando integridad referencial y polimorfismo completo.

---

## 📋 Guion de Pruebas: Tabla de Cobertura y Verificación

| N° | Prueba | Procedimiento en el Sistema | Resultado Obtenido |
|:--:|:---|:---|:---:|
| **P01** | **El programa se ejecuta** | Ejecutar `python main.py` habiendo instalado `requirements.txt`. | **Cumple** (Muestra menú principal) |
| **P02** | **Crear: material** | Opción [1]: Libro "Rayuela", valor $15.000. | **Cumple** (Confirma guardado en SQLite) |
| **P03** | **Listar: material** | Opción [2]: Listado general del catálogo. | **Cumple** (Aparece "Rayuela") |
| **P04** | **Modificar: material** | Opción [3]: Cambiar título a "Rayuela (ed. 2020)". | **Cumple** (Actualiza en BD y muestra cambio) |
| **P05** | **Los datos quedan guardados** | Salir [0], volver a abrir `python main.py` y listar [2]. | **Cumple** (El registro modificado sigue ahí) |
| **P06** | **Eliminar: material** | Opción [4]: Eliminar "Rayuela" y listar. | **Cumple** (Se elimina de SQLite y no aparece) |
| **P07** | **RUT correcto** | Opción [6]: Inscribir socio con RUT `12.345.678-5`. | **Cumple** (Validado por setter y aceptado) |
| **P08** | **RUT incorrecto (DV falso)** | Opción [6]: Inscribir socio con RUT `12.345.678-9`. | **Cumple** (Rechazado con mensaje amigable sin caerse) |
| **P09** | **Tipo Libro** | Opción [5]: Políticas Libro. | **Cumple** (14 días de préstamo; renovable 1 vez) |
| **P10** | **Tipo Revista** | Opción [5]: Políticas Revista. | **Cumple** (7 días de préstamo; no renovable) |
| **P11** | **Tipo DVD / multimedia** | Opción [5]: Políticas DVD. | **Cumple** (3 días de préstamo; no renovable) |
| **P12** | **Registrar: préstamo múltiple**| Opción [9]: Socio solicita 2 libros y 1 revista. | **Cumple** (Un solo préstamo con 3 líneas) |
| **P13** | **Ver detalle: préstamo** | Opción [10]: Consultar préstamo creado en P12. | **Cumple** (Se visualizan todas sus líneas de detalle) |
| **P14** | **Regla: Socio con multa** | Opción [7] poner multa impaga y luego Opción [9]. | **Cumple** (Préstamo impedido sin caerse) |
| **P15** | **Regla: Material ya prestado** | Prestar ejemplar a Socio A; intentar prestar a Socio B. | **Cumple** (Segundo préstamo bloqueado sin caerse) |
| **P16** | **Dólar API en vivo** | Opción [12]: Calcular libro USD 20 x dólar hoy. | **Cumple** (Usa cotización real de mindicador.cl) |
| **P17** | **Sin internet (Resiliencia)** | Desconectar conexión y calcular precio en Opción [12]. | **Cumple** (Avisa desconexión y usa contingencia sin caerse) |
| **P18** | **Opción menú inexistente** | Ingresar opción `99` en el menú. | **Cumple** (Mensaje de aviso y vuelve al menú) |
| **P19** | **Letras donde va número** | En valor de reposición de Opción [1] escribir `abc`. | **Cumple** (Avisa amigablemente y no se cae) |
