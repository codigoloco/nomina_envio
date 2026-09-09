"""
Servicio: lectura de archivos Excel y Google Sheets (incluyendo Tablas Dinámicas y Múltiples Cuadros).
Soporta la lectura unificada del Cuadro 1 (Trabajadores con cédula) y Cuadro 2 (Encargados especiales sin cédula -> 'N/A').
Rango: A1:N(última fila con datos). No modifica ningún archivo; solo lectura.
"""

import io
import unicodedata
import pandas as pd

# Mapa de columnas exactas A1:N1 -> nombre interno estandarizado
ENCARGADOS_COLUMN_MAP = {
    "encargado": "nombre",
    "nombre_del_encargado": "nombre",
    "nombre_encargado": "nombre",
    "nombre": "nombre",
    "cedula": "cedula",
    "tienda": "unidad_administrativa",
    "unidad_administrativa": "unidad_administrativa",
    "mes": "periodo",
    "total_venta": "TOTAL VENTA",
    "gastos_deducibles": "Gastos deducibles",
    "total_gastos_deducibles": "Gastos deducibles",
    "neto_(ventas_-_gastos)": "Neto (Ventas - Gastos)",
    "%_comision": "% Comision",
    "%_comision_encargado": "% Comision",
    "comision": "% Comision",
    "comision_encargado": "Comision encargado",
    "monto_comision_encargado": "Comision encargado",
    "sueldo": "Sueldo",
    "sueldo_encargado": "Sueldo",
    "bonificacion": "Bonificacion",
    "bonificacion_mensual": "Bonificacion",
    "vales": "Vales",
    "pagos_realizados": "Pagos realizados",
    "neto_a_pagar": "Neto a pagar"
}

NOMBRES_COLUMNAS_POSICIONALES = [
    "nombre",                  # A: Encargado
    "cedula",                  # B: Cédula
    "unidad_administrativa",   # C: Tienda
    "periodo",                 # D: Mes
    "TOTAL VENTA",             # E: TOTAL VENTA
    "Gastos deducibles",       # F: Gastos deducibles
    "Neto (Ventas - Gastos)",  # G: Neto (Ventas - Gastos)
    "% Comision",              # H: % Comisión
    "Comision encargado",      # I: Comisión encargado
    "Sueldo",                  # J: Sueldo
    "Bonificacion",            # K: Bonificación
    "Vales",                   # L: Vales
    "Pagos realizados",        # M: Pagos realizados
    "Neto a pagar"             # N: Neto a pagar
]

HOJA_PAGOS_ENCARGADOS = "Pagos a encargados"
HOJA_EXCEL_PAGO_RESUMEN = "Pago Encargados Resumen"
TOTALIZADORES_EXACTOS = {"suma_total", "total_general", "grand_total", "totales", "resultado_general", "suma_totales"}
ALIAS_CEDULA = {"cedula", "ci", "c_i", "cedula_de_identidad", "nro_cedula", "numero_cedula", "documento"}

MESES_MAP = {
    "ene": "enero",
    "feb": "febrero",
    "mar": "marzo",
    "abr": "abril",
    "may": "mayo",
    "jun": "junio",
    "jul": "julio",
    "ago": "agosto",
    "sept": "septiembre",
    "sep": "septiembre",
    "oct": "octubre",
    "nov": "noviembre",
    "dic": "diciembre"
}


def normalizar_columna(col) -> str:
    """
    Normaliza el nombre de una columna: convierte a minúsculas, elimina tildes/acentos,
    recorta espacios y reemplaza espacios intermedios por guiones bajos.
    """
    texto = str(col).strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = texto.replace(" ", "_")
    return texto


def limpiar_cedula(val) -> str:
    """
    Limpia el número de cédula eliminando puntos, guiones, prefijos o ceros flotantes.
    Ej: "20.904.205" -> "20904205", "V-4181192.0" -> "4181192"
    """
    if not val or str(val).strip() in ("N/A", "nan", "None", ""):
        return "N/A"
    txt = str(val).strip()
    if txt.endswith(".0"):
        txt = txt[:-2]
    digitos = "".join(c for c in txt if c.isdigit())
    if digitos:
        return digitos
    res = txt.replace(".", "").replace(",", "").replace("-", "").replace(" ", "")
    return res if res else "N/A"


