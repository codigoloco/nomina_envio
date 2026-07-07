"""
Vista: formulario de alta/edición de empleado.
Solo construye el formulario y valida datos de entrada; el guardado real
lo hace el controlador (EmployeeController), invocado desde main_window.
"""

import re
from PyQt5 import QtWidgets

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmployeeDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, empleado=None):
        super().__init__(parent)
        self.empleado = empleado
        self.setWindowTitle("Editar empleado" if empleado else "Nuevo empleado")
        self.setMinimumWidth(350)

        self.cedula_edit = QtWidgets.QLineEdit()
        self.nombre_edit = QtWidgets.QLineEdit()
        self.telefono_edit = QtWidgets.QLineEdit()
        self.correo_edit = QtWidgets.QLineEdit()

        form = QtWidgets.QFormLayout()
        form.addRow("Cédula:", self.cedula_edit)
        form.addRow("Nombre completo:", self.nombre_edit)
        form.addRow("Teléfono:", self.telefono_edit)
        form.addRow("Correo:", self.correo_edit)

        botones = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        botones.accepted.connect(self.validar_y_aceptar)
        botones.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(botones)

        if empleado:
            self.cedula_edit.setText(empleado["cedula"])
            self.nombre_edit.setText(empleado["nombre"])
            self.telefono_edit.setText(empleado.get("telefono") or "")
            self.correo_edit.setText(empleado["correo"])

    def validar_y_aceptar(self):
        if not self.cedula_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Campo requerido", "La cédula es obligatoria.")
            return
        if not self.nombre_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Campo requerido", "El nombre es obligatorio.")
            return
        if not EMAIL_REGEX.match(self.correo_edit.text().strip()):
            QtWidgets.QMessageBox.warning(self, "Correo inválido", "Ingrese un correo electrónico válido.")
            return
        self.accept()

    def get_data(self):
        return {
            "cedula": self.cedula_edit.text().strip(),
            "nombre": self.nombre_edit.text().strip(),
            "telefono": self.telefono_edit.text().strip(),
            "correo": self.correo_edit.text().strip(),
        }
