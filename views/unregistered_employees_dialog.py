"""
Diálogo modal de alerta: Empleados no registrados detectados tras cargar el archivo Excel.
Muestra la lista de empleados que poseen cédula en el Excel pero aún no existen en la base de datos.
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class UnregisteredEmployeesDialog(QtWidgets.QDialog):

    def __init__(self, empleados_no_registrados: list, parent=None):
        super().__init__(parent)
        self.empleados = empleados_no_registrados or []
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Alerta: Empleados no registrados en el sistema")
        self.resize(540, 420)
        self.setMinimumSize(450, 320)

        layout_principal = QtWidgets.QVBoxLayout(self)
        layout_principal.setSpacing(12)
        layout_principal.setContentsMargins(16, 16, 16, 16)

        # Encabezado con icono y texto explicativo
        layout_header = QtWidgets.QHBoxLayout()
        icono_label = QtWidgets.QLabel()
        icono_sistema = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        icono_label.setPixmap(icono_sistema.pixmap(36, 36))
        layout_header.addWidget(icono_label)

        layout_textos = QtWidgets.QVBoxLayout()
        total = len(self.empleados)
        titulo_label = QtWidgets.QLabel(f"<b>Se detectaron {total} empleado{'s' if total != 1 else ''} no registrado{'s' if total != 1 else ''}:</b>")
        titulo_label.setWordWrap(True)
        layout_textos.addWidget(titulo_label)

        subtitulo_label = QtWidgets.QLabel(
            "Las siguientes personas aparecen con cédula en el archivo cargado, pero no existen en la base de datos. "
            "Para poder enviarles sus recibos por correo, debes registrarlas previamente en la sección de Empleados."
        )
        subtitulo_label.setWordWrap(True)
        subtitulo_label.setStyleSheet("color: gray;")
        layout_textos.addWidget(subtitulo_label)
        layout_header.addLayout(layout_textos, 1)

        layout_principal.addLayout(layout_header)

        # Tabla de visualización
        self.tabla = QtWidgets.QTableWidget(len(self.empleados), 2)
        self.tabla.setHorizontalHeaderLabels(["Cédula", "Nombre / Encargado"])
        self.tabla.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

        for fila_idx, emp in enumerate(self.empleados):
            item_cedula = QtWidgets.QTableWidgetItem(str(emp.get("cedula", "")))
            item_cedula.setTextAlignment(QtCore.Qt.AlignCenter)
            item_nombre = QtWidgets.QTableWidgetItem(str(emp.get("nombre", "")))

            self.tabla.setItem(fila_idx, 0, item_cedula)
            self.tabla.setItem(fila_idx, 1, item_nombre)

        layout_principal.addWidget(self.tabla, 1)

        # Botones inferiores
        layout_botones = QtWidgets.QHBoxLayout()

        self.btn_copiar = QtWidgets.QPushButton("Copiar lista al portapapeles")
        self.btn_copiar.clicked.connect(self._copiar_al_portapapeles)
        layout_botones.addWidget(self.btn_copiar)

        layout_botones.addStretch()

        self.btn_aceptar = QtWidgets.QPushButton("Aceptar y continuar")
        self.btn_aceptar.setDefault(True)
        self.btn_aceptar.clicked.connect(self.accept)
        layout_botones.addWidget(self.btn_aceptar)

        layout_principal.addLayout(layout_botones)

    def _copiar_al_portapapeles(self):
        """Copia la lista de cédulas y nombres al portapapeles del sistema operativo."""
        lineas = ["Cédula\tNombre"]
        for emp in self.empleados:
            lineas.append(f"{emp.get('cedula', '')}\t{emp.get('nombre', '')}")

        texto = "\n".join(lineas)
        QtWidgets.QApplication.clipboard().setText(texto)

        self.btn_copiar.setText("✔ ¡Copiado al portapapeles!")
        QtCore.QTimer.singleShot(2500, lambda: self.btn_copiar.setText("Copiar lista al portapapeles"))