def es_totalizador(texto) -> bool:
    """Retorna True si el texto es un totalizador de cierre final (ej: 'Suma total')."""
    if not texto:
        return False
    norm = normalizar_columna(texto)
    if norm in ("total_venta", "ventas", "neto_a_pagar", "total", "neto_(ventas_-_gastos)"):
        return False
    return norm in TOTALIZADORES_EXACTOS or norm.startswith("suma_total") or norm.startswith("total_general")


class ExcelReader:

    @classmethod
    def extraer_periodo_de_slicer(cls, origen_excel) -> str:
        """
        Extrae el mes seleccionado en la segmentación de datos (Slicer)
        'FECHA (mes) 3' correspondiente a la hoja de resumen en el archivo Excel .xlsx.
        Acepta una ruta de archivo (str) o un búfer en memoria (io.BytesIO).
        """
        if isinstance(origen_excel, str) and not origen_excel.lower().endswith(".xlsx"):
            return ""

        import zipfile
        import xml.etree.ElementTree as ET

        try:
            if isinstance(origen_excel, io.BytesIO):
                origen_excel.seek(0)
            with zipfile.ZipFile(origen_excel, "r") as z:
                # 1. Localizar el identificador de cache del slicer 'FECHA (mes) 3'
                cache_target = None
                for name in z.namelist():
                    if "slicers/slicer" in name.lower():
                        root = ET.fromstring(z.read(name))
                        for item in root.iter():
                            s_name = normalizar_columna(item.attrib.get("name", ""))
                            if "fecha_(mes)_3" in s_name or "fecha__mes3" in s_name:
                                cache_target = normalizar_columna(item.attrib.get("cache", ""))
                                break
                        if cache_target:
                            break

                target_cache_norm = cache_target or "segmentaciondedatos_fecha__mes3"

                # 2. Buscar la selección activa en el archivo slicerCaches correspondiente
                for name in z.namelist():
                    if "slicercaches/" in name.lower():
                        root = ET.fromstring(z.read(name))
                        c_name = normalizar_columna(root.attrib.get("name", ""))
                        if c_name == target_cache_norm or "fecha__mes3" in c_name:
                            for sel in root.iter():
                                if sel.tag.endswith("selection"):
                                    val = sel.attrib.get("n", "")
                                    if "&[" in val:
                                        mes_raw = val.split("&[")[-1].rstrip("]").strip().lower()
                                        return MESES_MAP.get(mes_raw, mes_raw)

        except Exception:
            pass

        return ""

    @classmethod
    def _procesar_dataframe_pagos(cls, df: pd.DataFrame, periodo_defecto: str = "", omitir_pagos_realizados: bool = False) -> list:
        """
        Procesa la matriz de filas de pagos desde un DataFrame (origen CSV o Excel).
        Soporta Cuadro 1 (con cédula) y Cuadro 2 (sin cédula -> 'N/A').
        Formatea campos faltantes como 'N/A'.
        """
        from controllers.settings_controller import SettingsController

        filas_resultado = []
        mapa_columnas_actual = None
        tiene_cedula_en_bloque = False

        orden_prioritario = [
            "nombre", "cedula", "periodo", "unidad_administrativa",
            "% Comision", "Bonificacion", "Comision encargado", "Sueldo",
            "TOTAL VENTA", "Gastos deducibles", "Neto (Ventas - Gastos)",
            "Vales", "Pagos realizados", "Neto a pagar"
        ]

        if omitir_pagos_realizados:
            orden_prioritario = [col for col in orden_prioritario if col != "Pagos realizados"]

        for idx, row_vals in df.iterrows():
            vals = [str(v).strip() if v is not None and str(v).lower() != "nan" else "" for v in row_vals.values]
            if not any(vals):
                continue

            first_val = vals[0]
            norm_first = normalizar_columna(first_val)

            # Detectar fila de encabezados para un nuevo bloque/cuadro
            if norm_first in ("encargado", "nombre", "nombre_del_encargado", "nombre_encargado"):
                mapa_columnas_actual = []
                tiene_cedula_en_bloque = False
                for c_i, c_val in enumerate(vals):
                    c_norm = normalizar_columna(c_val)
                    if c_norm in ENCARGADOS_COLUMN_MAP:
                        col_mapped = ENCARGADOS_COLUMN_MAP[c_norm]
                    elif c_norm in ("encargado", "nombre", "nombre_encargado", "nombre_del_encargado"):
                        col_mapped = "nombre"
                    elif c_norm in ALIAS_CEDULA:
                        col_mapped = "cedula"
                    elif "tienda" in c_norm:
                        col_mapped = "unidad_administrativa"
                    elif c_norm in ("mes", "periodo"):
                        col_mapped = "periodo"
                    else:
                        col_mapped = c_val

                    # Si el encabezado está vacío en columnas financieras de cuadros sin nombre, asignar posicional
                    if (not col_mapped or col_mapped.lower() in ("nan", "none", "")) and c_i < len(NOMBRES_COLUMNAS_POSICIONALES):
                        # Solo asignar posicional si los primeros encabezados coinciden con el esquema estándar A-D
                        if len(mapa_columnas_actual) >= 2 and mapa_columnas_actual[0] == "nombre" and mapa_columnas_actual[1] == "cedula":
                            col_mapped = NOMBRES_COLUMNAS_POSICIONALES[c_i]

                    if col_mapped == "cedula":
                        tiene_cedula_en_bloque = True
                    mapa_columnas_actual.append(col_mapped)
                continue

            # Omitir filas de totales
            if es_totalizador(first_val) or any(es_totalizador(v) for v in vals[:3]):
                continue

            # Procesar fila de datos si tenemos un bloque activo
            if mapa_columnas_actual:
                raw_dict = {}
                for c_i, col_name in enumerate(mapa_columnas_actual):
                    if c_i < len(vals) and col_name:
                        raw_dict[col_name] = vals[c_i]

                nombre_val = str(raw_dict.get("nombre", "")).strip()
                if not nombre_val or nombre_val.lower() in ("encargado", "nombre", "n/a") or es_totalizador(nombre_val):
                    continue

                # Tratar Cédula: si el bloque no tiene columna de cédula o está vacía, asignar "N/A"
                if not tiene_cedula_en_bloque or not raw_dict.get("cedula"):
                    raw_dict["cedula"] = "N/A"
                else:
                    raw_dict["cedula"] = limpiar_cedula(raw_dict["cedula"])

                # Construir fila_ordenada en la secuencia estricta
                fila_ordenada = {}
                for col_key in orden_prioritario:
                    val_raw = raw_dict.get(col_key, "").strip()

                    # Calcular Neto (Ventas - Gastos) automáticamente si no está explícito en la hoja
                    if col_key == "Neto (Ventas - Gastos)" and (not val_raw or val_raw == "N/A"):
                        raw_v = raw_dict.get("TOTAL VENTA", "").replace(",", ".")
                        raw_g = raw_dict.get("Gastos deducibles", "").replace(",", ".")
                        try:
                            val_calc = float(raw_v) - float(raw_g)
                            val_raw = str(val_calc)
                        except Exception:
                            val_raw = ""

                    # Asignar período obtenido del Slicer si no viene en las celdas
                    if col_key == "periodo" and (not val_raw or val_raw == "N/A") and periodo_defecto:
                        val_raw = periodo_defecto

                    if not val_raw:
                        val_final = "N/A"
                    elif col_key == "cedula":
                        val_final = val_raw
                    elif col_key in ("nombre", "unidad_administrativa", "periodo", "telefono", "correo"):
                        val_final = val_raw if val_raw else "N/A"
                    else:
                        val_final = SettingsController.format_amount(val_raw) if val_raw != "N/A" else "N/A"

                    fila_ordenada[col_key] = val_final

                filas_resultado.append(fila_ordenada)

        return filas_resultado

    @classmethod
    def read_payments_from_csv(cls, path_csv):
        """
        Lee todos los cuadros de 'Pagos a encargados' desde un archivo CSV.
        Soporta Cuadro 1 (con cédula) y Cuadro 2 (sin cédula -> 'N/A').
        Formatea campos faltantes como 'N/A'.
        """
        with open(path_csv, "r", encoding="utf-8-sig", errors="replace") as f:
            df = pd.read_csv(f, header=None, dtype=str)
        df = df.fillna("")
        return cls._procesar_dataframe_pagos(df)

    @classmethod
    def read_payments(cls, path):
        """
        Método de lectura para archivos Excel (.xlsx, .xls) o CSV locales.
        Para archivos Excel busca la hoja 'Pago Encargados Resumen' y mantiene
        la misma estructura que los datos obtenidos de Google Drive.
        """
        ruta_str = str(path).lower()
        if ruta_str.endswith(".csv"):
            return cls.read_payments_from_csv(path)

        # Manejo de archivo Excel (.xlsx / .xls)
        # Leer el contenido completo a memoria de inmediato para liberar el archivo en disco o red
        with open(path, "rb") as f:
            contenido_bytes = io.BytesIO(f.read())

        # Extraer el período seleccionado en la segmentación de datos (slicer) si existe
        periodo_slicer = cls.extraer_periodo_de_slicer(contenido_bytes) if ruta_str.endswith(".xlsx") else ""

        contenido_bytes.seek(0)
        with pd.ExcelFile(contenido_bytes, engine="openpyxl" if ruta_str.endswith(".xlsx") else None) as excel_file:
            nombres_hojas = excel_file.sheet_names

            # Búsqueda de la hoja ignorando mayúsculas/minúsculas y tildes/espacios
            hoja_objetivo = None
            busqueda_normalizada = normalizar_columna(HOJA_EXCEL_PAGO_RESUMEN)

            for hoja in nombres_hojas:
                if normalizar_columna(hoja) == busqueda_normalizada:
                    hoja_objetivo = hoja
                    break

            # Búsqueda por palabras clave si no hubo coincidencia exacta normalizada
            if not hoja_objetivo:
                for hoja in nombres_hojas:
                    norm_h = normalizar_columna(hoja)
                    if "pago" in norm_h and "resumen" in norm_h:
                        hoja_objetivo = hoja
                        break

            # Si aún no coincide, usar la única hoja disponible o lanzar excepción clara
            if not hoja_objetivo:
                if len(nombres_hojas) == 1:
                    hoja_objetivo = nombres_hojas[0]
                else:
                    raise ValueError(
                        f"No se encontró la hoja '{HOJA_EXCEL_PAGO_RESUMEN}' en el archivo Excel.\n"
                        f"Hojas encontradas en el archivo: {', '.join(nombres_hojas)}"
                    )

            df = pd.read_excel(excel_file, sheet_name=hoja_objetivo, header=None, dtype=str)

        df = df.fillna("")
        return cls._procesar_dataframe_pagos(df, periodo_defecto=periodo_slicer, omitir_pagos_realizados=True)

    @classmethod
    def read_employees_template(cls, path):
        """
        Lee una plantilla de empleados generada por la aplicación y devuelve
        una lista de diccionarios. Valida la presencia de la columna 'cedula'.
        """
        ruta_str = str(path).lower()
        if ruta_str.endswith(".csv"):
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                df = pd.read_csv(f, header=0, dtype=str)
        else:
            with open(path, "rb") as f:
                contenido_bytes = io.BytesIO(f.read())
            with pd.ExcelFile(contenido_bytes, engine="openpyxl" if ruta_str.endswith(".xlsx") else None) as excel_file:
                df = pd.read_excel(excel_file, header=0, dtype=str)
        df.columns = [normalizar_columna(c) for c in df.columns]

        cedula_col = None
        for col in df.columns:
            if col in ALIAS_CEDULA:
                cedula_col = col
                break

        if not cedula_col:
            raise ValueError("La plantilla debe contener una columna llamada 'cedula'.")

        if cedula_col != "cedula":
            df = df.rename(columns={cedula_col: "cedula"})

        df = df.fillna("")
        filas = df.to_dict(orient="records")

        for fila in filas:
            fila["cedula"] = limpiar_cedula(fila.get("cedula", ""))

        return [f for f in filas if f.get("cedula") and f.get("cedula") != "N/A"]
