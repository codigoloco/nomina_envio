"""
Servicio: lectura de archivos Excel externos.
Adapta fuentes externas (.xlsx) al formato que la aplicacion necesita.
No modifica ningun archivo; solo lectura.
"""

import pandas as pd

# Fila donde estan los encabezados reales en la hoja "Pago a encargados"
ENCARGADOS_HEADER_ROW = 8  # indice 0-based → fila 9 de Excel


# Mapa de columnas del Excel → nombre interno
ENCARGADOS_COLUMN_MAP = {
    "nombre del encargado": "nombre_encargado",
    "unidad administrativa": "unidad_administrativa",
    "monto a pagar": "monto_a_pagar",
    "monto del vale": "monto_vale",
    "comision": "comision",
    "bonificacion": "bonificacion"
}

ENCARGADOS_SHEET = "Pago a encargados"
EMPLOYEES_REQUIRED_COLUMN = "cedula"


class ExcelReader:

    @classmethod
    def read_encargados(cls, path):
        """
        Lee la hoja "Pago a encargados" del Excel de pagos y devuelve
        una lista de diccionarios con las 6 columnas de interes.
        Filtra las filas donde el nombre del encargado este vacio.
        @param path ruta absoluta al archivo .xlsx
        @return lista de dicts con claves: nombre_encargado, unidad_administrativa,
                monto_a_pagar, monto_vale, comision, bonificacion
        """
        df = pd.read_excel(
            path,
            sheet_name=ENCARGADOS_SHEET,
            header=ENCARGADOS_HEADER_ROW,
            dtype=str
        )
        df.columns = [str(c).strip().lower() for c in df.columns]

        columnas_requeridas = list(ENCARGADOS_COLUMN_MAP.keys())
        faltantes = [c for c in columnas_requeridas if c not in df.columns]
        if faltantes:
            raise ValueError(
                f"La hoja '{ENCARGADOS_SHEET}' no contiene las columnas esperadas: "
                f"{', '.join(faltantes)}. Columnas encontradas: {', '.join(df.columns)}"
            )

        df = df[columnas_requeridas].copy()
        df = df.rename(columns=ENCARGADOS_COLUMN_MAP)
        df = df.fillna("")
        df = df[df["nombre_encargado"].str.strip() != ""]

        filas = df.to_dict(orient="records")

        from controllers.settings_controller import SettingsController
        for fila in filas:
            for clave, valor in fila.items():
                if clave not in ("nombre_encargado", "unidad_administrativa", "cedula", "nombre", "telefono", "correo", "periodo"):
                    fila[clave] = SettingsController.format_amount(valor)

        return filas

    @classmethod
    def read_employees_template(cls, path):
        """
        Lee una plantilla de empleados generada por la aplicacion y devuelve
        una lista de diccionarios. Valida la presencia de la columna 'cedula'.
        @param path ruta al archivo .xlsx de la plantilla
        @return lista de dicts con claves: cedula, nombre, telefono, correo
        """
        df = pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        if EMPLOYEES_REQUIRED_COLUMN not in df.columns:
            raise ValueError(
                f"La plantilla debe contener una columna llamada 'cedula'. "
                f"Columnas encontradas: {', '.join(df.columns)}"
            )

        df = df.fillna("")
        filas = df.to_dict(orient="records")

        for fila in filas:
            cedula = str(fila.get("cedula", "")).strip()
            if cedula.endswith(".0"):
                cedula = cedula[:-2]
            fila["cedula"] = cedula

        return [f for f in filas if f.get("cedula")]

    @classmethod
    def read_payments(cls, path):
        """
        Lee el Excel. Si tiene la hoja 'Pago a encargados' con su formato correspondiente,
        la lee y mapea automaticamente. De lo contrario, lee la hoja activa buscando
        la columna 'cedula'.
        """
        try:
            # Intentar lectura especifica de la hoja de encargados
            return cls.read_encargados(path)
        except Exception:
            # Caida en caso de usar un Excel tradicional con columna 'cedula'
            df = pd.read_excel(path, dtype=str)
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

            if EMPLOYEES_REQUIRED_COLUMN not in df.columns:
                raise ValueError(
                    f"El archivo Excel debe contener una columna llamada 'cedula' o la hoja '{ENCARGADOS_SHEET}'. "
                    f"Columnas encontradas: {', '.join(df.columns)}"
                )

            df = df.fillna("")
            filas = df.to_dict(orient="records")

            from controllers.settings_controller import SettingsController
            for fila in filas:
                cedula = str(fila.get(EMPLOYEES_REQUIRED_COLUMN, "")).strip()
                if cedula.endswith(".0"):
                    cedula = cedula[:-2]
                fila[EMPLOYEES_REQUIRED_COLUMN] = cedula

                # Formatear montos en columnas de datos adicionales
                for clave, valor in fila.items():
                    if clave not in (EMPLOYEES_REQUIRED_COLUMN, "nombre", "telefono", "correo", "periodo"):
                        fila[clave] = SettingsController.format_amount(valor)

            return filas


