"""
Fábrica de drivers de base de datos.
Agregar un motor nuevo = crear su clase y registrarla en _DRIVERS (abierto/cerrado).
"""

from models.drivers.base import DriverBase, DriverNoDisponibleError
from models.drivers.sqlserver_driver import SqlServerDriver
from models.drivers.sqlite_driver import SqliteDriver
from models.drivers.mysql_driver import MysqlDriver
from models.drivers.postgres_driver import PostgresDriver

# El orden de este diccionario es el orden que se muestra en el desplegable.
_DRIVERS = {
    driver.clave: driver
    for driver in (SqlServerDriver(), SqliteDriver(), MysqlDriver(), PostgresDriver())
}


def obtener_driver(clave: str) -> DriverBase:
    """Devuelve el driver del motor indicado (ej. 'mysql'). Lanza ValueError si no existe."""
    clave_norm = str(clave).strip().lower()
    if clave_norm not in _DRIVERS:
        raise ValueError(f"Motor de base de datos no soportado: '{clave}'")
    return _DRIVERS[clave_norm]


def listar_motores() -> list:
    """Lista de dicts {clave, etiqueta, puerto, usa_archivo} para poblar el desplegable."""
    return [
        {
            "clave": d.clave,
            "etiqueta": d.etiqueta,
            "puerto": d.puerto_defecto,
            "usa_archivo": d.usa_archivo,
        }
        for d in _DRIVERS.values()
    ]
