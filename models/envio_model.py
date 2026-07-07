"""
Modelo: Envío (log de cada correo enviado, exitoso o con error).
Encapsula el SQL relacionado con la tabla 'envios'.
"""

from datetime import datetime
from models.database import get_connection


class EnvioModel:

    @staticmethod
    def add_log(empleado_id, cedula, nombre, correo, periodo, monto, asunto, estado, detalle):
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO envios
                    (empleado_id, cedula, nombre, correo, periodo, monto, asunto, fecha_envio, estado, detalle)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                empleado_id, cedula, nombre, correo, periodo, str(monto), asunto,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), estado, detalle
            ))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_logs(estado_filtro=None, texto_busqueda=None):
        conn = get_connection()
        try:
            query = "SELECT * FROM envios WHERE 1=1"
            params = []
            if estado_filtro and estado_filtro != "Todos":
                query += " AND estado = ?"
                params.append(estado_filtro)
            if texto_busqueda:
                query += " AND (cedula LIKE ? OR nombre LIKE ? OR correo LIKE ?)"
                like = f"%{texto_busqueda}%"
                params += [like, like, like]
            query += " ORDER BY id DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
