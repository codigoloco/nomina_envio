"""Migración: crea la tabla 'empleados'."""

from models.esquema import Columna


def crear_tabla_empleados(esquema):
    esquema.crear_tabla("empleados", [
        Columna.id_autoincremental(),
        Columna("cedula", "cadena", 50, nulo=False, unico=True),
        Columna("nombre", "cadena", 255, nulo=False),
        Columna("telefono", "cadena", 50),
        Columna("correo", "cadena", 255, nulo=False),
    ])
