"""
Controlador: conexiones a bases de datos.
Orquesta el almacén local de conexiones (modelo), los drivers, las migraciones y la
importación de datos locales. La vista (DatabaseDialog) solo habla con esta clase.
"""

from models.auditoria_model import registrar_auditoria
from models.conexion_config_model import ConexionConfigModel
from models.database import abrir_conexion
from models.drivers import listar_motores, obtener_driver
from services.importacion_local_service import ImportacionLocalService
from services.migration_service import MigrationService


class ConexionController:

    # ---------------------- Consultas ----------------------
    @staticmethod
    def listar_motores() -> list:
        return listar_motores()

    @staticmethod
    def listar_controladores_motor(motor_clave: str) -> list:
        driver = obtener_driver(motor_clave)
        if hasattr(driver, "listar_controladores"):
            return driver.listar_controladores()
        return []

    @staticmethod
    def listar() -> list:
        return ConexionConfigModel.listar()

    @staticmethod
    def nombre_activa() -> str:
        return ConexionConfigModel.nombre_activa()

    @staticmethod
    def hay_datos_locales() -> bool:
        return ImportacionLocalService.hay_datos_locales()

    # ---------------------- Validación ----------------------
    @staticmethod
    def _validar(config: dict):
        if not config.get("nombre", "").strip():
            raise ValueError("Debe indicar un nombre para la conexión.")
        driver = obtener_driver(config.get("motor", ""))
        if driver.usa_archivo:
            if not config.get("base_datos", "").strip():
                raise ValueError("Debe indicar el archivo de la base de datos.")
            return
        for campo, etiqueta in (("host", "el servidor (host)"), ("base_datos", "la base de datos"), ("usuario", "el usuario")):
            if not config.get(campo, "").strip():
                raise ValueError(f"Debe indicar {etiqueta}.")

    # ---------------------- Administración ----------------------
    @classmethod
    def guardar(cls, config: dict, nombre_original: str = None):
        cls._validar(config)
        ConexionConfigModel.guardar(config, nombre_original)
        registrar_auditoria(
            "guardar_conexion", entidad=config["nombre"],
            detalle=f"Motor={config['motor']}, host={config.get('host', '')}, bd={config.get('base_datos', '')}",
        )

    @staticmethod
    def eliminar(nombre: str):
        ConexionConfigModel.eliminar(nombre)
        registrar_auditoria("eliminar_conexion", entidad=nombre)

    # ---------------------- Operaciones sobre una conexión ----------------------
    @staticmethod
    def probar(config: dict) -> tuple:
        """@return (ok, mensaje)"""
        try:
            ok, mensaje = obtener_driver(config["motor"]).probar(config)
        except Exception as error:
            ok, mensaje = False, str(error)
        registrar_auditoria(
            "probar_conexion", entidad=config.get("nombre", ""),
            detalle=f"{'Exitosa' if ok else 'Fallida'} ({config.get('motor', '')})",
        )
        return ok, mensaje

    @staticmethod
    def pendientes(config: dict) -> list:
        """Nombres de las migraciones que faltan por ejecutar en esa base."""
        driver = obtener_driver(config.get("motor", ""))
        if hasattr(driver, "asegurar_base_datos"):
            try:
                driver.asegurar_base_datos(config)
            except Exception:
                pass
        conexion = abrir_conexion(config)
        try:
            return [m["nombre"] for m in MigrationService.pendientes(conexion)]
        finally:
            conexion.close()

    @staticmethod
    def migrar(config: dict) -> list:
        """Ejecuta las migraciones pendientes. @return nombres de las ejecutadas."""
        driver = obtener_driver(config.get("motor", ""))
        if hasattr(driver, "asegurar_base_datos"):
            driver.asegurar_base_datos(config)
        conexion = abrir_conexion(config)
        try:
            return MigrationService.ejecutar(conexion)
        finally:
            conexion.close()

    @staticmethod
    def importar_local(config: dict) -> dict:
        conexion = abrir_conexion(config)
        try:
            return ImportacionLocalService.importar(conexion)
        finally:
            conexion.close()

    @staticmethod
    def importar_desde_origen(config_destino: dict, origen: dict) -> dict:
        conexion = abrir_conexion(config_destino)
        try:
            return ImportacionLocalService.importar_desde_origen(conexion, origen)
        finally:
            conexion.close()

    @classmethod
    def activar(cls, nombre: str):
        """
        Marca la conexión como activa. Exige conexión exitosa y migraciones al día,
        porque de lo contrario la aplicación fallaría al leer/escribir.
        """
        config = ConexionConfigModel.obtener(nombre)
        if not config:
            raise ValueError("Guarde la conexión antes de marcarla como activa.")
        ok, mensaje = obtener_driver(config["motor"]).probar(config)
        if not ok:
            raise ValueError(f"No se puede activar: {mensaje}")
        pendientes = cls.pendientes(config)
        if pendientes:
            raise ValueError(f"Ejecute 'Migrar' antes de activarla: hay {len(pendientes)} migración(es) pendiente(s).")
        ConexionConfigModel.establecer_activa(config["nombre"])
        registrar_auditoria("activar_conexion", entidad=config["nombre"], detalle=f"Motor={config['motor']}")

    # ---------------------- Arranque ----------------------
    @classmethod
    def estado_inicial(cls) -> tuple:
        """
        Verifica al iniciar la app que exista una conexión activa operativa y migrada.
        @return (ok, mensaje)
        """
        config = ConexionConfigModel.obtener_activa()
        if not config:
            return False, "No hay una base de datos activa. Configure y active una conexión para continuar."
        ok, mensaje = obtener_driver(config["motor"]).probar(config)
        if not ok:
            return False, f"No se pudo conectar a la base activa '{config['nombre']}': {mensaje}"
        try:
            pendientes = cls.pendientes(config)
        except Exception as error:
            return False, f"No se pudo verificar las migraciones de '{config['nombre']}': {error}"
        if pendientes:
            return False, f"La base activa tiene {len(pendientes)} migración(es) pendiente(s). Ejecute 'Migrar'."
        return True, ""
