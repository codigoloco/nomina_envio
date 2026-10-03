"""
Servicio: ejecución de migraciones.
- Descubre los archivos de la carpeta 'migraciones/' (AAAA_MM_DD_HHMMSS_nombre_funcion.py).
- Las ordena por fecha y SOLO ejecuta las que no estén registradas en la tabla 'migraciones'
  de la base destino. Cada archivo debe tener una función con el mismo nombre del archivo
  (sin la fecha), que recibe un objeto Esquema.
"""

import importlib
import pkgutil
import re

import migraciones as paquete_migraciones
from models.auditoria_model import registrar_auditoria
from models.esquema import Esquema
from models.migracion_model import MigracionModel

_PATRON = re.compile(r"^(\d{4}_\d{2}_\d{2}_\d{6})_(.+)$")


class MigracionError(Exception):
    """Falló una migración; el mensaje indica cuál y por qué."""


class MigrationService:

    @staticmethod
    def listar_archivos() -> list:
        """Todas las migraciones del proyecto, ordenadas por fecha: [{nombre, funcion}]."""
        encontradas = []
        for modulo in pkgutil.iter_modules(paquete_migraciones.__path__):
            coincidencia = _PATRON.match(modulo.name)
            if coincidencia:
                encontradas.append({"nombre": modulo.name, "funcion": coincidencia.group(2)})
        return sorted(encontradas, key=lambda m: m["nombre"])

    @classmethod
    def pendientes(cls, conexion) -> list:
        """Migraciones del proyecto que aún no constan en la tabla 'migraciones'."""
        ejecutadas = MigracionModel.listar_ejecutadas(conexion)
        return [m for m in cls.listar_archivos() if m["nombre"] not in ejecutadas]

    @staticmethod
    def _cargar_funcion(migracion: dict):
        modulo = importlib.import_module(f"{paquete_migraciones.__name__}.{migracion['nombre']}")
        funcion = getattr(modulo, migracion["funcion"], None)
        if not callable(funcion):
            raise MigracionError(
                f"El archivo '{migracion['nombre']}' debe definir la función '{migracion['funcion']}'."
            )
        return funcion

    @classmethod
    def ejecutar(cls, conexion) -> list:
        """
        Ejecuta las migraciones pendientes en la base destino.
        @return lista con los nombres de las migraciones ejecutadas (vacía si no había pendientes).
        """
        MigracionModel.asegurar_tabla(conexion)
        pendientes = cls.pendientes(conexion)
        if not pendientes:
            return []

        lote = MigracionModel.siguiente_lote(conexion)
        ejecutadas = []
        for migracion in pendientes:
            try:
                cls._cargar_funcion(migracion)(Esquema(conexion))
                MigracionModel.registrar(conexion, migracion["nombre"], lote)
            except Exception as error:
                try:
                    conexion.rollback()
                except Exception:
                    pass
                raise MigracionError(f"Falló la migración '{migracion['nombre']}': {error}")
            ejecutadas.append(migracion["nombre"])

        # La tabla 'auditoria' ya existe al terminar; se registra cada migración ejecutada.
        for nombre in ejecutadas:
            registrar_auditoria("migrar", entidad=nombre, detalle=f"Lote {lote}", conexion=conexion)
        return ejecutadas
