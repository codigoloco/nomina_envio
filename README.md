# Gestión de Nómina — Envío de Pagos por Correo (arquitectura MVC)

App de escritorio en **Python + PyQt5**, organizada en **Modelo–Vista–Controlador**,
para:

1. Registrar empleados (cédula, nombre, teléfono, correo) en **SQLite**.
2. Leer un archivo **Excel** con la información de pagos.
3. Enviar automáticamente un **correo con el detalle del pago** a cada empleado.
4. Dejar un **log** de cada envío (exitoso o con error) en una tabla de historial.

## 1. Estructura del proyecto (MVC)

```
nomina_app_mvc/
├── main.py                        # Punto de entrada
├── requirements.txt
├── plantilla_pagos_ejemplo.xlsx   # Ejemplo de Excel de pagos
│
├── models/                        # === MODELO === (acceso puro a datos, SQLite)
│   ├── database.py                #   conexión + creación de tablas
│   ├── employee_model.py          #   CRUD tabla 'empleados'
│   └── envio_model.py             #   CRUD tabla 'envios' (logs)
│
├── views/                         # === VISTA === (solo interfaz PyQt, sin SQL)
│   ├── main_window.py             #   ventana principal (3 pestañas)
│   ├── employee_dialog.py         #   formulario alta/edición de empleado
│   └── settings_dialog.py         #   formulario configuración SMTP
│
├── controllers/                   # === CONTROLADOR === (lógica de negocio)
│   ├── employee_controller.py     #   mediador Vista <-> EmployeeModel
│   ├── payment_controller.py      #   mediador Vista <-> Excel/EnvioModel
│   ├── settings_controller.py     #   mediador Vista <-> QSettings (SMTP)
│   └── send_worker.py             #   QThread: orquesta el envío masivo
│
└── services/                      # Integraciones externas (no son "modelo" de datos propio)
    ├── excel_reader.py            #   lee y normaliza el Excel de pagos
    └── email_sender.py            #   arma y envía el correo (SMTP)
```

**Regla de dependencia (importante):**
`views/` **nunca** importa nada de `models/` directamente — todo pasa por
`controllers/`. Esto significa que:

- Puedes cambiar SQLite por PostgreSQL/MySQL modificando solo `models/`.
- Puedes cambiar PyQt5 por otra librería de GUI modificando solo `views/`,
  sin tocar la lógica de negocio ni el acceso a datos.
- Puedes probar la lógica de negocio (`controllers/`) con pruebas
  automatizadas sin levantar ninguna ventana.

```
Vista (PyQt)  --llama-->  Controlador  --usa-->  Modelo (SQLite)
                                        --usa-->  Servicio (Excel / SMTP)
```

## 2. Instalación

```bash
cd nomina_app_mvc
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Ejecutar la app

```bash
python main.py
```

Se crea automáticamente `nomina.db` (SQLite) en la raíz del proyecto,
con las tablas `empleados` y `envios`.

## 4. Configurar el correo (SMTP)

Menú **Configuración → Configurar correo SMTP**:

| Proveedor | Host                | Puerto | Seguridad   |
|-----------|---------------------|--------|-------------|
| Gmail     | smtp.gmail.com      | 587    | STARTTLS    |
| Gmail     | smtp.gmail.com      | 465    | SSL directo |
| Outlook   | smtp.office365.com  | 587    | STARTTLS    |

**Importante:** usa una **"contraseña de aplicación"**, nunca la
contraseña principal de la cuenta. Esto se guarda localmente con
`QSettings` (ver `controllers/settings_controller.py`); en producción
real considera cifrarlo o usar un gestor de secretos (`keyring`, variables
de entorno, etc.).

## 5. Pestaña "Empleados"

CRUD de empleados. La **cédula es única** y es la llave para hacer match
con el Excel de pagos. Nota: si un empleado ya tiene envíos en el
historial, no se puede eliminar (se protege la trazabilidad); el sistema
avisa con un mensaje si intentas hacerlo.

## 6. Pestaña "Procesar Pagos"

1. **"Seleccionar archivo Excel..."** → carga y previsualiza los pagos.
2. Ajusta el **asunto** si quieres (`{periodo}` y `{nombre}` como variables).
3. **"Enviar correos"** → corre en un hilo aparte (`SendWorker`), con
   barra de progreso, log en vivo y botón para **detener**.
4. Al terminar, resumen de exitosos/errores.

### Formato del Excel

Incluido: `plantilla_pagos_ejemplo.xlsx`. Única columna **obligatoria**:
`cedula`. El resto de columnas son libres (`periodo`, `salario_base`,
`horas_extra`, `deducciones`, `neto_a_pagar`, etc.) — se arman
automáticamente como tabla de detalle en el cuerpo del correo.

Si una cédula del Excel no existe en `empleados`, esa fila queda como
`ERROR` en el historial y el proceso continúa con las demás.

## 7. Pestaña "Historial de Envíos"

Cada envío queda registrado con: fecha, cédula, nombre, correo, periodo,
monto, asunto, **estado** (`ENVIADO`/`ERROR`, en rojo) y **detalle** (el
mensaje exacto de error del servidor SMTP si algo falló). Se puede
filtrar por estado o buscar por cédula/nombre/correo.

## 8. Extender el proyecto

Gracias a la separación MVC, algunas mejoras típicas y dónde irían:

| Mejora                                          | Dónde se implementa               |
|--------------------------------------------------|------------------------------------|
| Cambiar SQLite por PostgreSQL                    | `models/database.py`               |
| Adjuntar PDF del volante de pago                 | `services/email_sender.py`         |
| Exportar historial a Excel                       | nuevo método en `payment_controller.py` + `services/` |
| Reintentos automáticos ante fallos de red         | `controllers/send_worker.py`       |
| Nueva pantalla (ej. reportes)                    | nuevo archivo en `views/` + controlador propio |
| Cifrar contraseña SMTP con `keyring`             | `controllers/settings_controller.py` |

## 9. Empaquetado como ejecutable (opcional)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name NominaApp main.py
```
