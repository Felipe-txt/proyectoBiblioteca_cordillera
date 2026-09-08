# 📚 Sistema de Gestión Biblioteca Municipal Cordillera (POO Python)

Sistema integral desarrollado bajo el paradigma de **Programación Orientada a Objetos (POO)** en Python y estructurado como paquete para **Visual Studio Code**, basado en el diseño UML del diagrama `Biblioteca_cordillera.drawio`.

---

## 🏛️ Arquitectura del Sistema y Relaciones UML

### 1. Dominio de Personas y Seguridad
- **`Persona` (Clase Base Abstracta)**: Encapsula RUT, nombre completo, teléfono y email. Valida el formato y dígito verificador del RUT chileno mediante el algoritmo **Módulo 11**.
- **`Socio`**: Administra la membresía, estado de morosidad, multas acumuladas y elegibilidad para préstamos.
- **`Usuario` (Clase Base Abstracta)**: Gestiona credenciales de acceso con contraseñas seguras hasheadas en **SHA-256** y matriz de control de permisos.
- **`BibliotecariaAtencion`**: Encargada de registrar préstamos múltiples, procesar devoluciones y autorizar renovaciones de plazo.
- **`Administradora`**: Rol con privilegios máximos (`SUPERADMIN`) para dar de alta/baja materiales del catálogo y autorizar condonación de multas.

### 2. Dominio de Materiales (Polimorfismo) y API Dólar
- **`Material` (Clase Base Abstracta)**: Define la interfaz polimórfica para duración de préstamos y políticas de extensión.
  - **`Libro`**: Préstamo estándar de **14 días** | Admite hasta **1 renovación**.
  - **`Revista`**: Préstamo de **7 días** | **0 renovaciones** (No renovable).
  - **`MaterialMultimedia` (DVD/CD/Blu-ray)**: Préstamo de **3 días** | **0 renovaciones** (Alta rotación).
  - **`MaterialExtranjero`**: Ítems importados cotizados en **USD**, calculando el costo de reposición con un recargo aduanero del **6%** y cotización en tiempo real mediante **`ServicioDolarAPI`** (`mindicador.cl`).

### 3. Transacción de Préstamos (Cabecera & Detalle)
- **`Prestamo`**: Cabecera transaccional que relaciona al `Socio`, a la `BibliotecariaAtencion` y contiene una lista de líneas de detalle.
- **`DetallePrestamo`**: Registra individualmente cada ítem prestado, su fecha límite de devolución, renovaciones utilizadas y cálculo de multas diarias por atraso ($500 CLP/día).

### 4. Controlador y Persistencia Relacional
- **`SistemaBiblioteca` (Fachada / Façade)**: Controlador central que orquesta las reglas de negocio, coordinando socios, catálogo, préstamos y usuarios.
- **`RepositorioBibliotecaBD`**: Persistencia relacional en **SQLite (`biblioteca_cordillera.db`)** para tablas de socios, usuarios, catálogo, préstamos, detalles y bitácora de auditoría.

---

## 🚫 Reglas Infranqueables del Negocio

1. **Bloqueo por Multa Pendiente**: Prohibido cursar préstamos a socios que mantengan deudas o multas pendientes.
2. **Disponibilidad de Material**: Prohibido prestar cualquier material que ya se encuentre en préstamo.
3. **Validación de RUT**: Todos los socios y personal deben registrar un RUT chileno válido verificado por Módulo 11.
4. **Segregación de Funciones**: Únicamente el usuario con rol `Administradora` puede modificar el catálogo y condonar deudas.

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
