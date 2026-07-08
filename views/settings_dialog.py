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
        self.setWindowTitle("Configuración de correo y formato")
        self.setMinimumWidth(430)

        # Controles SMTP
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

        form_smtp = QtWidgets.QFormLayout()
        form_smtp.addRow("Servidor SMTP (host):", self.host_edit)
        form_smtp.addRow("Puerto:", self.port_edit)
        form_smtp.addRow("Usuario / correo:", self.user_edit)
        form_smtp.addRow("Contraseña / clave de app:", self.password_edit)
        form_smtp.addRow("Nombre del remitente:", self.remitente_edit)
        form_smtp.addRow(self.tls_check)

        # Controles Formato de Moneda
        self.moneda_group = QtWidgets.QGroupBox("Formato de Moneda / Montos en Bs.")
        form_moneda = QtWidgets.QFormLayout(self.moneda_group)
        
        self.mask_edit = QtWidgets.QLineEdit()
        self.mask_edit.setToolTip("Usa {monto} donde quieres que aparezca el numero. Ej. Bs. {monto}")
        self.thousands_edit = QtWidgets.QLineEdit()
        self.thousands_edit.setMaxLength(1)
        self.thousands_edit.setFixedWidth(50)
        self.decimal_edit = QtWidgets.QLineEdit()
        self.decimal_edit.setMaxLength(1)
        self.decimal_edit.setFixedWidth(50)

        form_moneda.addRow("Máscara del monto:", self.mask_edit)
        form_moneda.addRow("Separador de miles:", self.thousands_edit)
        form_moneda.addRow("Separador de decimales:", self.decimal_edit)

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
        layout.addLayout(form_smtp)
        layout.addWidget(self.moneda_group)
        layout.addWidget(nota)
        layout.addWidget(botones)

        self.cargar()

    def cargar(self):
        # SMTP
        config = SettingsController.get_smtp_config()
        self.host_edit.setText(config["host"])
        self.port_edit.setText(config["port"])
        self.user_edit.setText(config["user"])
        self.password_edit.setText(config["password"])
        self.remitente_edit.setText(config["remitente_nombre"])
        self.tls_check.setChecked(config["use_tls"])

        # Moneda
        moneda = SettingsController.get_currency_config()
        self.mask_edit.setText(moneda["mask"])
        self.thousands_edit.setText(moneda["thousands_sep"])
        self.decimal_edit.setText(moneda["decimal_sep"])

    def guardar(self):
        if not self.host_edit.text().strip() or not self.user_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Datos incompletos", "Host y usuario son obligatorios.")
            return

        mask = self.mask_edit.text().strip()
        if "{monto}" not in mask:
            QtWidgets.QMessageBox.warning(
                self, "Máscara inválida", "La máscara de monto debe incluir el marcador '{monto}'."
            )
            return

        # SMTP
        SettingsController.save_smtp_config(
            host=self.host_edit.text().strip(),
            port=self.port_edit.text().strip(),
            user=self.user_edit.text().strip(),
            password=self.password_edit.text(),
            remitente_nombre=self.remitente_edit.text().strip(),
            use_tls=self.tls_check.isChecked(),
        )

        # Moneda
        SettingsController.save_currency_config(
            mask=mask,
            thousands_sep=self.thousands_edit.text(),
            decimal_sep=self.decimal_edit.text()
        )
        self.accept()

