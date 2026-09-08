"""
Controlador/Worker: Hilo en segundo plano para la carga de datos (Excel o Google Drive).
Mantiene la interfaz respondiendo y emite eventos de progreso (porcentaje y mensajes)
para actualizar la barra de progreso y el spinner en la vista.
"""

import time
from PyQt5 import QtCore
from controllers.payment_controller import PaymentController


class DataLoaderWorker(QtCore.QThread):

    # Señales: (porcentaje, mensaje)
    sig_progreso = QtCore.pyqtSignal(int, str)
    sig_exito = QtCore.pyqtSignal(list)
    sig_error = QtCore.pyqtSignal(str)

    def __init__(self, tipo_fuente: str, fuente: str, parent=None):
        """
        @param tipo_fuente: 'drive' o 'excel'
        @param fuente: URL/ID de Google Sheets o ruta absoluta del archivo .xlsx
        """
        super().__init__(parent)
        self.tipo_fuente = tipo_fuente
        self.fuente = fuente

    def run(self):
        try:
            if self.tipo_fuente == "drive":
                self.sig_progreso.emit(15, "Iniciando conexión con Google Drive...")
                time.sleep(0.2)

                self.sig_progreso.emit(35, "Exportando hoja 'Pagos a encargados' (CSV renderizado)...")
                filas = PaymentController.cargar_drive_pagos(self.fuente)

            else:
                self.sig_progreso.emit(25, "Abriendo archivo Excel local...")
                time.sleep(0.2)

                self.sig_progreso.emit(50, "Extrayendo matriz de datos A2:N...")
                filas = PaymentController.cargar_excel_pagos(self.fuente)

            self.sig_progreso.emit(85, "Filtrando totalizadores y organizando columnas...")
            time.sleep(0.2)

            self.sig_progreso.emit(100, "¡Carga finalizada con éxito!")
            time.sleep(0.1)

            self.sig_exito.emit(filas)

        except Exception as e:
            self.sig_error.emit(str(e))
