"""
Modelo: Auditoría.
Toda funcionalidad, cambio de estatus, operación transaccional o acción de usuario
debe registrarse llamando a registrar_auditoria().
Nunca debe romper el flujo principal: si no hay base disponible, devuelve False.
"""

import getpass
from datetime import datetime

from models.database import get_connection


class AuditoriaModel:

    @staticmethod
    def registrar(accion, entidad, detalle, usuario, conexion=None):
        propia = conexion is None
        conn = conexion if conexion is not None else get_connection()
        try:
            conn.execute(
                "INSERT INTO auditoria (fecha, usuario, accion, entidad, detalle) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, accion, entidad, detalle),
            )
            conn.commit()
        finally:
            if propia:
                conn.close()

    @staticmethod
    def listar(limite=200):
        conn = get_connection()
        try:
            filas = conn.execute("SELECT * FROM auditoria ORDER BY id DESC").fetchall()
            return filas[:limite]
        finally:
            conn.close()


def registrar_auditoria(accion: str, entidad: str = "", detalle: str = "", usuario: str = None, conexion=None) -> bool:
    """
    Registra una acción en la tabla 'auditoria' de la base activa (o de 'conexion' si se indica).
    @param accion   Qué ocurrió (ej. 'probar_conexion', 'migrar', 'configuracion_smtp').
    @param entidad  Sobre qué ocurrió (ej. nombre de la conexión, tabla, archivo).
    @param detalle  Información adicional (nunca incluir contraseñas).
    @param usuario  Usuario que ejecuta la acción; por defecto el usuario de Windows.
    @param conexion Conexión ya abierta donde registrar (por defecto la base activa).
    @return True si se registró, False si no había base disponible o la tabla aún no existe.
    """
    try:
        AuditoriaModel.registrar(
            accion=accion,
            entidad=entidad,
            detalle=detalle,
            usuario=usuario or getpass.getuser(),
            conexion=conexion,
        )
        return True
    except Exception:
        return False
