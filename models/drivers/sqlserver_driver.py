"""Driver SQL Server (librería: pyodbc + 'ODBC Driver for SQL Server' instalado en Windows)."""

from models.drivers.base import DriverBase, DriverNoDisponibleError


def _escapar_valor_odbc(valor: str) -> str:
    """Encierra un valor entre llaves para que ';' o '}' no rompan la cadena de conexión."""
    return "{" + str(valor).replace("}", "}}") + "}"


class SqlServerDriver(DriverBase):
    clave = "sqlserver"
    etiqueta = "SQL Server"
    puerto_defecto = 1433
    placeholder = "?"

    tipos = {
        "entero": "INT",
        "texto": "NVARCHAR(MAX)",
        "cadena": "NVARCHAR({n})",
    }

    @classmethod
    def listar_controladores(cls) -> list:
        """Devuelve los drivers ODBC de SQL Server instalados en Windows ordenados por modernidad."""
        try:
            import pyodbc
            instalados = [d for d in pyodbc.drivers() if "SQL Server" in d]
            modernos = sorted((d for d in instalados if d.startswith("ODBC Driver")), reverse=True)
            otros = [d for d in instalados if not d.startswith("ODBC Driver")]
            return modernos + otros
        except Exception:
            return []

    def _resolver_driver_odbc(self, driver_solicitado: str = None) -> str:
        controladores = self.listar_controladores()
        if driver_solicitado and driver_solicitado in controladores:
            return driver_solicitado
        if controladores:
            return controladores[0]
        raise DriverNoDisponibleError(
            "Falta la librería 'pyodbc' o no hay controladores ODBC de SQL Server instalados en Windows."
        )

    def abrir(self, config: dict):
        try:
            import pyodbc
        except ImportError:
            raise DriverNoDisponibleError(
                "Falta la librería 'pyodbc'. Instálela con: pip install pyodbc"
            )

        driver_odbc = self._resolver_driver_odbc(config.get("driver_odbc"))
        puerto = int(config.get("puerto") or self.puerto_defecto)
        cadena = (
            f"DRIVER={{{driver_odbc}}};"
            f"SERVER={config.get('host', '')},{puerto};"
            f"DATABASE={_escapar_valor_odbc(config.get('base_datos', ''))};"
            f"UID={_escapar_valor_odbc(config.get('usuario', ''))};"
            f"PWD={_escapar_valor_odbc(config.get('password', ''))};"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(cadena, timeout=6)

    def probar(self, config: dict):
        """
        Prueba la conexión al servidor. Si la base de datos no existe aún (error 4060),
        valida las credenciales contra la base de datos 'master' y notifica al usuario.
        """
        ok, mensaje = super().probar(config)
        if ok:
            return ok, mensaje

        # Si falló la conexión directa, verificar si es porque la base de datos no existe
        try:
            import pyodbc
            driver_odbc = self._resolver_driver_odbc(config.get("driver_odbc"))
            puerto = int(config.get("puerto") or self.puerto_defecto)
            cadena_master = (
                f"DRIVER={{{driver_odbc}}};"
                f"SERVER={config.get('host', '')},{puerto};"
                f"DATABASE=master;"
                f"UID={_escapar_valor_odbc(config.get('usuario', ''))};"
                f"PWD={_escapar_valor_odbc(config.get('password', ''))};"
                "TrustServerCertificate=yes;"
            )
            conexion_master = pyodbc.connect(cadena_master, timeout=6)
            cur = conexion_master.cursor()
            bd_nombre = config.get("base_datos", "").strip()
            cur.execute("SELECT name FROM sys.databases WHERE name = ?", (bd_nombre,))
            existe = cur.fetchone() is not None
            conexion_master.close()

            if not existe:
                return True, (
                    f"Conexión al servidor exitosa usando '{driver_odbc}'.\n"
                    f"Aviso: La base de datos '{bd_nombre}' aún no existe en SQL Server. "
                    f"Al presionar 'Migrar' se creará automáticamente."
                )
        except Exception:
            pass

        return ok, mensaje

    def asegurar_base_datos(self, config: dict):
        """Verifica si la base de datos existe en el servidor; si no existe, la crea conectando a master."""
        bd_nombre = config.get("base_datos", "").strip()
        if not bd_nombre:
            return

        import pyodbc
        driver_odbc = self._resolver_driver_odbc(config.get("driver_odbc"))
        puerto = int(config.get("puerto") or self.puerto_defecto)
        cadena_master = (
            f"DRIVER={{{driver_odbc}}};"
            f"SERVER={config.get('host', '')},{puerto};"
            f"DATABASE=master;"
            f"UID={_escapar_valor_odbc(config.get('usuario', ''))};"
            f"PWD={_escapar_valor_odbc(config.get('password', ''))};"
            "TrustServerCertificate=yes;"
        )
        # En SQL Server, CREATE DATABASE no puede ejecutarse dentro de una transacción explícita
        conexion_master = pyodbc.connect(cadena_master, autocommit=True, timeout=10)
        try:
            cur = conexion_master.cursor()
            cur.execute("SELECT name FROM sys.databases WHERE name = ?", (bd_nombre,))
            if not cur.fetchone():
                bd_escapada = bd_nombre.replace("]", "]]")
                cur.execute(f"CREATE DATABASE [{bd_escapada}]")
        finally:
            conexion_master.close()

    def sql_id(self) -> str:
        return "INT IDENTITY(1,1) PRIMARY KEY"

    def sql_existe_tabla(self, nombre: str):
        return (
            "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
            (nombre,),
        )
