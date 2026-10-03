"""
Envoltorio de conexión: da a TODOS los motores la misma interfaz que ya usaban
los modelos con SQLite (conn.execute(sql, params), fetchone/fetchall, commit, close).
- Convierte los marcadores '?' al estilo del motor.
- Devuelve las filas como diccionarios (dict(r) y r["columna"] siguen funcionando).
"""

from models.drivers.base import DriverBase


class CursorBD:
    def __init__(self, cursor):
        self._cursor = cursor

    def _columnas(self) -> list:
        descripcion = self._cursor.description
        return [d[0] for d in descripcion] if descripcion else []

    def fetchone(self):
        fila = self._cursor.fetchone()
        if fila is None:
            return None
        return dict(zip(self._columnas(), fila))

    def fetchall(self) -> list:
        columnas = self._columnas()
        return [dict(zip(columnas, fila)) for fila in self._cursor.fetchall()]

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount


class ConexionBD:
    def __init__(self, conexion_nativa, driver: DriverBase):
        self._conexion = conexion_nativa
        self.driver = driver

    def execute(self, sql: str, params=()) -> CursorBD:
        cursor = self._conexion.cursor()
        sql_adaptado = self.driver.adaptar_sql(sql)
        if params:
            cursor.execute(sql_adaptado, tuple(params))
        else:
            cursor.execute(sql_adaptado)
        return CursorBD(cursor)

    def commit(self):
        self._conexion.commit()

    def rollback(self):
        self._conexion.rollback()

    def close(self):
        self._conexion.close()
