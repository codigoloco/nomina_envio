"""Migración: crea la tabla 'envios' (historial de correos enviados)."""

from models.esquema import Columna


def crear_tabla_envios(esquema):
    esquema.crear_tabla("envios", [
        Columna.id_autoincremental(),
        Columna("empleado_id", "entero"),
        Columna("cedula", "cadena", 50),
        Columna("nombre", "cadena", 255),
        Columna("correo", "cadena", 255),
        Columna("periodo", "cadena", 100),
        Columna("monto", "cadena", 100),
        Columna("asunto", "cadena", 500),
        Columna("fecha_envio", "cadena", 19, nulo=False),
        Columna("estado", "cadena", 30, nulo=False),
        Columna("detalle", "texto"),
        Columna("datos_json", "texto"),
    ], foraneas=[("empleado_id", "empleados", "id")])
