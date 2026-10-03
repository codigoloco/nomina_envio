"""
Modelo: conexiones a bases de datos configuradas por el usuario.
Se guardan LOCALMENTE (QSettings) porque la base de datos no puede contener
los datos necesarios para conectarse a sí misma. La contraseña se almacena cifrada.
"""

import json

from models.config_local import abrir_qsettings
from services.encryption_service import EncryptionService

_CLAVE_CONEXIONES = "db/conexiones"
_CLAVE_ACTIVA = "db/activa"


class ConexionConfigModel:

    @staticmethod
    def _leer_crudo() -> list:
        texto = abrir_qsettings().value(_CLAVE_CONEXIONES, "[]")
        try:
            lista = json.loads(texto)
            return lista if isinstance(lista, list) else []
        except Exception:
            return []

    @staticmethod
    def _escribir_crudo(lista: list):
        abrir_qsettings().setValue(_CLAVE_CONEXIONES, json.dumps(lista, ensure_ascii=False))

    @staticmethod
    def _a_config(crudo: dict) -> dict:
        """Convierte el registro guardado (con clave cifrada) en un dict de trabajo."""
        return {
            "nombre": crudo.get("nombre", ""),
            "motor": crudo.get("motor", ""),
            "host": crudo.get("host", ""),
            "puerto": crudo.get("puerto", ""),
            "base_datos": crudo.get("base_datos", ""),
            "usuario": crudo.get("usuario", ""),
            "password": EncryptionService.desencriptar(crudo.get("password_enc", "")),
        }

    @staticmethod
    def listar() -> list:
        return [ConexionConfigModel._a_config(c) for c in ConexionConfigModel._leer_crudo()]

    @staticmethod
    def obtener(nombre: str):
        buscado = str(nombre).strip().lower()
        for config in ConexionConfigModel.listar():
            if config["nombre"].strip().lower() == buscado:
                return config
        return None

    @staticmethod
    def guardar(config: dict, nombre_original: str = None):
        """
        Inserta o reemplaza una conexión. Si nombre_original se indica, se reemplaza
        esa entrada (permite renombrar). Si la conexión era la activa, sigue activa.
        """
        crudo_nuevo = {
            "nombre": config["nombre"].strip(),
            "motor": config["motor"],
            "host": config.get("host", "").strip(),
            "puerto": str(config.get("puerto", "")).strip(),
            "base_datos": config.get("base_datos", "").strip(),
            "usuario": config.get("usuario", "").strip(),
            "password_enc": EncryptionService.encriptar(config.get("password", "")),
        }
        referencia = (nombre_original or crudo_nuevo["nombre"]).strip().lower()
        lista = ConexionConfigModel._leer_crudo()

        # Evitar nombres duplicados distintos a la entrada que se edita
        for existente in lista:
            nombre_existente = existente.get("nombre", "").strip().lower()
            if nombre_existente == crudo_nuevo["nombre"].lower() and nombre_existente != referencia:
                raise ValueError(f"Ya existe una conexión llamada '{crudo_nuevo['nombre']}'.")

        reemplazada = False
        for i, existente in enumerate(lista):
            if existente.get("nombre", "").strip().lower() == referencia:
                lista[i] = crudo_nuevo
                reemplazada = True
                break
        if not reemplazada:
            lista.append(crudo_nuevo)
        ConexionConfigModel._escribir_crudo(lista)

        activa = ConexionConfigModel.nombre_activa()
        if activa and activa.strip().lower() == referencia:
            abrir_qsettings().setValue(_CLAVE_ACTIVA, crudo_nuevo["nombre"])

    @staticmethod
    def eliminar(nombre: str):
        buscado = str(nombre).strip().lower()
        lista = [c for c in ConexionConfigModel._leer_crudo() if c.get("nombre", "").strip().lower() != buscado]
        ConexionConfigModel._escribir_crudo(lista)
        activa = ConexionConfigModel.nombre_activa()
        if activa and activa.strip().lower() == buscado:
            abrir_qsettings().remove(_CLAVE_ACTIVA)

    @staticmethod
    def nombre_activa() -> str:
        return abrir_qsettings().value(_CLAVE_ACTIVA, "") or ""

    @staticmethod
    def establecer_activa(nombre: str):
        abrir_qsettings().setValue(_CLAVE_ACTIVA, nombre)

    @staticmethod
    def obtener_activa():
        nombre = ConexionConfigModel.nombre_activa()
        return ConexionConfigModel.obtener(nombre) if nombre else None
