"""
Vista: Diálogo de carga con spinner y porcentaje de progreso.
Muestra información visual en tiempo real durante la lectura de archivos
o descarga de Google Drive.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from controllers.loader_worker import DataLoaderWorker


class LoadingDialog(QtWidgets.QDialog):

    def __init__(self, tipo_fuente: str, fuente: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Procesando datos")
        self.setFixedSize(420, 220)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        self.setModal(True)

        self.resultado_filas = None
        self.error_mensaje = None

        self._crear_ui()

        # Iniciar el hilo de carga en segundo plano
        self.worker = DataLoaderWorker(tipo_fuente, fuente, parent=self)
        self.worker.sig_progreso.connect(self._actualizar_progreso)
        self.worker.sig_exito.connect(self._on_exito)
        self.worker.sig_error.connect(self._on_error)
        self.worker.start()

    def _crear_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Contenedor superior con ícono/spinner y porcentaje
        header_layout = QtWidgets.QHBoxLayout()
        
        self.lbl_icono = QtWidgets.QLabel("⏳")
        self.lbl_icono.setFont(QtGui.QFont("Segoe UI Emoji", 24))
        
        self.lbl_titulo = QtWidgets.QLabel("Cargando información...")
        self.lbl_titulo.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))

        self.lbl_porcentaje = QtWidgets.QLabel("0%")
        self.lbl_porcentaje.setFont(QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold))
        self.lbl_porcentaje.setStyleSheet("color: #2b5797;")

        header_layout.addWidget(self.lbl_icono)
        header_layout.addWidget(self.lbl_titulo)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_porcentaje)

        # Mensaje de estado dinámico
        self.lbl_estado = QtWidgets.QLabel("Iniciando proceso...")
        self.lbl_estado.setFont(QtGui.QFont("Segoe UI", 9))
        self.lbl_estado.setStyleSheet("color: #555555;")
        self.lbl_estado.setWordWrap(True)

        # Barra de progreso estilizada
        self.barra_progreso = QtWidgets.QProgressBar()
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.setFixedHeight(12)
        self.barra_progreso.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 6px;
                background-color: #e6e6e6;
            }
            QProgressBar::chunk {
                background-color: #2b5797;
                border-radius: 5px;
            }
        """)

        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_estado)
        layout.addWidget(self.barra_progreso)
        layout.addStretch()

    @QtCore.pyqtSlot(int, str)
    def _actualizar_progreso(self, porcentaje: int, mensaje: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_porcentaje.setText(f"{porcentaje}%")
        self.lbl_estado.setText(mensaje)

    @QtCore.pyqtSlot(list)
    def _on_exito(self, filas: list):
        self.resultado_filas = filas
        self.accept()

    @QtCore.pyqtSlot(str)
    def _on_error(self, mensaje_error: str):
        self.error_mensaje = mensaje_error
        self.reject()
