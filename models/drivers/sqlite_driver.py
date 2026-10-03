"""Driver SQLite (archivo local). Solo existe si el usuario crea esa conexión."""

import os
import sqlite3

from models.drivers.base import DriverBase


class SqliteDriver(DriverBase):
    clave = "sqlite"
    etiqueta = "SQLite"
    puerto_defecto = 0
    placeholder = "?"
    usa_archivo = True

    def abrir(self, config: dict):
        ruta = str(config.get("base_datos", "")).strip()
        if not ruta:
            raise ValueError("Debe indicar el archivo de la base de datos SQLite.")
        carpeta = os.path.dirname(os.path.abspath(ruta))
        if not os.path.isdir(carpeta):
            raise ValueError(f"La carpeta '{carpeta}' no existe.")
        conexion = sqlite3.connect(ruta, timeout=5)
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    def sql_id(self) -> str:
        return "INTEGER PRIMARY KEY AUTOINCREMENT"

    def sql_existe_tabla(self, nombre: str):
        return "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (nombre,)
