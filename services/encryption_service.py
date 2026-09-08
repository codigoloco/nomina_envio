"""
Servicio: cifrado y descifrado de datos sensibles (URLs, credenciales).
Utiliza transformación XOR con clave secreta y codificación Base64
para evitar que la información quede almacenada en texto plano.
"""

import base64

# Clave secreta interna para cifrado de la aplicación
_SECRET_KEY = b"NominaApp_Drive_Security_Key_2026_Vzla"


class EncryptionService:

    @classmethod
    def encriptar(cls, texto: str) -> str:
        """
        Cifra una cadena de texto y devuelve el resultado en Base64.
        @param texto Cadena en texto plano
        @return Cadena cifrada en Base64
        """
        if not texto:
            return ""
        datos = texto.encode("utf-8")
        cifrado = bytes([b ^ _SECRET_KEY[i % len(_SECRET_KEY)] for i, b in enumerate(datos)])
        return base64.b64encode(cifrado).decode("utf-8")

    @classmethod
    def desencriptar(cls, texto_cifrado: str) -> str:
        """
        Descifra una cadena en Base64 cifrada previamente.
        @param texto_cifrado Cadena cifrada en Base64
        @return Cadena descifrada en texto plano
        """
        if not texto_cifrado:
            return ""
        try:
            raw_bytes = base64.b64decode(texto_cifrado.encode("utf-8"))
            descifrado = bytes([b ^ _SECRET_KEY[i % len(_SECRET_KEY)] for i, b in enumerate(raw_bytes)])
            return descifrado.decode("utf-8")
        except Exception:
            return ""
