"""
Punto único de acceso a la base de datos.
Ya NO existe una base SQLite por defecto: la app trabaja con la conexión
marcada como ACTIVA en Configuración > Conexiones de base de datos.
Los modelos (EmployeeModel, EnvioModel, ...) siguen llamando a get_connection().
"""

import os

from models.conexion_bd import ConexionBD
from models.conexion_config_model import ConexionConfigModel
from models.drivers import obtener_driver

# Ruta del antiguo nomina.db: solo se usa para importar datos locales hacia la base nueva.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DB_LEGADA = os.path.join(BASE_DIR, "nomina.db")


class SinConexionActivaError(Exception):
    """No hay ninguna conexión de base de datos marcada como activa."""


def abrir_conexion(config: dict) -> ConexionBD:
    """Abre una conexión con la configuración indicada (sea o no la activa)."""
    driver = obtener_driver(config["motor"])
    return ConexionBD(driver.abrir(config), driver)


def get_connection() -> ConexionBD:
    """Abre una conexión a la base de datos ACTIVA."""
    config = ConexionConfigModel.obtener_activa()
    if not config:
        raise SinConexionActivaError(
            "No hay una base de datos activa. Configure una en Configuración > Conexiones de base de datos."
        )
    return abrir_conexion(config)
