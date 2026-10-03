"""
Servicio: importación de datos desde orígenes seleccionables (archivo SQLite o conexión existente)
hacia la base de datos destino. Soporta transferir empleados, historial de envíos y configuración SMTP.
"""

import os
import sqlite3

from models.auditoria_model import registrar_auditoria
from models.config_local import abrir_qsettings
from models.config_carga_excel_model import ConfigCargaExcelModel
from models.configuracion_model import ConfiguracionModel
from models.database import RUTA_DB_LEGADA, abrir_conexion
from models.conexion_config_model import ConexionConfigModel
from services.smtp_config_service import SmtpConfigService


class ImportacionLocalService:

    @staticmethod
    def hay_datos_locales() -> bool:
        return os.path.isfile(RUTA_DB_LEGADA)

    @classmethod
    def _abrir_origen(cls, origen: dict):
        tipo = origen.get("tipo", "archivo")
        if tipo == "archivo":
            ruta = origen.get("ruta_archivo", RUTA_DB_LEGADA)
            if not os.path.isfile(ruta):
                raise ValueError(f"No se encontró el archivo de base de datos origen: {ruta}")
            conn = sqlite3.connect(ruta)
            conn.row_factory = sqlite3.Row
            return conn, "sqlite"
        else:
            nombre_conn = origen.get("conexion_nombre", "")
            config = ConexionConfigModel.obtener(nombre_conn)
            if not config:
                raise ValueError(f"No se encontró la conexión origen '{nombre_conn}'.")
            return abrir_conexion(config), config.get("motor", "")

    @classmethod
    def _leer_filas(cls, conexion_origen, tipo_motor: str, nombre_tabla: str) -> list:
        try:
            if tipo_motor == "sqlite" and isinstance(conexion_origen, sqlite3.Connection):
                cur = conexion_origen.execute(f"SELECT * FROM {nombre_tabla}")
                return [dict(f) for f in cur.fetchall()]
            else:
                cur = conexion_origen.execute(f"SELECT * FROM {nombre_tabla}")
                return cur.fetchall()
        except Exception:
            return []

    @classmethod
    def _importar_empleados(cls, conexion_origen, tipo_motor: str, conexion_destino) -> tuple:
        """@return (mapa id_antiguo -> id_nuevo, cantidad_insertados)"""
        mapa_ids = {}
        insertados = 0
        filas = cls._leer_filas(conexion_origen, tipo_motor, "empleados")

        for emp in filas:
            cedula = str(emp.get("cedula", "")).strip()
            if not cedula:
                continue

            existente = conexion_destino.execute(
                "SELECT id FROM empleados WHERE cedula = ?", (cedula,)
            ).fetchone()

            if existente:
                mapa_ids[emp.get("id")] = existente["id"]
                continue

            conexion_destino.execute(
                "INSERT INTO empleados (cedula, nombre, telefono, correo) VALUES (?, ?, ?, ?)",
                (cedula, emp.get("nombre", ""), emp.get("telefono", ""), emp.get("correo", "")),
            )
            nuevo = conexion_destino.execute(
                "SELECT id FROM empleados WHERE cedula = ?", (cedula,)
            ).fetchone()
            if nuevo:
                mapa_ids[emp.get("id")] = nuevo["id"]
            insertados += 1

        conexion_destino.commit()
        return mapa_ids, insertados

    @classmethod
    def _importar_envios(cls, conexion_origen, tipo_motor: str, conexion_destino, mapa_ids: dict) -> int:
        cantidad = 0
        filas = cls._leer_filas(conexion_origen, tipo_motor, "envios")

        for env in filas:
            id_orig = env.get("empleado_id")
            id_dest = mapa_ids.get(id_orig)

            conexion_destino.execute(
                "INSERT INTO envios (empleado_id, cedula, nombre, correo, periodo, monto, asunto, "
                "fecha_envio, estado, detalle, datos_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    id_dest,
                    env.get("cedula", ""),
                    env.get("nombre", ""),
                    env.get("correo", ""),
                    env.get("periodo", ""),
                    env.get("monto", ""),
                    env.get("asunto", ""),
                    env.get("fecha_envio", ""),
                    env.get("estado", ""),
                    env.get("detalle", ""),
                    env.get("datos_json", ""),
                ),
            )
            cantidad += 1

        conexion_destino.commit()
        return cantidad

    @classmethod
    def _importar_smtp(cls, conexion_origen, tipo_motor: str, conexion_destino, origen: dict) -> bool:
        """Copia la configuración SMTP desde la base de datos origen o desde QSettings."""
        # 1. Intentar leer desde tabla configuraciones en la base origen
        filas_cfg = cls._leer_filas(conexion_origen, tipo_motor, "configuraciones")
        dict_cfg = {f.get("clave"): f.get("valor") for f in filas_cfg if f.get("clave")}

        host = dict_cfg.get("smtp.host", "")
        if host:
            SmtpConfigService.guardar(
                host=host,
                port=dict_cfg.get("smtp.port", "587"),
                user=dict_cfg.get("smtp.user", ""),
                password=dict_cfg.get("smtp.password", ""),
                remitente_nombre=dict_cfg.get("smtp.remitente", ""),
                use_tls=dict_cfg.get("smtp.use_tls", "1") == "1",
                conexion=conexion_destino,
            )
            return True

        # 2. Si es archivo local y coincide con nomina.db, verificar si hay en QSettings
        if origen.get("tipo") == "archivo":
            ajustes = abrir_qsettings()
            host_q = ajustes.value("smtp/host", "")
            if host_q:
                SmtpConfigService.guardar(
                    host=host_q,
                    port=ajustes.value("smtp/port", "587"),
                    user=ajustes.value("smtp/user", ""),
                    password=ajustes.value("smtp/password", ""),
                    remitente_nombre=ajustes.value("smtp/remitente", ""),
                    use_tls=ajustes.value("smtp/use_tls", "true") == "true",
                    conexion=conexion_destino,
                )
                return True

        return False

    @classmethod
    def importar_desde_origen(cls, conexion_destino, origen: dict) -> dict:
        """
        Importa datos desde el origen especificado hacia conexion_destino.
        @param origen: dict con 'tipo' ('archivo'/'conexion'), 'ruta_archivo' o 'conexion_nombre',
                       y banderas booleanas 'importar_empleados', 'importar_envios', 'importar_smtp'.
        @return resumen con cantidades de registros importados.
        """
        conexion_origen, tipo_motor = cls._abrir_origen(origen)
        etiqueta_origen = (
            os.path.basename(origen.get("ruta_archivo", "archivo.db"))
            if origen.get("tipo") == "archivo"
            else f"conexion:{origen.get('conexion_nombre')}"
        )

        try:
            empleados_importados = 0
            mapa_ids = {}
            if origen.get("importar_empleados", True):
                mapa_ids, empleados_importados = cls._importar_empleados(conexion_origen, tipo_motor, conexion_destino)

            envios_importados = 0
            if origen.get("importar_envios", True):
                envios_importados = cls._importar_envios(conexion_origen, tipo_motor, conexion_destino, mapa_ids)

            smtp_importado = False
            if origen.get("importar_smtp", True):
                smtp_importado = cls._importar_smtp(conexion_origen, tipo_motor, conexion_destino, origen)

            resumen = {
                "empleados": empleados_importados,
                "envios": envios_importados,
                "smtp": smtp_importado,
                "origen": etiqueta_origen,
            }

            registrar_auditoria(
                "importar_datos",
                entidad=etiqueta_origen,
                detalle=f"empleados={empleados_importados}, envios={envios_importados}, smtp={'si' if smtp_importado else 'no'}",
                conexion=conexion_destino,
            )
            return resumen
        finally:
            try:
                conexion_origen.close()
            except Exception:
                pass

    @classmethod
    def importar(cls, conexion) -> dict:
        """Método de retrocompatibilidad para importar desde el nomina.db por defecto."""
        return cls.importar_desde_origen(
            conexion,
            {
                "tipo": "archivo",
                "ruta_archivo": RUTA_DB_LEGADA,
                "importar_empleados": True,
                "importar_envios": True,
                "importar_smtp": True,
            },
        )
