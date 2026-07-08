"""
Controlador: Configuración SMTP.
Encapsula el almacenamiento (QSettings) para que la vista (SettingsDialog)
no acceda directamente al mecanismo de persistencia.
"""

from PyQt5 import QtCore

_ORG = "MiEmpresa"
_APP = "NominaApp"


class SettingsController:

    @staticmethod
    def get_smtp_config():
        settings = QtCore.QSettings(_ORG, _APP)
        return {
            "host": settings.value("smtp/host", ""),
            "port": settings.value("smtp/port", "587"),
            "user": settings.value("smtp/user", ""),
            "password": settings.value("smtp/password", ""),
            "remitente_nombre": settings.value("smtp/remitente", ""),
            "use_tls": settings.value("smtp/use_tls", "true") == "true",
        }

    @staticmethod
    def save_smtp_config(host, port, user, password, remitente_nombre, use_tls):
        settings = QtCore.QSettings(_ORG, _APP)
        settings.setValue("smtp/host", host)
        settings.setValue("smtp/port", port or "587")
        settings.setValue("smtp/user", user)
        settings.setValue("smtp/password", password)
        settings.setValue("smtp/remitente", remitente_nombre)
        settings.setValue("smtp/use_tls", "true" if use_tls else "false")

    @staticmethod
    def get_currency_config():
        settings = QtCore.QSettings(_ORG, _APP)
        return {
            "mask": settings.value("currency/mask", "Bs. {monto}"),
            "thousands_sep": settings.value("currency/thousands_sep", "."),
            "decimal_sep": settings.value("currency/decimal_sep", ","),
        }

    @staticmethod
    def save_currency_config(mask, thousands_sep, decimal_sep):
        settings = QtCore.QSettings(_ORG, _APP)
        settings.setValue("currency/mask", mask)
        settings.setValue("currency/thousands_sep", thousands_sep)
        settings.setValue("currency/decimal_sep", decimal_sep)

    @staticmethod
    def format_amount(val_str):
        """
        Formatea un valor numerico a formato de moneda con la mascara activa.
        Conserva el valor original si no es un numero convertible.
        @param val_str Valor original a evaluar.
        @return Valor formateado o el original.
        """
        if val_str is None:
            return ""
        val_str_clean = str(val_str).strip()
        if not val_str_clean:
            return val_str_clean

        # Normalizacion para parsear floats de Excel
        cleaned = val_str_clean.replace("$", "").replace("Bs.", "").replace(" ", "")

        if "," in cleaned and "." in cleaned:
            if cleaned.find(".") < cleaned.find(","):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            parts = cleaned.split(",")
            if len(parts) == 2:
                cleaned = cleaned.replace(",", ".")

        try:
            val_float = float(cleaned)
        except ValueError:
            return val_str_clean

        config = SettingsController.get_currency_config()
        mask = config["mask"]
        thousands_sep = config["thousands_sep"]
        decimal_sep = config["decimal_sep"]

        is_negative = val_float < 0
        val_abs = abs(val_float)

        # Redondear y forzar 2 decimales
        formatted_raw = f"{val_abs:.2f}"
        parts = formatted_raw.split(".")
        entera = parts[0]
        decimal = parts[1]

        # Insertar separadores de miles
        entera_sep = ""
        for i, digit in enumerate(reversed(entera)):
            if i > 0 and i % 3 == 0:
                entera_sep = thousands_sep + entera_sep
            entera_sep = digit + entera_sep

        monto_str = entera_sep + decimal_sep + decimal
        result = mask.replace("{monto}", monto_str)

        if is_negative:
            result = "-" + result

        return result

