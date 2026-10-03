"""
Modelo: registro de migraciones ejecutadas (tabla 'migraciones').
Siempre trabaja sobre la conexión recibida, porque se migra una base destino
que puede no ser la activa.
"""

from datetime import datetime

from models.esquema import Columna, Esquema

TABLA = "migraciones"


class MigracionModel:

    @staticmethod
    def asegurar_tabla(conexion):
        """Crea la tabla 'migraciones' si todavía no existe en la base destino."""
        Esquema(conexion).crear_tabla(TABLA, [
            Columna.id_autoincremental(),
            Columna("migracion", "cadena", 191, nulo=False, unico=True),
            Columna("lote", "entero", nulo=False),
            Columna("fecha_ejecucion", "cadena", 19, nulo=False),
        ])

    @staticmethod
    def listar_ejecutadas(conexion) -> set:
        if not Esquema(conexion).existe_tabla(TABLA):
            return set()
        filas = conexion.execute("SELECT migracion FROM migraciones").fetchall()
        return {fila["migracion"] for fila in filas}

    @staticmethod
    def siguiente_lote(conexion) -> int:
        fila = conexion.execute("SELECT MAX(lote) AS lote_max FROM migraciones").fetchone()
        return int(fila["lote_max"] or 0) + 1

    @staticmethod
    def registrar(conexion, nombre: str, lote: int):
        conexion.execute(
            "INSERT INTO migraciones (migracion, lote, fecha_ejecucion) VALUES (?, ?, ?)",
            (nombre, lote, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conexion.commit()
