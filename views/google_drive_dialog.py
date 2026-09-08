"""
Vista: Diálogo emergente para ingresar el enlace o ID de Google Sheets.
"""

from PyQt5 import QtWidgets, QtCore


class GoogleDriveDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, url_inicial: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Configurar / Cargar Google Drive")
        self.resize(550, 160)

        self._crear_ui()
        if url_inicial:
            self.input_url.setText(url_inicial)

    def _crear_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        lbl_instruccion = QtWidgets.QLabel(
            "Ingrese la URL pública o el ID de la hoja de Google Sheets:"
        )
        lbl_instruccion.setWordWrap(True)

        self.input_url = QtWidgets.QLineEdit()
        self.input_url.setPlaceholderText(
            "Ejemplo: https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        )

        lbl_nota = QtWidgets.QLabel(
            "Nota: El documento en Google Drive debe tener permisos de acceso habilitados:\n"
            "'Cualquier persona con el enlace puede ver'."
        )
        lbl_nota.setStyleSheet("color: #666666; font-size: 11px;")
        lbl_nota.setWordWrap(True)

        botones_layout = QtWidgets.QHBoxLayout()
        btn_cancelar = QtWidgets.QPushButton("Cancelar")
        btn_cargar = QtWidgets.QPushButton("Cargar datos")
        btn_cargar.setDefault(True)

        botones_layout.addStretch()
        botones_layout.addWidget(btn_cancelar)
        botones_layout.addWidget(btn_cargar)

        layout.addWidget(lbl_instruccion)
        layout.addWidget(self.input_url)
        layout.addWidget(lbl_nota)
        layout.addLayout(botones_layout)

        btn_cancelar.clicked.connect(self.reject)
        btn_cargar.clicked.connect(self.accept)

    def get_url_or_id(self) -> str:
        """Devuelve el valor ingresado por el usuario sin espacios al inicio ni al final."""
        return self.input_url.text().strip()
