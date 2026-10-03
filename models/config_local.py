"""
Configuración LOCAL de la aplicación (QSettings).
Aquí solo vive lo que no puede estar dentro de la base de datos: los datos
de las conexiones (la BD no puede contener los datos para conectarse a sí misma)
y los ajustes de la interfaz. Todo lo demás se centraliza en la base activa.
"""

from PyQt5 import QtCore

ORG = "MiEmpresa"
APP = "NominaApp"


def abrir_qsettings() -> QtCore.QSettings:
    """Devuelve el QSettings local de la aplicación."""
    return QtCore.QSettings(ORG, APP)
