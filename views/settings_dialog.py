"""
Vista: configuración del servidor SMTP.
El almacenamiento real (QSettings) vive en SettingsController; esta
clase solo construye el formulario y delega guardar/cargar al controlador.
"""

from PyQt5 import QtWidgets

from controllers.settings_controller import SettingsController


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de correo SMTP")
        self.setMinimumWidth(400)

        self.host_edit = QtWidgets.QLineEdit()
        self.host_edit.setPlaceholderText("smtp.gmail.com")
        self.port_edit = QtWidgets.QLineEdit()
        self.port_edit.setPlaceholderText("587")
        self.user_edit = QtWidgets.QLineEdit()
        self.user_edit.setPlaceholderText("nomina@miempresa.com")
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.remitente_edit = QtWidgets.QLineEdit()
        self.remitente_edit.setPlaceholderText("Departamento de Nómina")
        self.tls_check = QtWidgets.QCheckBox("Usar STARTTLS (recomendado con el puerto 587)")
        self.tls_check.setChecked(True)

        form = QtWidgets.QFormLayout()
        form.addRow("Servidor SMTP (host):", self.host_edit)
        form.addRow("Puerto:", self.port_edit)
        form.addRow("Usuario / correo:", self.user_edit)
        form.addRow("Contraseña / clave de app:", self.password_edit)
        form.addRow("Nombre del remitente:", self.remitente_edit)
        form.addRow(self.tls_check)

        nota = QtWidgets.QLabel(
            "Sugerencia: con Gmail usa el puerto 587 (TLS) o 465 (SSL) y una\n"
            "'contraseña de aplicación' generada desde la cuenta de Google."
        )
        nota.setStyleSheet("color:#777;font-size:11px;")

        botones = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        botones.accepted.connect(self.guardar)
        botones.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(nota)
        layout.addWidget(botones)

        self.cargar()

    def cargar(self):
        config = SettingsController.get_smtp_config()
        self.host_edit.setText(config["host"])
        self.port_edit.setText(config["port"])
        self.user_edit.setText(config["user"])
        self.password_edit.setText(config["password"])
        self.remitente_edit.setText(config["remitente_nombre"])
        self.tls_check.setChecked(config["use_tls"])

    def guardar(self):
        if not self.host_edit.text().strip() or not self.user_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Datos incompletos", "Host y usuario son obligatorios.")
            return
        SettingsController.save_smtp_config(
            host=self.host_edit.text().strip(),
            port=self.port_edit.text().strip(),
            user=self.user_edit.text().strip(),
            password=self.password_edit.text(),
            remitente_nombre=self.remitente_edit.text().strip(),
            use_tls=self.tls_check.isChecked(),
        )
        self.accept()
