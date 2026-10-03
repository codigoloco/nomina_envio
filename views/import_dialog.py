"""
Diálogo para seleccionar el origen de importación de datos.
Permite elegir entre un archivo SQLite local (.db / .sqlite) o
una conexión de base de datos ya registrada en el sistema,
así como seleccionar qué entidades importar (empleados, envíos, SMTP).
"""

import os
from PyQt5 import QtCore, QtWidgets
from models.database import RUTA_DB_LEGADA


class ImportSourceDialog(QtWidgets.QDialog):

    def __init__(self, conexiones_guardadas: list = None, conexion_actual_nombre: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar origen de importación")
        self.resize(480, 320)
        self.setModal(True)

        self._conexiones = [
            c for c in (conexiones_guardadas or [])
            if c.get("nombre") != conexion_actual_nombre
        ]

        self._crear_widgets()
        self._armar_layout()
        self._conectar_senales()
        self._actualizar_visibilidad()

    def _crear_widgets(self):
        # Grupo de origen
        self.grupo_origen = QtWidgets.QGroupBox("Origen de los datos")

        self.radio_archivo = QtWidgets.QRadioButton("Archivo SQLite local (.db / .sqlite)")
        self.radio_archivo.setChecked(True)

        self.radio_conexion = QtWidgets.QRadioButton("Desde otra conexión guardada")
        if not self._conexiones:
            self.radio_conexion.setEnabled(False)
            self.radio_conexion.setText("Desde otra conexión guardada (sin otras conexiones)")

        # Controles para archivo
        self.ruta_edit = QtWidgets.QLineEdit()
        if os.path.isfile(RUTA_DB_LEGADA):
            self.ruta_edit.setText(os.path.abspath(RUTA_DB_LEGADA))
        else:
            self.ruta_edit.setPlaceholderText("Seleccione un archivo de base de datos...")
        self.btn_examinar = QtWidgets.QPushButton("Examinar...")

        # Controles para conexión
        self.conexion_combo = QtWidgets.QComboBox()
        for c in self._conexiones:
            motor_tag = c.get("motor", "").upper()
            self.conexion_combo.addItem(f"{c['nombre']} ({motor_tag})", c["nombre"])

        # Grupo de datos a importar
        self.grupo_datos = QtWidgets.QGroupBox("Datos a importar")
        self.chk_empleados = QtWidgets.QCheckBox("Empleados (evita duplicar cédulas existentes)")
        self.chk_empleados.setChecked(True)

        self.chk_envios = QtWidgets.QCheckBox("Historial de envíos de recibos")
        self.chk_envios.setChecked(True)

        self.chk_smtp = QtWidgets.QCheckBox("Configuración del servidor de correo SMTP")
        self.chk_smtp.setChecked(True)

        # Botones de acción
        self.btn_importar = QtWidgets.QPushButton("Iniciar importación")
        self.btn_importar.setDefault(True)
        self.btn_cancelar = QtWidgets.QPushButton("Cancelar")

    def _armar_layout(self):
        layout_archivo = QtWidgets.QHBoxLayout()
        layout_archivo.addWidget(self.ruta_edit)
        layout_archivo.addWidget(self.btn_examinar)

        layout_origen = QtWidgets.QVBoxLayout()
        layout_origen.addWidget(self.radio_archivo)
        layout_origen.addLayout(layout_archivo)
        layout_origen.addSpacing(6)
        layout_origen.addWidget(self.radio_conexion)
        layout_origen.addWidget(self.conexion_combo)
        self.grupo_origen.setLayout(layout_origen)

        layout_datos = QtWidgets.QVBoxLayout()
        layout_datos.addWidget(self.chk_empleados)
        layout_datos.addWidget(self.chk_envios)
        layout_datos.addWidget(self.chk_smtp)
        self.grupo_datos.setLayout(layout_datos)

        layout_botones = QtWidgets.QHBoxLayout()
        layout_botones.addStretch()
        layout_botones.addWidget(self.btn_importar)
        layout_botones.addWidget(self.btn_cancelar)

        principal = QtWidgets.QVBoxLayout(self)
        principal.addWidget(self.grupo_origen)
        principal.addWidget(self.grupo_datos)
        principal.addStretch()
        principal.addLayout(layout_botones)

    def _conectar_senales(self):
        self.radio_archivo.toggled.connect(self._actualizar_visibilidad)
        self.radio_conexion.toggled.connect(self._actualizar_visibilidad)
        self.btn_examinar.clicked.connect(self._examinar_archivo)
        self.btn_importar.clicked.connect(self._validar_y_aceptar)
        self.btn_cancelar.clicked.connect(self.reject)

    def _actualizar_visibilidad(self):
        es_archivo = self.radio_archivo.isChecked()
        self.ruta_edit.setEnabled(es_archivo)
        self.btn_examinar.setEnabled(es_archivo)
        self.conexion_combo.setEnabled(not es_archivo and bool(self._conexiones))

    def _examinar_archivo(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Seleccionar base de datos SQLite origen",
            self.ruta_edit.text() or ".",
            "Bases de datos SQLite (*.db *.sqlite *.sqlite3);;Todos los archivos (*.*)",
        )
        if ruta:
            self.ruta_edit.setText(ruta)

    def _validar_y_aceptar(self):
        if self.radio_archivo.isChecked():
            ruta = self.ruta_edit.text().strip()
            if not ruta or not os.path.isfile(ruta):
                QtWidgets.QMessageBox.warning(
                    self, "Archivo requerido",
                    "Debe seleccionar un archivo de base de datos existente."
                )
                return
        else:
            if not self.conexion_combo.currentData():
                QtWidgets.QMessageBox.warning(
                    self, "Conexión requerida",
                    "Debe seleccionar una conexión de origen válida."
                )
                return

        if not (self.chk_empleados.isChecked() or self.chk_envios.isChecked() or self.chk_smtp.isChecked()):
            QtWidgets.QMessageBox.warning(
                self, "Selección requerida",
                "Debe marcar al menos un tipo de dato a importar (Empleados, Envíos o SMTP)."
            )
            return

        self.accept()

    def obtener_datos_origen(self) -> dict:
        es_archivo = self.radio_archivo.isChecked()
        return {
            "tipo": "archivo" if es_archivo else "conexion",
            "ruta_archivo": self.ruta_edit.text().strip() if es_archivo else "",
            "conexion_nombre": self.conexion_combo.currentData() if not es_archivo else "",
            "importar_empleados": self.chk_empleados.isChecked(),
            "importar_envios": self.chk_envios.isChecked(),
            "importar_smtp": self.chk_smtp.isChecked(),
        }
