"""
Servicio: configuración SMTP centralizada en la base de datos activa.
La contraseña se guarda cifrada (EncryptionService), nunca en texto plano.
"""

from models.configuracion_model import ConfiguracionModel
from services.encryption_service import EncryptionService

_PREFIJO = "smtp."


class SmtpConfigService:

    @staticmethod
    def obtener(conexion=None) -> dict:
        def leer(clave, defecto=""):
            return ConfiguracionModel.obtener(_PREFIJO + clave, defecto, conexion=conexion)

        return {
            "host": leer("host"),
            "port": leer("port", "587"),
            "user": leer("user"),
            "password": EncryptionService.desencriptar(leer("password_enc")),
            "remitente_nombre": leer("remitente"),
            "use_tls": leer("use_tls", "true") == "true",
            "correo_pruebas_recepcion": leer("correo_pruebas_recepcion"),
        }

    @staticmethod
    def guardar(host, port, user, password, remitente_nombre, use_tls, correo_pruebas_recepcion="", conexion=None):
        def escribir(clave, valor):
            ConfiguracionModel.guardar(_PREFIJO + clave, valor, conexion=conexion)

        escribir("host", host)
        escribir("port", port or "587")
        escribir("user", user)
        escribir("password_enc", EncryptionService.encriptar(password))
        escribir("remitente", remitente_nombre)
        escribir("use_tls", "true" if use_tls else "false")
        escribir("correo_pruebas_recepcion", correo_pruebas_recepcion or "")
