"""
Servicio: lectura del archivo Excel de pagos.
Es un servicio (no un modelo de datos propio) porque adapta una fuente
externa (un .xlsx) al formato que la aplicación necesita.
"""

import pandas as pd


class ExcelReader:

    REQUIRED_COLUMN = "cedula"

    @classmethod
    def read_payments(cls, path):
        """
        Lee el Excel y devuelve una lista de diccionarios (uno por fila).
        Lanza ValueError si no existe la columna 'cedula'.
        """
        df = pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        if cls.REQUIRED_COLUMN not in df.columns:
            raise ValueError(
                f"El archivo Excel debe contener una columna llamada '{cls.REQUIRED_COLUMN}'. "
                f"Columnas encontradas: {', '.join(df.columns)}"
            )

        df = df.fillna("")
        filas = df.to_dict(orient="records")

        # Limpieza básica de la cédula (pandas a veces la vuelve '123.0')
        for fila in filas:
            cedula = str(fila.get(cls.REQUIRED_COLUMN, "")).strip()
            if cedula.endswith(".0"):
                cedula = cedula[:-2]
            fila[cls.REQUIRED_COLUMN] = cedula

        return filas
