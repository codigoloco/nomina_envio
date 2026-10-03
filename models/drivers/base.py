"""
Driver base de base de datos.
Cada motor (SQLite, MySQL, PostgreSQL, SQL Server) hereda de esta clase y
solo implementa lo que es distinto: cómo abrir la conexión, los tipos de
columna y cómo saber si una tabla existe. El resto de la aplicación habla
únicamente con esta interfaz (principio de inversión de dependencias).
"""


class DriverNoDisponibleError(Exception):
    """El motor está soportado pero falta la librería/ODBC en el equipo."""


class DriverBase:
    clave = ""
    etiqueta = ""
    puerto_defecto = 0
    placeholder = "?"
    usa_archivo = False

    # Tipos lógicos -> tipo SQL propio de cada motor
    tipos = {
        "entero": "INTEGER",
        "texto": "TEXT",
        "cadena": "VARCHAR({n})",
    }

    def abrir(self, config: dict):
        """Abre y devuelve la conexión nativa (sin envolver)."""
        raise NotImplementedError

    def sql_id(self) -> str:
        """Definición SQL de la clave primaria autoincremental."""
        raise NotImplementedError

    def sql_existe_tabla(self, nombre: str):
        """Devuelve (sql, params) con '?' como marcador para consultar si existe la tabla."""
        raise NotImplementedError

    def sufijo_tabla(self) -> str:
        """Texto opcional al final del CREATE TABLE (ej. ENGINE=InnoDB)."""
        return ""

    def tipo_sql(self, tipo: str, longitud: int = None) -> str:
        return self.tipos[tipo].format(n=longitud or 255)

    def adaptar_sql(self, sql: str) -> str:
        """Convierte los marcadores '?' al estilo del motor."""
        if self.placeholder == "?":
            return sql
        return sql.replace("?", self.placeholder)

    def probar(self, config: dict):
        """
        Intenta conectar y ejecutar una consulta mínima.
        @return tupla (ok: bool, mensaje: str)
        """
        try:
            conexion_nativa = self.abrir(config)
        except DriverNoDisponibleError as error:
            return False, str(error)
        except Exception as error:
            return False, f"No se pudo conectar: {error}"

        try:
            cursor = conexion_nativa.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
        except Exception as error:
            return False, f"La conexión se abrió pero la consulta de prueba falló: {error}"
        finally:
            try:
                conexion_nativa.close()
            except Exception:
                pass
        return True, "Conexión realizada correctamente."
