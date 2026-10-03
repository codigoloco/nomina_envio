"""Migración: crea la tabla 'auditoria' (registro de acciones del sistema)."""

from models.esquema import Columna


def crear_tabla_auditoria(esquema):
    esquema.crear_tabla("auditoria", [
        Columna.id_autoincremental(),
        Columna("fecha", "cadena", 19, nulo=False),
        Columna("usuario", "cadena", 100),
        Columna("accion", "cadena", 100, nulo=False),
        Columna("entidad", "cadena", 255),
        Columna("detalle", "texto"),
    ])
