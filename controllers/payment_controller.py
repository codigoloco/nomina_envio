"""
Controlador: Pagos.
Orquesta la lectura del Excel (servicio) y la consulta del historial
de envios (modelo). El envio en si se maneja en SendWorker (un
QThread que actua como "controlador en segundo plano").
"""

from services.excel_reader import ExcelReader
from models.envio_model import EnvioModel


class PaymentController:

    @staticmethod
    def cargar_excel_pagos(path):
        """Devuelve la lista de filas (dict) leidas del Excel de pagos."""
        return ExcelReader.read_payments(path)

    @staticmethod
    def obtener_historial(estado_filtro=None, texto_busqueda=None):
        return EnvioModel.get_logs(estado_filtro=estado_filtro, texto_busqueda=texto_busqueda)

