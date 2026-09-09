---
name: excel-2021-skill-matrix
description: Matriz de habilidades y evaluación para Excel 2021 y Microsoft 365. Utiliza este skill para evaluar competencias de usuarios, diseñar pruebas técnicas, o estructurar planes de formación en Excel moderno (Matrices Dinámicas, Power Query, LAMBDA).
---

# Matriz de Habilidades: Excel 2021 y Microsoft 365

Esta matriz abandona el enfoque de versiones antiguas y pone el peso principal en las herramientas modernas: **Matrices Dinámicas, Power Query, XLOOKUP, y automatización contemporánea**.

## Instrucciones de uso para el Agente
1. Al evaluar el nivel de un usuario, clasifícalo en uno de los 4 niveles detallados a continuación.
2. Si se solicita crear una prueba técnica o de selección, basa los ejercicios en los "Indicadores de Logro" de los Niveles 2 y 3.
3. Prioriza siempre el uso de herramientas modernas (ej. `BUSCARX` sobre `BUSCARV`, Matrices Dinámicas sobre arrastre manual de fórmulas).

---

## Nivel 1: Fundamentos Operativos (Básico)
*El objetivo de este nivel es la autonomía para la entrada, limpieza básica y presentación de datos sin alterar la integridad del archivo.*

| Categoría | Habilidades Específicas | Indicador de Logro |
| :--- | :--- | :--- |
| **Navegación e Interfaz** | Uso de atajos de teclado esenciales, gestión de hojas y ventanas, vistas de impresión. | Se desplaza y formatea documentos para impresión sin usar el ratón constantemente. |
| **Gestión de Datos** | Tipos de datos, formatos de número/fecha, validación de datos simple (listas desplegables). | Introduce datos sin errores de formato (ej. fechas que no se reconocen como texto). |
| **Fórmulas Básicas** | Operadores aritméticos, referencias relativas y absolutas (`$A$1`), funciones agregadas (`SUMA`, `PROMEDIO`, `MIN`, `MAX`, `CONTAR`). | Construye cálculos básicos y arrastra fórmulas sin romper las referencias. |
| **Visualización Base** | Formato condicional básico (escalas de color, barras de datos), creación de gráficos de barras y líneas simples. | Destaca visualmente los valores atípicos de una tabla en menos de un minuto. |

## Nivel 2: Lógica y Gestión de Tablas (Intermedio)
*El usuario pasa de ser un "capturista" a un gestor de información capaz de cruzar bases de datos y resumir grandes volúmenes de información.*

| Categoría | Habilidades Específicas | Indicador de Logro |
| :--- | :--- | :--- |
| **Lógica y Condicionales** | Funciones lógicas (`SI`, `Y`, `O`), condicionales anidadas, `SUMAR.SI.CONJUNTO`, `CONTAR.SI.CONJUNTO`. | Segmenta y suma datos en base a 2 o más criterios simultáneos. |
| **Búsqueda Moderna** | Uso de **`BUSCARX` (XLOOKUP)** (reemplazo absoluto de BUSCARV/H e INDICE/COINCIDIR), manejo de errores (`SI.ERROR`, `ND`). | Cruza tablas de izquierda a derecha sin errores estructurales y maneja los datos no encontrados. |
| **Limpieza de Texto** | `EXTRAE`, `TEXTO`, `IZQUIERDA`, `DERECHA`, `ENCONTRAR`, `UNIRCADENAS`. | Extrae códigos específicos o nombres desde cadenas de texto sucias. |
| **Tablas Dinámicas I** | Creación de Tablas Dinámicas, campos calculados simples, segmentación de datos (Slicers) y gráficos dinámicos. | Genera un reporte interactivo con filtros a partir de una tabla de datos plana. |

## Nivel 3: Matrices Dinámicas y Análisis (Avanzado - Exclusivo 2021+)
*Este nivel separa a los usuarios tradicionales de los usuarios modernos. Se enfoca en el "Spill Behavior" (Rango de Desbordamiento) y la ingesta de datos.*

| Categoría | Habilidades Específicas | Indicador de Logro |
| :--- | :--- | :--- |
| **Matrices Dinámicas** | `FILTRAR`, `ORDENAR`, `ORDENARPOR`, `UNICOS`, `SECUENCIA`, operando con el símbolo `#` para rangos desbordados. | Construye reportes que se actualizan y cambian de tamaño automáticamente sin usar Macros. |
| **Optimización de Fórmulas** | Uso de la función **`LET`** para declarar variables dentro de la fórmula y evitar recálculos redundantes. | Reduce fórmulas de 5 líneas a 2 líneas limpias, mejorando el rendimiento del archivo. |
| **ETL con Power Query** | Importar datos desde CSV/Web/Carpetas, transformar columnas (Unpivot, Split, Merge), cargar al Modelo de Datos. | Automatiza la limpieza mensual de un reporte descargado del ERP con un solo clic en "Actualizar". |
| **Tablas Dinámicas II** | Conexión de múltiples tablas mediante relaciones (Data Model) en lugar de usar BUSCARX repetitivamente. | Cruza 3 tablas masivas sin que el rendimiento de Excel colapse. |

## Nivel 4: Modelado de Datos y Automatización (Experto)
*Diseñado para perfiles analíticos (Data Analysts, Financial Modelers) que utilizan Excel como un motor de desarrollo o modelado avanzado.*

| Categoría | Habilidades Específicas | Indicador de Logro |
| :--- | :--- | :--- |
| **Fórmulas Personalizadas** | Uso de **`LAMBDA`** para crear funciones personalizadas reutilizables en el administrador de nombres. | Crea una función propia (ej. `=CALCULAR_ROI()`) que el equipo puede usar sin saber la fórmula real. |
| **Modelado con DAX (Power Pivot)** | Medidas DAX avanzadas (`CALCULATE`, `FILTER`, `TIME INTELLIGENCE`), KPIs personalizados, contextos de evaluación. | Construye un modelo relacional que analiza ventas Year-over-Year (YoY) dinámicamente. |
| **Automatización Moderna** | **Office Scripts (TypeScript)** para web y escritorio (el sucesor natural de VBA), integración con Power Automate. | Crea un script que formatea el documento y envía automáticamente un correo con el Excel adjunto a través de Power Automate. |
| **Macros y VBA (Legacy)** | Programación orientada a objetos en VBA, bucles (`For`, `Do While`), UserForms, eventos de hoja/libro. | Automatiza procesos heredados locales que interactúan con el sistema de archivos de Windows. |
