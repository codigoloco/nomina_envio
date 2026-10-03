"""
Modelo: Configuración de carga de Excel.
Guarda y recupera la última hoja, lista de columnas elegidas y mes seleccionado
para recordarlos la próxima vez que se abra el modal de carga.
Si la base de datos activa está disponible se almacena centralizada; de lo contrario,
hace fallback transparente a QSettings local.
"""

import json
from datetime import datetime

from models.auditoria_model import registrar_auditoria
from models.config_local import abrir_qsettings
from models.database import get_connection

_CLAVE_HOJA_LOCAL = "excel_carga/hoja"
_CLAVE_COLUMNAS_LOCAL = "excel_carga/columnas_json"
_CLAVE_MES_LOCAL = "excel_carga/mes"


class ConfigCargaExcelModel:

    @staticmethod
    def obtener_ultima() -> dict:
        """
        Devuelve dict con {'hoja': str, 'columnas': list, 'mes': str}.
        Si no hay configuración previa, devuelve valores por defecto vacíos.
        """
        try:
            conn = get_connection()
            try:
                fila = conn.execute(
                    "SELECT hoja, columnas_json, mes FROM config_carga_excel ORDER BY id DESC LIMIT 1"
                ).fetchone()
                if fila:
                    columnas = []
                    try:
                        columnas = json.loads(fila["columnas_json"])
                    except Exception:
                        columnas = []
                    return {
                        "hoja": fila["hoja"] or "",
                        "columnas": columnas if isinstance(columnas, list) else [],
                        "mes": fila["mes"] or "",
                    }
            finally:
                conn.close()
        except Exception:
            pass

        # Fallback a QSettings local
        ajustes = abrir_qsettings()
        hoja = ajustes.value(_CLAVE_HOJA_LOCAL, "")
        mes = ajustes.value(_CLAVE_MES_LOCAL, "")
        cols_raw = ajustes.value(_CLAVE_COLUMNAS_LOCAL, "[]")
        columnas = []
        try:
            columnas = json.loads(cols_raw)
        except Exception:
            columnas = []
        return {
            "hoja": str(hoja or ""),
            "columnas": columnas if isinstance(columnas, list) else [],
            "mes": str(mes or ""),
        }

    @staticmethod
    def guardar(hoja: str, columnas: list, mes: str):
        """
        Guarda la configuración de carga activa y registra la auditoría.
        """
        cols_json = json.dumps(columnas, ensure_ascii=False)
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Guardar en base de datos si está disponible
        try:
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO config_carga_excel (hoja, columnas_json, mes, actualizado) VALUES (?, ?, ?, ?)",
                    (hoja.strip(), cols_json, (mes or "").strip(), ahora),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

        # Respaldo en QSettings local
        ajustes = abrir_qsettings()
        ajustes.setValue(_CLAVE_HOJA_LOCAL, hoja.strip())
        ajustes.setValue(_CLAVE_COLUMNAS_LOCAL, cols_json)
        ajustes.setValue(_CLAVE_MES_LOCAL, (mes or "").strip())

        registrar_auditoria(
            "configurar_carga_excel",
            entidad=hoja.strip(),
            detalle=f"mes={mes}, columnas={len(columnas)} seleccionadas",
        )
