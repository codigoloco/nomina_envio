"""
Modelo: Configuraciones centralizadas (clave/valor) guardadas en la base activa.
Aquí vive, por ejemplo, la configuración de correo SMTP.
"""

from datetime import datetime

from models.database import get_connection


class ConfiguracionModel:

    @staticmethod
    def obtener(clave: str, defecto: str = "", conexion=None) -> str:
        propia = conexion is None
        conn = conexion if conexion is not None else get_connection()
        try:
            fila = conn.execute("SELECT valor FROM configuraciones WHERE clave = ?", (clave,)).fetchone()
            return fila["valor"] if fila and fila["valor"] is not None else defecto
        finally:
            if propia:
                conn.close()

    @staticmethod
    def guardar(clave: str, valor: str, conexion=None):
        propia = conexion is None
        conn = conexion if conexion is not None else get_connection()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            existe = conn.execute("SELECT id FROM configuraciones WHERE clave = ?", (clave,)).fetchone()
            if existe:
                conn.execute(
                    "UPDATE configuraciones SET valor = ?, actualizado = ? WHERE clave = ?",
                    (str(valor), ahora, clave),
                )
            else:
                conn.execute(
                    "INSERT INTO configuraciones (clave, valor, actualizado) VALUES (?, ?, ?)",
                    (clave, str(valor), ahora),
                )
            conn.commit()
        finally:
            if propia:
                conn.close()
