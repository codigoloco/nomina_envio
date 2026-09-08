"""
Servicio: lectura de archivos Excel y Google Sheets (incluyendo Tablas Dinámicas y Múltiples Cuadros).
Soporta la lectura unificada del Cuadro 1 (Trabajadores con cédula) y Cuadro 2 (Encargados especiales sin cédula -> 'N/A').
Rango: A1:N(última fila con datos). No modifica ningún archivo; solo lectura.
"""

import unicodedata
import pandas as pd

# Mapa de columnas exactas A1:N1 -> nombre interno estandarizado
ENCARGADOS_COLUMN_MAP = {
    "encargado": "nombre",
    "nombre_del_encargado": "nombre",
    "nombre": "nombre",
    "cedula": "cedula",
    "tienda": "unidad_administrativa",
    "unidad_administrativa": "unidad_administrativa",
    "mes": "periodo",
    "total_venta": "TOTAL VENTA",
    "gastos_deducibles": "Gastos deducibles",
    "neto_(ventas_-_gastos)": "Neto (Ventas - Gastos)",
    "%_comision": "% Comision",
    "comision": "% Comision",
    "comision_encargado": "Comision encargado",
    "sueldo": "Sueldo",
    "bonificacion": "Bonificacion",
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
TOTALIZADORES_EXACTOS = {"suma_total", "total_general", "grand_total", "totales", "resultado_general", "suma_totales"}
ALIAS_CEDULA = {"cedula", "ci", "c_i", "cedula_de_identidad", "nro_cedula", "numero_cedula", "documento"}


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
    def read_payments_from_csv(cls, path_csv):
        """
        Lee todos los cuadros de 'Pagos a encargados' desde un archivo CSV.
        Soporta Cuadro 1 (con cédula) y Cuadro 2 (sin cédula -> 'N/A').
        Formatea campos faltantes como 'N/A'.
        """
        df = pd.read_csv(path_csv, header=None, dtype=str)
        df = df.fillna("")

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

        for idx, row_vals in df.iterrows():
            vals = [str(v).strip() for v in row_vals.values]
            if not any(vals):
                continue

            first_val = vals[0]
            norm_first = normalizar_columna(first_val)

            # Detectar fila de encabezados para un nuevo bloque/cuadro
            if norm_first in ("encargado", "nombre", "nombre_del_encargado"):
                mapa_columnas_actual = []
                tiene_cedula_en_bloque = False
                for c_i, c_val in enumerate(vals):
                    c_norm = normalizar_columna(c_val)
                    if c_norm in ENCARGADOS_COLUMN_MAP:
                        col_mapped = ENCARGADOS_COLUMN_MAP[c_norm]
                    elif "encargado" in c_norm or "nombre" in c_norm:
                        col_mapped = "nombre"
                    elif "cedula" in c_norm or "ci" in c_norm:
                        col_mapped = "cedula"
                    elif "tienda" in c_norm:
                        col_mapped = "unidad_administrativa"
                    elif c_norm in ("mes", "periodo"):
                        col_mapped = "periodo"
                    else:
                        col_mapped = c_val

                    # Si el encabezado está vacío en columnas financieras, asignar el nombre posicional predeterminado
                    if (not col_mapped or col_mapped.lower() in ("nan", "none", "")) and c_i < len(NOMBRES_COLUMNAS_POSICIONALES):
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
                    if c_i < len(vals):
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
    def read_payments(cls, path):
        """
        Método de lectura para archivos Excel/CSV locales.
        """
        return cls.read_payments_from_csv(path)

    @classmethod
    def read_employees_template(cls, path):
        """
        Lee una plantilla de empleados generada por la aplicación y devuelve
        una lista de diccionarios. Valida la presencia de la columna 'cedula'.
        """
        df = pd.read_excel(path, header=0, dtype=str)
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
