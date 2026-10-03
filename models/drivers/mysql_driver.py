"""Driver MySQL / MariaDB (librería: pymysql)."""

from models.drivers.base import DriverBase, DriverNoDisponibleError


class MysqlDriver(DriverBase):
    clave = "mysql"
    etiqueta = "MySQL"
    puerto_defecto = 3306
    placeholder = "%s"

    tipos = {
        "entero": "INT",
        "texto": "LONGTEXT",
        "cadena": "VARCHAR({n})",
    }

    def abrir(self, config: dict):
        try:
            import pymysql
        except ImportError:
            raise DriverNoDisponibleError(
                "Falta la librería 'pymysql'. Instálela con: pip install pymysql"
            )
        return pymysql.connect(
            host=config.get("host", ""),
            port=int(config.get("puerto") or self.puerto_defecto),
            user=config.get("usuario", ""),
            password=config.get("password", ""),
            database=config.get("base_datos", ""),
            charset="utf8mb4",
            connect_timeout=5,
        )

    def sql_id(self) -> str:
        return "INT AUTO_INCREMENT PRIMARY KEY"

    def sufijo_tabla(self) -> str:
        return "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"

    def sql_existe_tabla(self, nombre: str):
        return (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = ?",
            (nombre,),
        )
