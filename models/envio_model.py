"""
Modelo: Envío (log de cada correo enviado, exitoso o con error).
Encapsula el SQL relacionado con la tabla 'envios'.
"""

from datetime import datetime
from models.database import get_connection


class EnvioModel:

    @staticmethod
    def add_log(empleado_id, cedula, nombre, correo, periodo, monto, asunto, estado, detalle, datos_json=None):
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO envios
                    (empleado_id, cedula, nombre, correo, periodo, monto, asunto, fecha_envio, estado, detalle, datos_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                empleado_id, cedula, nombre, correo, periodo, str(monto), asunto,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), estado, detalle, datos_json
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

    @staticmethod
    def get_latest_recipients():
        """
        Obtiene los destinatarios únicos del último lote de envíos registrado en la tabla 'envios'.
        Un lote se define como los registros enviados dentro de una ventana de tiempo
        cercana al último envío registrado (últimos 30 minutos desde el último envío).
        Si no hay registros suficientes, toma los más recientes evitando duplicados.
        """
        conn = get_connection()
        try:
            row = conn.execute("SELECT MAX(fecha_envio) AS max_fecha FROM envios").fetchone()
            if not row or not row["max_fecha"]:
                return []
            max_fecha_str = row["max_fecha"]

            from datetime import datetime, timedelta
            try:
                max_dt = datetime.strptime(max_fecha_str, "%Y-%m-%d %H:%M:%S")
                ventana_inicio = (max_dt - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                rows = conn.execute("""
                    SELECT empleado_id, cedula, nombre, correo, MAX(fecha_envio) as fecha_envio
                    FROM envios
                    WHERE fecha_envio >= ? AND correo IS NOT NULL AND TRIM(correo) != ''
                    GROUP BY LOWER(TRIM(correo))
                    ORDER BY id ASC
                """, (ventana_inicio,)).fetchall()
                if rows:
                    return [dict(r) for r in rows]
            except Exception:
                pass

            # Respaldo en caso de formato o ventana vacía
            rows = conn.execute("""
                SELECT empleado_id, cedula, nombre, correo, MAX(fecha_envio) as fecha_envio
                FROM envios
                WHERE correo IS NOT NULL AND TRIM(correo) != ''
                GROUP BY LOWER(TRIM(correo))
                ORDER BY id DESC
                LIMIT 50
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

