"""Migración: crea la tabla 'config_carga_excel' (recuerda la última hoja, columnas y mes seleccionados)."""

from models.esquema import Columna


def crear_tabla_config_carga_excel(esquema):
    esquema.crear_tabla("config_carga_excel", [
        Columna.id_autoincremental(),
        Columna("hoja", "cadena", 150, nulo=False),
        Columna("columnas_json", "texto", nulo=False),
        Columna("mes", "cadena", 50),
        Columna("actualizado", "cadena", 19, nulo=False),
    ])
