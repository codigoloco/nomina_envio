"""Migración: crea la tabla 'migraciones' (registro de migraciones ejecutadas)."""

from models.migracion_model import MigracionModel


def crear_tabla_migraciones(esquema):
    MigracionModel.asegurar_tabla(esquema.conexion)
