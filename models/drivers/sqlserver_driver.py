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
        """Devuelve los drivers ODBC de SQL Server instalados en Windows ordenados por modernidad y compatibilidad."""
        try:
            import pyodbc
            todos = pyodbc.drivers()
            # Excluir controladores de réplica móvil o dañados (RDA)
            instalados = [d for d in todos if "sql server" in d.lower() and "rda" not in d.lower()]
            modernos = sorted((d for d in instalados if d.startswith("ODBC Driver")), reverse=True)
            clasico = [d for d in instalados if d == "SQL Server"]
            otros = [d for d in instalados if not d.startswith("ODBC Driver") and d != "SQL Server"]
            return modernos + clasico + otros
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

    def _construir_parametro_servidor(self, host: str, puerto: str = "", omitir_puerto: bool = False) -> str:
        """
        Construye el valor para SERVER en la cadena ODBC.
        Soporta IP (ej: 192.168.1.50) con puerto TCP, y nombres de equipo
        (ej: SRV-APP, localhost, ., SRV-APP\\SQLEXPRESS) sin forzar puerto
        para permitir memoria compartida y Named Pipes como usa Profit Plus.
        """
        import re
        host_limpio = str(host or "").strip()
        puerto_limpio = str(puerto or "").strip()

        if not host_limpio:
            return "localhost"

        if "," in host_limpio:
            return host_limpio

        if omitir_puerto:
            return host_limpio

        es_ip = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host_limpio))
        if es_ip:
            pto = puerto_limpio if puerto_limpio else str(self.puerto_defecto)
            return f"{host_limpio},{pto}"

        if puerto_limpio and puerto_limpio != str(self.puerto_defecto):
            return f"{host_limpio},{puerto_limpio}"

        return host_limpio

    def _armar_cadena(self, config: dict, driver_odbc: str, base_datos: str, omitir_puerto: bool = False) -> str:
        host = config.get("host", "")
        puerto = config.get("puerto", "")
        servidor = self._construir_parametro_servidor(host, puerto, omitir_puerto=omitir_puerto)

        return (
            f"DRIVER={{{driver_odbc}}};"
            f"SERVER={servidor};"
            f"DATABASE={_escapar_valor_odbc(base_datos)};"
            f"UID={_escapar_valor_odbc(config.get('usuario', ''))};"
            f"PWD={_escapar_valor_odbc(config.get('password', ''))};"
            "TrustServerCertificate=yes;"
        )

    def abrir(self, config: dict):
        try:
            import pyodbc
        except ImportError:
            raise DriverNoDisponibleError(
                "Falta la librería 'pyodbc'. Instálela con: pip install pyodbc"
            )

        driver_odbc = self._resolver_driver_odbc(config.get("driver_odbc"))
        cadena = self._armar_cadena(config, driver_odbc, config.get("base_datos", ""), omitir_puerto=False)
        try:
            return pyodbc.connect(cadena, timeout=6)
        except pyodbc.Error as e:
            # Si falló por timeout de red TCP (error 08001 / 258) y se usó puerto, reintentar sin puerto para usar memoria compartida / Named Pipes
            if "08001" in str(e) and "," in cadena:
                cadena_sin_puerto = self._armar_cadena(config, driver_odbc, config.get("base_datos", ""), omitir_puerto=True)
                return pyodbc.connect(cadena_sin_puerto, timeout=6)
            raise

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
            cadena_master = self._armar_cadena(config, driver_odbc, "master", omitir_puerto=False)
            try:
                conexion_master = pyodbc.connect(cadena_master, timeout=6)
            except pyodbc.Error as e:
                if "08001" in str(e) and "," in cadena_master:
                    cadena_master_sin = self._armar_cadena(config, driver_odbc, "master", omitir_puerto=True)
                    conexion_master = pyodbc.connect(cadena_master_sin, timeout=6)
                else:
                    raise

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
