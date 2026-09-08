"""
Servicio: integración con Google Drive / Google Sheets.
Permite extraer el ID de una hoja de cálculo y descargarla como archivo CSV/XLSX temporal.
No modifica datos; solo descarga para lectura.
"""

import re
import tempfile
import urllib.request
import urllib.error


class GoogleDriveService:

    PATRON_SHEET_ID = r"/d/([a-zA-Z0-9-_]+)"

    @classmethod
    def extraer_sheet_id(cls, url_o_id: str) -> str:
        """
        Extrae el ID de una hoja de Google Sheets a partir de una URL completa o un ID directo.
        @param url_o_id URL de Google Sheets o ID del documento
        @return ID limpio de la hoja de cálculo
        """
        cadena = url_o_id.strip()
        if not cadena:
            raise ValueError("El enlace o ID de Google Sheets no puede estar vacío.")

        coincidencia = re.search(cls.PATRON_SHEET_ID, cadena)
        if coincidencia:
            return coincidencia.group(1)

        if re.match(r"^[a-zA-Z0-9-_]{20,}$", cadena):
            return cadena

        raise ValueError(
            "El enlace o ID proporcionado no tiene un formato válido de Google Sheets.\n"
            "Ejemplo de enlace válido: https://docs.google.com/spreadsheets/d/1ABC.../edit"
        )

    @classmethod
    def descargar_sheet_como_excel(cls, url_o_id: str) -> str:
        """
        Descarga el libro de Google Sheets como un archivo .xlsx temporal.
        @param url_o_id URL o ID del Google Sheet
        @return Ruta absoluta del archivo .xlsx temporal descargado
        """
        sheet_id = cls.extraer_sheet_id(url_o_id)
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

        req = urllib.request.Request(
            export_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0.0.0 Safari/537.36"
                )
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise ValueError(f"Error al acceder a Google Sheets. Código de estado: {response.status}")

                contenido = response.read()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                temp_file.write(contenido)
                temp_file.close()
                return temp_file.name

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(
                    "No se encontró la hoja de Google Sheets (Error 404).\n"
                    "Verifica que el enlace sea correcto y que el documento exista."
                )
            elif e.code in (401, 403):
                raise ValueError(
                    "Acceso denegado a la hoja de Google Sheets.\n"
                    "Asegúrate de que el documento tenga activada la opción:\n"
                    "'Cualquier persona con el enlace puede ver'."
                )
            else:
                raise ValueError(f"Error al descargar la hoja de Google Sheets (HTTP {e.code}): {e.reason}")
        except urllib.error.URLError as e:
            raise ValueError(f"Error de conexión al intentar acceder a Google Sheets:\n{e.reason}")
        except Exception as e:
            raise ValueError(f"No se pudo descargar la hoja de Google Sheets:\n{str(e)}")

    @classmethod
    def descargar_hoja_como_csv(cls, url_o_id: str, nombre_hoja: str) -> str:
        """
        Descarga una hoja específica de Google Sheets como archivo CSV temporal.
        El CSV incluye los valores renderizados de Tablas Dinámicas (Pivot Tables).
        @param url_o_id URL o ID del Google Sheet
        @param nombre_hoja Nombre exacto de la pestaña (ej: 'Pagos a encargados')
        @return Ruta absoluta del archivo .csv temporal descargado
        """
        sheet_id = cls.extraer_sheet_id(url_o_id)
        nombre_codificado = urllib.request.quote(nombre_hoja)
        export_url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            f"/gviz/tq?tqx=out:csv&sheet={nombre_codificado}"
        )

        req = urllib.request.Request(
            export_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0.0.0 Safari/537.36"
                )
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise ValueError(f"Error al exportar la hoja como CSV. Codigo: {response.status}")

                contenido = response.read()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                temp_file.write(contenido)
                temp_file.close()
                return temp_file.name

        except urllib.error.HTTPError as e:
            raise ValueError(f"Error HTTP {e.code} al exportar la hoja '{nombre_hoja}' como CSV: {e.reason}")
        except urllib.error.URLError as e:
            raise ValueError(f"Error de conexion al exportar CSV: {e.reason}")
        except Exception as e:
            raise ValueError(f"No se pudo exportar la hoja '{nombre_hoja}' como CSV: {str(e)}")
