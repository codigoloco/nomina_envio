"""Driver PostgreSQL (librería: psycopg2)."""

from models.drivers.base import DriverBase, DriverNoDisponibleError


class PostgresDriver(DriverBase):
    clave = "postgresql"
    etiqueta = "PostgreSQL"
    puerto_defecto = 5432
    placeholder = "%s"

    tipos = {
        "entero": "INTEGER",
        "texto": "TEXT",
        "cadena": "VARCHAR({n})",
    }

    def abrir(self, config: dict):
        try:
            import psycopg2
        except ImportError:
            raise DriverNoDisponibleError(
                "Falta la librería 'psycopg2'. Instálela con: pip install psycopg2-binary"
            )
        return psycopg2.connect(
            host=config.get("host", ""),
            port=int(config.get("puerto") or self.puerto_defecto),
            user=config.get("usuario", ""),
            password=config.get("password", ""),
            dbname=config.get("base_datos", ""),
            connect_timeout=5,
        )

    def sql_id(self) -> str:
        return "SERIAL PRIMARY KEY"

    def sql_existe_tabla(self, nombre: str):
        return (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = ?",
            (nombre,),
        )
