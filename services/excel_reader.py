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
    def extraer_periodo_de_slicer(cls, origen_excel, nombre_hoja: str = "") -> str:
        """
        Extrae el mes seleccionado en la segmentación de datos (Slicer)
        asociada a 'nombre_hoja', o de cualquier slicer de FECHA (mes) disponible.
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
                # 1. Intentar buscar el slicer específico de la hoja si se especificó nombre_hoja
                cache_target = None
                if nombre_hoja:
                    try:
                        wb_root = ET.fromstring(z.read("xl/workbook.xml"))
                        rid = None
                        sheet_norm = normalizar_columna(nombre_hoja)
                        for s in wb_root.iter():
                            if s.tag.endswith("sheet"):
                                n = normalizar_columna(s.attrib.get("name", ""))
                                if n == sheet_norm or sheet_norm in n:
                                    for k, v in s.attrib.items():
                                        if k.endswith("id"):
                                            rid = v
                                            break
                                    if rid:
                                        break

                        if rid and "xl/_rels/workbook.xml.rels" in z.namelist():
                            rels_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
                            target_sheet = None
                            for r in rels_root.iter():
                                if r.attrib.get("Id") == rid:
                                    target_sheet = r.attrib.get("Target", "")
                                    break

                            if target_sheet:
                                sheet_file = target_sheet.split("/")[-1]
                                rels_sheet_path = f"xl/worksheets/_rels/{sheet_file}.rels"
                                if rels_sheet_path in z.namelist():
                                    sheet_rels_root = ET.fromstring(z.read(rels_sheet_path))
                                    slicer_target = None
                                    for r in sheet_rels_root.iter():
                                        t = r.attrib.get("Type", "")
                                        if "slicer" in t.lower() or "slicer" in r.attrib.get("Target", "").lower():
                                            slicer_target = r.attrib.get("Target", "")
                                            break
                                    if slicer_target:
                                        slicer_file = slicer_target.split("/")[-1]
                                        slicer_path = f"xl/slicers/{slicer_file}"
                                        if slicer_path in z.namelist():
                                            slicer_root = ET.fromstring(z.read(slicer_path))
                                            for item in slicer_root.iter():
                                                if item.attrib.get("cache"):
                                                    cache_target = normalizar_columna(item.attrib.get("cache"))
                                                    break
                    except Exception:
                        pass

                # 2. Si no se encontró por relación directa de hoja, buscar por nombre o contenido
                if not cache_target:
                    for name in z.namelist():
                        if "slicers/slicer" in name.lower():
                            root = ET.fromstring(z.read(name))
                            for item in root.iter():
                                s_name = normalizar_columna(item.attrib.get("name", ""))
                                if "fecha" in s_name or "mes" in s_name:
                                    cache_target = normalizar_columna(item.attrib.get("cache", ""))
                                    break
                            if cache_target:
                                break

                # 3. Buscar la selección activa en los archivos slicerCaches
                if cache_target:
                    # Intento 1: Coincidencia exacta de cache
                    for name in z.namelist():
                        if "slicercaches/" in name.lower():
                            root = ET.fromstring(z.read(name))
                            c_name = normalizar_columna(root.attrib.get("name", ""))
                            if c_name == cache_target:
                                for sel in root.iter():
                                    if sel.tag.endswith("selection"):
                                        val = sel.attrib.get("n", "")
                                        if "&[" in val:
                                            mes_raw = val.split("&[")[-1].rstrip("]").strip().lower()
                                            return mes_raw

                    # Intento 2: Coincidencia parcial si no hubo exacta
                    for name in z.namelist():
                        if "slicercaches/" in name.lower():
                            root = ET.fromstring(z.read(name))
                            c_name = normalizar_columna(root.attrib.get("name", ""))
                            if cache_target in c_name:
                                for sel in root.iter():
                                    if sel.tag.endswith("selection"):
                                        val = sel.attrib.get("n", "")
                                        if "&[" in val:
                                            mes_raw = val.split("&[")[-1].rstrip("]").strip().lower()
                                            return mes_raw

        except Exception:
            pass

        return ""

    @classmethod
    def inspeccionar_estructura(cls, origen_excel) -> dict:
        """
        Inspecciona el archivo Excel y devuelve un resumen de:
        - Lista de hojas VISIBLES (omite hojas ocultas).
        - Para cada hoja visible: columnas disponibles, lista de meses únicos y mes activo en el slicer.
        """
        import openpyxl

        if isinstance(origen_excel, str):
            with open(origen_excel, "rb") as f:
                contenido_bytes = io.BytesIO(f.read())
        else:
            contenido_bytes = origen_excel
            contenido_bytes.seek(0)

        wb = openpyxl.load_workbook(contenido_bytes, read_only=False, data_only=True)
        hojas_visibles = [s for s in wb.sheetnames if wb[s].sheet_state == "visible"]

        resultado_hojas = {}
        for h in hojas_visibles:
            ws = wb[h]
            encabezados = []
            fila_encabezado = None

            # Buscar fila de encabezados en las primeras 20 filas
            for r in range(1, min(25, ws.max_row + 1)):
                vals = [str(ws.cell(r, c).value or "").strip() for c in range(1, min(40, ws.max_column + 1))]
                norm_vals = [normalizar_columna(v) for v in vals if v]
                if any(k in norm_vals for k in ("encargado", "nombre", "tienda", "total_venta", "neto_a_pagar", "cedula")):
                    fila_encabezado = r
                    encabezados = [ws.cell(r, c).value for c in range(1, min(40, ws.max_column + 1))]
                    break

            cols_limpias = []
            for c in encabezados:
                if c is not None and str(c).strip() and str(c).strip() not in cols_limpias:
                    cols_limpias.append(str(c).strip())

            # Detectar columna de mes
            meses = []
            col_mes_idx = None
            for idx, col in enumerate(encabezados, 1):
                if col and normalizar_columna(col) in ("fecha_(mes)", "fecha_mes", "mes", "periodo"):
                    col_mes_idx = idx
                    break

            if col_mes_idx:
                for r in range((fila_encabezado or 1) + 1, min((fila_encabezado or 1) + 300, ws.max_row + 1)):
                    val = ws.cell(r, col_mes_idx).value
                    if val is not None:
                        val_s = str(val).strip().lower()
                        if val_s not in ("fecha (mes)", "mes", "total general", "none", "") and val_s not in meses:
                            meses.append(val_s)

            # Obtener el mes seleccionado en el slicer de esta hoja
            mes_slicer = cls.extraer_periodo_de_slicer(contenido_bytes, nombre_hoja=h)

            resultado_hojas[h] = {
                "columnas": cols_limpias,
                "meses": meses,
                "mes_slicer": mes_slicer,
            }

        return {
            "hojas_visibles": hojas_visibles,
            "hojas_info": resultado_hojas,
        }

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
    def read_payments(cls, path, config_carga: dict = None):
        """
        Método de lectura para archivos Excel (.xlsx, .xls) o CSV locales.
        Si se pasa config_carga (dict con 'hoja', 'columnas', 'mes'), procesa
        exclusivamente la hoja seleccionada, filtrando por el mes indicado y
        extrayendo las columnas marcadas por el usuario.
        """
        import os
        from controllers.settings_controller import SettingsController
        from models.auditoria_model import registrar_auditoria

        ruta_str = str(path).lower()
        if ruta_str.endswith(".csv"):
            filas = cls.read_payments_from_csv(path)
            registrar_auditoria("cargar_excel", entidad=os.path.basename(path), detalle=f"formato=csv, registros={len(filas)}")
            return filas

        # Manejo de archivo Excel (.xlsx / .xls)
        with open(path, "rb") as f:
            contenido_bytes = io.BytesIO(f.read())

        # Si el usuario especificó una configuración personalizada
        if config_carga and isinstance(config_carga, dict) and config_carga.get("hoja"):
            hoja_nombre = config_carga["hoja"]
            mes_filtro = (config_carga.get("mes") or "").strip().lower()
            cols_deseadas = config_carga.get("columnas") or []
            cols_deseadas_norm = {normalizar_columna(c): c for c in cols_deseadas}

            contenido_bytes.seek(0)
            df = pd.read_excel(contenido_bytes, sheet_name=hoja_nombre, header=None, dtype=str)
            df = df.fillna("")

            # Localizar fila de encabezados
            fila_encabezado_idx = None
            encabezados_raw = []
            for idx, row in df.iterrows():
                vals = [str(v).strip() for v in row.values]
                norm_vals = [normalizar_columna(v) for v in vals if v]
                if any(k in norm_vals for k in ("encargado", "nombre", "tienda", "cedula", "total_venta", "neto_a_pagar")):
                    fila_encabezado_idx = idx
                    encabezados_raw = vals
                    break

            if fila_encabezado_idx is None:
                fila_encabezado_idx = 0
                encabezados_raw = [str(v).strip() for v in df.iloc[0].values]

            # Detectar bloques independientes de columnas (tablas paralelas lado a lado)
            bloques = []
            bloque_actual = []
            for c_idx, c_name in enumerate(encabezados_raw):
                nombre_limpio = str(c_name or "").strip()
                if not nombre_limpio or nombre_limpio.lower() in ("nan", "none", "unnamed"):
                    if bloque_actual:
                        bloques.append(bloque_actual)
                        bloque_actual = []
                    continue

                c_norm = normalizar_columna(nombre_limpio)
                ya_tiene_nombre = any(normalizar_columna(x[1]) in ("encargado", "nombre", "nombre_encargado") for x in bloque_actual)
                if c_norm in ("encargado", "nombre", "nombre_encargado") and ya_tiene_nombre:
                    bloques.append(bloque_actual)
                    bloque_actual = []

                bloque_actual.append((c_idx, nombre_limpio))

            if bloque_actual:
                bloques.append(bloque_actual)

            # Filtrar bloques con al menos 2 columnas para descartar columnas aisladas
            bloques = [b for b in bloques if len(b) >= 2]

            if not bloques:
                bloques = [[(i, c) for i, c in enumerate(encabezados_raw) if c.strip()]]

            # Importar modelo para resolución de cédulas
            from models.employee_model import EmployeeModel

            filas_resultado = []

            for bloque in bloques:
                mapa_col_bloque = {normalizar_columna(name): c_idx for c_idx, name in bloque}

                # Detectar índice de columna de mes para este bloque
                col_mes_idx = None
                for c_idx, name in bloque:
                    if normalizar_columna(name) in ("fecha_(mes)", "fecha_mes", "mes", "periodo"):
                        col_mes_idx = c_idx
                        break

                for idx in range(fila_encabezado_idx + 1, len(df)):
                    vals = [str(v).strip() for v in df.iloc[idx].values]
                    if not any(vals):
                        continue

                    # Obtener nombre en este bloque
                    col_nombre_idx = None
                    for k in ("encargado", "nombre", "nombre_del_encargado", "nombre_encargado"):
                        if k in mapa_col_bloque:
                            col_nombre_idx = mapa_col_bloque[k]
                            break

                    if col_nombre_idx is None or col_nombre_idx >= len(vals):
                        continue

                    nombre_val = vals[col_nombre_idx]
                    if not nombre_val or es_totalizador(nombre_val) or nombre_val.lower() in ("(en blanco)", "total general", "encargado", "none", "nan"):
                        continue

                    # Filtrar por mes si aplica
                    if mes_filtro and col_mes_idx is not None and col_mes_idx < len(vals):
                        mes_fila = vals[col_mes_idx].lower().strip()
                        mes_norm = MESES_MAP.get(mes_fila, mes_fila)
                        mes_filtro_norm = MESES_MAP.get(mes_filtro, mes_filtro)
                        if mes_norm != mes_filtro_norm and mes_fila != mes_filtro:
                            continue

                    # Determinar cédula: si viene en el bloque usarla, sino buscar en BD
                    cedula_val = ""
                    for k in ALIAS_CEDULA:
                        if k in mapa_col_bloque:
                            c_i = mapa_col_bloque[k]
                            if c_i < len(vals) and vals[c_i]:
                                cedula_val = limpiar_cedula(vals[c_i])
                                break

                    if not cedula_val or cedula_val == "N/A":
                        try:
                            emp_bd = EmployeeModel.get_by_nombre(nombre_val)
                            if emp_bd and emp_bd.get("cedula"):
                                cedula_val = emp_bd["cedula"]
                            else:
                                cedula_val = "N/A"
                        except Exception:
                            cedula_val = "N/A"

                    # Extraer unidad administrativa / tienda
                    tienda_val = ""
                    for k in ("tienda", "unidad_administrativa"):
                        if k in mapa_col_bloque:
                            c_i = mapa_col_bloque[k]
                            if c_i < len(vals):
                                tienda_val = vals[c_i]
                                break

                    fila_procesada = {}
                    # Extraer columnas deseadas por el usuario
                    for col_orig in cols_deseadas:
                        c_norm = normalizar_columna(col_orig)
                        val_orig = ""
                        if c_norm in mapa_col_bloque:
                            c_i = mapa_col_bloque[c_norm]
                            if c_i < len(vals):
                                val_orig = vals[c_i]

                        # Formatear montos numéricos conocidos
                        if c_norm in ("total_venta", "gastos_deducibles", "neto_a_pagar", "vales", "monto_comision_encargado", "sueldo_encargado", "bonificacion_mensual", "monto_pagado", "neto_para_comisiones"):
                            val_final = SettingsController.format_amount(val_orig) if val_orig and val_orig != "N/A" else (val_orig or "N/A")
                        elif c_norm in ("encargado", "nombre"):
                            val_final = nombre_val
                        elif c_norm in ALIAS_CEDULA:
                            val_final = cedula_val
                        elif c_norm in ("fecha_(mes)", "fecha_mes", "mes", "periodo"):
                            val_final = mes_filtro or val_orig or "N/A"
                        elif c_norm in ("tienda", "unidad_administrativa"):
                            val_final = tienda_val or "N/A"
                        else:
                            val_final = val_orig if val_orig else "N/A"

                        # Guardar con el nombre original visual seleccionado
                        fila_procesada[col_orig.strip()] = val_final
                        # Guardar también con la clave estandarizada si difiere para compatibilidad
                        clave_std = ENCARGADOS_COLUMN_MAP.get(c_norm)
                        if clave_std and clave_std not in fila_procesada:
                            fila_procesada[clave_std] = val_final

                    # Asegurar presencia de campos base requeridos por el sistema
                    if "nombre" not in fila_procesada:
                        fila_procesada["nombre"] = nombre_val
                    if "cedula" not in fila_procesada:
                        fila_procesada["cedula"] = cedula_val
                    if "periodo" not in fila_procesada:
                        fila_procesada["periodo"] = mes_filtro or "N/A"
                    if "unidad_administrativa" not in fila_procesada and tienda_val:
                        fila_procesada["unidad_administrativa"] = tienda_val

                    filas_resultado.append(fila_procesada)

            registrar_auditoria(
                "cargar_excel",
                entidad=os.path.basename(path),
                detalle=f"hoja={hoja_nombre}, mes={mes_filtro or 'todos'}, columnas={len(cols_deseadas)}, registros={len(filas_resultado)}"
            )
            return filas_resultado

        # Modo por defecto sin config_carga (hoja de resumen o primera disponible)
        periodo_slicer = cls.extraer_periodo_de_slicer(contenido_bytes) if ruta_str.endswith(".xlsx") else ""

        contenido_bytes.seek(0)
        with pd.ExcelFile(contenido_bytes, engine="openpyxl" if ruta_str.endswith(".xlsx") else None) as excel_file:
            nombres_hojas = excel_file.sheet_names

            hoja_objetivo = None
            busqueda_normalizada = normalizar_columna(HOJA_EXCEL_PAGO_RESUMEN)

            for hoja in nombres_hojas:
                if normalizar_columna(hoja) == busqueda_normalizada:
                    hoja_objetivo = hoja
                    break

            if not hoja_objetivo:
                for hoja in nombres_hojas:
                    norm_h = normalizar_columna(hoja)
                    if "pago" in norm_h and "resumen" in norm_h:
                        hoja_objetivo = hoja
                        break

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
        filas = cls._procesar_dataframe_pagos(df, periodo_defecto=periodo_slicer, omitir_pagos_realizados=True)
        registrar_auditoria(
            "cargar_excel",
            entidad=os.path.basename(path),
            detalle=f"hoja={hoja_objetivo}, periodo={periodo_slicer}, registros={len(filas)}"
        )
        return filas

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
