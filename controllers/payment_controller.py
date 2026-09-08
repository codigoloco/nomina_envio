"""
Controlador: Pagos.
Orquesta la lectura del Excel (servicio) y la consulta del historial
de envios (modelo). El envio en si se maneja en SendWorker (un
QThread que actua como "controlador en segundo plano").
"""

from services.excel_reader import ExcelReader
from services.google_drive_service import GoogleDriveService
from models.envio_model import EnvioModel


class PaymentController:

    @staticmethod
    def cargar_excel_pagos(path):
        """Devuelve la lista de filas (dict) leidas del Excel de pagos."""
        return ExcelReader.read_payments(path)

    @staticmethod
    def cargar_drive_pagos(url_o_id):
        """
        Exporta la hoja 'Pagos a encargados' como CSV desde Google Sheets
        (para obtener valores renderizados de la Tabla Dinamica) y devuelve
        la lista de filas procesadas. Solo lectura; no modifica el documento.
        """
        from services.excel_reader import HOJA_PAGOS_ENCARGADOS
        temp_csv = GoogleDriveService.descargar_hoja_como_csv(url_o_id, HOJA_PAGOS_ENCARGADOS)
        return ExcelReader.read_payments_from_csv(temp_csv)

    @staticmethod
    def obtener_historial(estado_filtro=None, texto_busqueda=None):
        return EnvioModel.get_logs(estado_filtro=estado_filtro, texto_busqueda=texto_busqueda)


