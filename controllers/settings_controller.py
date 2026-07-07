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
