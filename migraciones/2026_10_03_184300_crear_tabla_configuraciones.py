"""Migración: crea la tabla 'configuraciones' (ajustes centralizados clave/valor, ej. SMTP)."""

from models.esquema import Columna


def crear_tabla_configuraciones(esquema):
    esquema.crear_tabla("configuraciones", [
        Columna.id_autoincremental(),
        Columna("clave", "cadena", 100, nulo=False, unico=True),
        Columna("valor", "texto"),
        Columna("actualizado", "cadena", 19),
    ])
