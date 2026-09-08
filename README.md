# 📚 Sistema de Gestión Biblioteca Municipal Cordillera (POO Python)

Sistema integral desarrollado bajo el paradigma de **Programación Orientada a Objetos (POO)** en Python y estructurado como paquete para **Visual Studio Code**, basado en el diseño UML del diagrama `Biblioteca_cordillera.drawio`.

---

## 🏛️ Arquitectura del Sistema y Relaciones UML

### 1. Dominio de Personas y Seguridad
- **`persona.py` (`Persona` - Clase Base Abstracta)**: Encapsula RUT, nombre completo, teléfono y email. Valida el formato y dígito verificador del RUT chileno mediante el algoritmo **Módulo 11**. Si el RUT no es matemáticamente válido, dispara `RutInvalidoError`.
- **`socio.py` (`Socio`)**: Administra la membresía, estado de morosidad, saldo acumulado y elegibilidad para préstamos (`puede_solicitar_prestamo()`).
- **`usuario.py` (`Usuario` - Clase Base Abstracta)**: Gestiona credenciales de acceso con contraseñas seguras hasheadas en **SHA-256** y matriz de control de permisos (RBAC).
- **`bibliotecaria_atencion.py` (`BibliotecariaAtencion`)**: Encargada de registrar préstamos múltiples, procesar devoluciones y autorizar renovaciones de plazo.
- **`administradora.py` (`Administradora`)**: Rol con privilegios máximos (`SUPERADMIN`) para dar de alta/baja materiales del catálogo y autorizar condonación de multas.

### 2. Dominio de Materiales (Polimorfismo) y API Dólar
- **`material.py` (`Material` - Clase Base Abstracta)**: Define la interfaz polimórfica para duración de préstamos y políticas de extensión. Protege la disponibilidad física con el método `prestar()`, lanzando `MaterialYaPrestadoError` si el ejemplar ya está prestado.
  - **`libro.py` (`Libro`)**: Préstamo estándar de **14 días** | Admite hasta **1 renovación**.
  - **`revista.py` (`Revista`)**: Préstamo de **7 días** | **0 renovaciones** (No renovable).
  - **`material_multimedia.py` (`MaterialMultimedia`)**: Préstamo de **3 días** | **0 renovaciones** (Alta rotación).
  - **`material_extranjero.py` (`MaterialExtranjero`)**: Ítems importados cotizados en **USD**, calculando el costo de reposición con un recargo aduanero del **6%** y cotización en tiempo real mediante **`ServicioDolarAPI`** (`mindicador.cl`).

### 3. Transacción de Préstamos (Cabecera & Detalle)
- **`prestamo.py` (`Prestamo`)**: Cabecera transaccional que relaciona al `Socio`, a la `BibliotecariaAtencion` y contiene una lista de líneas de detalle.
- **`detalle_prestamo.py` (`DetallePrestamo`)**: Registra individualmente cada ítem prestado, su fecha límite de devolución, renovaciones utilizadas y cálculo de multas diarias por atraso ($500 CLP/día). Lanza `RenovacionNoPermitidaError` si se intenta prorrogar un ítem no renovable o que excedió su tope.

### 4. Controlador y Persistencia Relacional
- **`sistema_biblioteca.py` (`SistemaBiblioteca` - Fachada / Façade)**: Controlador central que orquesta las reglas de negocio, coordinando socios, catálogo, préstamos y usuarios.
- **`repositorio_bd.py` (`RepositorioBibliotecaBD`)**: Persistencia relacional en **SQLite (`biblioteca_cordillera.db`)** para tablas de socios, usuarios, catálogo, préstamos, detalles y bitácora de auditoría.
- **`servicio_dolar.py` (`ServicioDolarAPI`)**: Cliente HTTP REST con fallback resiliente y caché local para cotización de divisas.

---

## ⚠️ Jerarquía y Explicación de Excepciones del Dominio (`excepciones.py`)

El proyecto implementa una jerarquía propia de excepciones para blindar las **Reglas Infranqueables del Negocio**:

```text
BibliotecaError (Excepción Base)
├── SocioConMultaPendienteError   # Bloqueo: Socio con deudas o sanciones impagas
├── MaterialYaPrestadoError       # Bloqueo: Ejemplar ya en préstamo a otro socio
├── RenovacionNoPermitidaError    # Infracción: Prórroga no admitida o cupo excedido
├── RutInvalidoError              # Validación: Dígito verificador o RUT inválido (Módulo 11)
├── PermisoInsuficienteError      # Seguridad: Usuario sin privilegios de rol (RBAC)
├── MaterialNoEncontradoError     # Búsqueda: Código de material inexistente
├── SocioNoEncontradoError        # Búsqueda: RUT de socio no registrado
└── PrestamoNoEncontradoError     # Búsqueda: ID de transacción inexistente
```

### Detalle de las Excepciones Principales:
1. **`SocioConMultaPendienteError`**:
   - *¿Por qué existe?*: Protege el patrimonio de la biblioteca evitando entregar más libros a usuarios con saldo deudor o sanciones pendientes.
   - *¿Dónde se valida?*: En `Socio.puede_solicitar_prestamo()` y `SistemaBiblioteca.crear_prestamo()`.
2. **`MaterialYaPrestadoError`**:
   - *¿Por qué existe?*: Impide inconsistencias físicas de inventario (un libro no puede estar en manos de dos lectores a la vez).
   - *¿Dónde se valida?*: En `Material.prestar()` y al armar un `Prestamo`.
3. **`RenovacionNoPermitidaError`**:
   - *¿Por qué existe?*: Hace cumplir las políticas de rotación de la biblioteca (revistas y DVDs no se renuevan; libros solo 1 vez).
   - *¿Dónde se valida?*: En `DetallePrestamo.renovar()`.
4. **`RutInvalidoError`**:
   - *¿Por qué existe?*: Asegura la veracidad de la identidad chilena mediante la fórmula del Módulo 11.
   - *¿Dónde se valida?*: En el constructor de `Persona`.
5. **`PermisoInsuficienteError`**:
   - *¿Por qué existe?*: Aplica el principio de mínimo privilegio; solo la Administradora puede alterar el catálogo o condonar multas.
   - *¿Dónde se valida?*: En `Administradora.dar_alta_material()`, `condonar_multa()`, etc.

---

## 🚀 Instrucciones de Ejecución

### Opción A: Ejecutar la Demostración Principal
```bash
python main.py
```

### Opción B: Ejecutar la Suite de Pruebas Unitarias
```bash
python test_biblioteca.py
```

### Opción C: Desde Visual Studio Code
- Abre la carpeta `Biblioteca Cordillera` en VS Code.
- Presiona `F5` o ve al menú de **Run & Debug** y selecciona:
  - `Python: Ejecutar Main (Biblioteca Cordillera)`
  - `Python: Ejecutar Tests Unitarios`
