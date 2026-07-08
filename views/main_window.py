"""
Vista: ventana principal (3 pestañas).
Regla de la arquitectura MVC de este proyecto: main_window.py NUNCA
importa 'models.*' directamente. Toda operación de datos pasa por un
controlador (EmployeeController, PaymentController, SettingsController)
o por el SendWorker (controlador en segundo plano).
"""

from PyQt5 import QtWidgets, QtCore

from controllers.employee_controller import EmployeeController
from controllers.payment_controller import PaymentController
from controllers.settings_controller import SettingsController
from controllers.send_worker import SendWorker

from views.employee_dialog import EmployeeDialog
from views.settings_dialog import SettingsDialog


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Nómina - Envío de Pagos por Correo")
        self.resize(1050, 680)

        self.filas_pago_actual = []
        self.worker = None

        self._crear_menu()
        self._crear_tabs()

        self.cargar_empleados()
        self.cargar_logs()

    # ==================== Menú ====================
    def _crear_menu(self):
        menu = self.menuBar().addMenu("Configuración")
        accion_smtp = menu.addAction("Configurar correo SMTP")
        accion_smtp.triggered.connect(self.abrir_configuracion_smtp)

    def abrir_configuracion_smtp(self):
        SettingsDialog(self).exec_()

    # ==================== Tabs ====================
    def _crear_tabs(self):
        tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(tabs)
        tabs.addTab(self._crear_tab_empleados(), "Empleados")
        tabs.addTab(self._crear_tab_pagos(), "Procesar Pagos")
        tabs.addTab(self._crear_tab_logs(), "Historial de Envíos")

    # -------------------- Tab Empleados --------------------
    def _crear_tab_empleados(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        botones_layout = QtWidgets.QHBoxLayout()
        btn_nuevo = QtWidgets.QPushButton("Nuevo empleado")
        btn_editar = QtWidgets.QPushButton("Editar")
        btn_eliminar = QtWidgets.QPushButton("Eliminar")
        btn_refrescar = QtWidgets.QPushButton("Refrescar")
        btn_plantilla = QtWidgets.QPushButton("Generar plantilla")
        btn_importar = QtWidgets.QPushButton("Importar desde Excel")
        botones_layout.addWidget(btn_nuevo)
        botones_layout.addWidget(btn_editar)
        botones_layout.addWidget(btn_eliminar)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_plantilla)
        botones_layout.addWidget(btn_importar)
        botones_layout.addWidget(btn_refrescar)

        self.tabla_empleados = QtWidgets.QTableWidget()
        self.tabla_empleados.setColumnCount(4)
        self.tabla_empleados.setHorizontalHeaderLabels(["Cédula", "Nombre", "Teléfono", "Correo"])
        self.tabla_empleados.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tabla_empleados.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla_empleados.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(botones_layout)
        layout.addWidget(self.tabla_empleados)

        btn_nuevo.clicked.connect(self.nuevo_empleado)
        btn_editar.clicked.connect(self.editar_empleado)
        btn_eliminar.clicked.connect(self.eliminar_empleado)
        btn_refrescar.clicked.connect(self.cargar_empleados)
        btn_plantilla.clicked.connect(self.generar_plantilla_empleados)
        btn_importar.clicked.connect(self.importar_empleados_excel)

        return widget

    def cargar_empleados(self):
        empleados = EmployeeController.listar_empleados()
        self.tabla_empleados.setRowCount(0)
        for empleado in empleados:
            fila = self.tabla_empleados.rowCount()
            self.tabla_empleados.insertRow(fila)
            self.tabla_empleados.setItem(fila, 0, QtWidgets.QTableWidgetItem(empleado["cedula"]))
            self.tabla_empleados.setItem(fila, 1, QtWidgets.QTableWidgetItem(empleado["nombre"]))
            self.tabla_empleados.setItem(fila, 2, QtWidgets.QTableWidgetItem(empleado["telefono"] or ""))
            self.tabla_empleados.setItem(fila, 3, QtWidgets.QTableWidgetItem(empleado["correo"]))
            self.tabla_empleados.item(fila, 0).setData(QtCore.Qt.UserRole, empleado["id"])

    def _empleado_seleccionado(self):
        fila = self.tabla_empleados.currentRow()
        if fila < 0:
            return None
        emp_id = self.tabla_empleados.item(fila, 0).data(QtCore.Qt.UserRole)
        return {
            "id": emp_id,
            "cedula": self.tabla_empleados.item(fila, 0).text(),
            "nombre": self.tabla_empleados.item(fila, 1).text(),
            "telefono": self.tabla_empleados.item(fila, 2).text(),
            "correo": self.tabla_empleados.item(fila, 3).text(),
        }

    def nuevo_empleado(self):
        dialogo = EmployeeDialog(self)
        if dialogo.exec_() == QtWidgets.QDialog.Accepted:
            datos = dialogo.get_data()
            try:
                EmployeeController.crear_empleado(**datos)
                self.cargar_empleados()
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"No se pudo guardar el empleado (¿cédula duplicada?):\n{e}"
                )

    def editar_empleado(self):
        seleccionado = self._empleado_seleccionado()
        if not seleccionado:
            QtWidgets.QMessageBox.information(self, "Selección requerida", "Seleccione un empleado de la tabla.")
            return
        dialogo = EmployeeDialog(self, empleado=seleccionado)
        if dialogo.exec_() == QtWidgets.QDialog.Accepted:
            datos = dialogo.get_data()
            try:
                EmployeeController.actualizar_empleado(seleccionado["id"], **datos)
                self.cargar_empleados()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo actualizar el empleado:\n{e}")

    def eliminar_empleado(self):
        seleccionado = self._empleado_seleccionado()
        if not seleccionado:
            QtWidgets.QMessageBox.information(self, "Selección requerida", "Seleccione un empleado de la tabla.")
            return
        respuesta = QtWidgets.QMessageBox.question(
            self, "Confirmar eliminación", f"¿Eliminar al empleado {seleccionado['nombre']}?"
        )
        if respuesta == QtWidgets.QMessageBox.Yes:
            try:
                EmployeeController.eliminar_empleado(seleccionado["id"])
                self.cargar_empleados()
            except Exception:
                QtWidgets.QMessageBox.warning(
                    self, "No se puede eliminar",
                    "Este empleado ya tiene envíos registrados en el historial y no puede "
                    "eliminarse (se perdería la trazabilidad). Si ya no trabaja en la empresa, "
                    "considera dejarlo registrado o crear un campo 'activo' en vez de borrarlo."
                )

    def generar_plantilla_empleados(self):
        ruta, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Guardar plantilla de empleados", "plantilla_empleados.xlsx", "Excel (*.xlsx)"
        )
        if not ruta:
            return
        try:
            EmployeeController.generar_plantilla(ruta)
            QtWidgets.QMessageBox.information(
                self, "Plantilla generada",
                f"Plantilla guardada en:\n{ruta}\n\nLlenala con los datos de los empleados "
                "(cedula, nombre, telefono, correo) y luego usa 'Importar desde Excel'."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo generar la plantilla:\n{e}")

    def importar_empleados_excel(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar plantilla de empleados", "", "Excel (*.xlsx *.xls)"
        )
        if not ruta:
            return
        try:
            insertados, duplicados = EmployeeController.importar_masivo(ruta)
            self.cargar_empleados()
            QtWidgets.QMessageBox.information(
                self, "Importacion completada",
                f"Empleados importados: {insertados}\nDuplicados ignorados: {duplicados}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error al importar", str(e))



    # -------------------- Tab Procesar Pagos --------------------
    def _crear_tab_pagos(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        fila_superior = QtWidgets.QHBoxLayout()
        btn_cargar_excel = QtWidgets.QPushButton("Seleccionar archivo Excel...")
        self.label_archivo = QtWidgets.QLabel("Ningún archivo cargado")
        fila_superior.addWidget(btn_cargar_excel)
        fila_superior.addWidget(self.label_archivo)
        fila_superior.addStretch()

        fila_asunto = QtWidgets.QHBoxLayout()
        fila_asunto.addWidget(QtWidgets.QLabel("Asunto del correo:"))
        self.asunto_edit = QtWidgets.QLineEdit("Reporte de pago - {periodo}")
        self.asunto_edit.setToolTip("Puede usar {periodo} y {nombre} como variables")
        fila_asunto.addWidget(self.asunto_edit)

        self.tabla_preview = QtWidgets.QTableWidget()
        self.tabla_preview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        fila_botones = QtWidgets.QHBoxLayout()
        self.btn_enviar = QtWidgets.QPushButton("Enviar correos")
        self.btn_enviar.setEnabled(False)
        self.btn_detener = QtWidgets.QPushButton("Detener")
        self.btn_detener.setEnabled(False)
        fila_botones.addWidget(self.btn_enviar)
        fila_botones.addWidget(self.btn_detener)
        fila_botones.addStretch()

        self.barra_progreso = QtWidgets.QProgressBar()
        self.texto_log = QtWidgets.QPlainTextEdit()
        self.texto_log.setReadOnly(True)
        self.texto_log.setMaximumBlockCount(2000)

        layout.addLayout(fila_superior)
        layout.addLayout(fila_asunto)
        layout.addWidget(self.tabla_preview, stretch=2)
        layout.addLayout(fila_botones)
        layout.addWidget(self.barra_progreso)
        layout.addWidget(self.texto_log, stretch=1)

        btn_cargar_excel.clicked.connect(self.seleccionar_excel)
        self.btn_enviar.clicked.connect(self.enviar_correos)
        self.btn_detener.clicked.connect(self.detener_envio)

        return widget

    def seleccionar_excel(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de pagos", "", "Excel (*.xlsx *.xls)"
        )
        if not ruta:
            return
        try:
            filas = PaymentController.cargar_excel_pagos(ruta)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error al leer el Excel", str(e))
            return

        self.filas_pago_actual = filas
        self.label_archivo.setText(ruta.split("/")[-1])
        self._mostrar_preview(filas)
        self.btn_enviar.setEnabled(len(filas) > 0)

    def _mostrar_preview(self, filas):
        self.tabla_preview.clear()
        if not filas:
            self.tabla_preview.setRowCount(0)
            self.tabla_preview.setColumnCount(0)
            return
        columnas = list(filas[0].keys())
        self.tabla_preview.setColumnCount(len(columnas))
        self.tabla_preview.setHorizontalHeaderLabels(columnas)
        self.tabla_preview.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for j, col in enumerate(columnas):
                self.tabla_preview.setItem(i, j, QtWidgets.QTableWidgetItem(str(fila.get(col, ""))))
        self.tabla_preview.resizeColumnsToContents()

    def enviar_correos(self):
        if not self.filas_pago_actual:
            return

        smtp_config = SettingsController.get_smtp_config()
        if not smtp_config["host"] or not smtp_config["user"] or not smtp_config["password"]:
            QtWidgets.QMessageBox.warning(
                self, "Configuración requerida",
                "Debe configurar el servidor SMTP en el menú Configuración antes de enviar correos."
            )
            return

        confirmacion = QtWidgets.QMessageBox.question(
            self, "Confirmar envío",
            f"Se enviarán {len(self.filas_pago_actual)} correos. ¿Desea continuar?"
        )
        if confirmacion != QtWidgets.QMessageBox.Yes:
            return

        self.texto_log.clear()
        self.barra_progreso.setValue(0)
        self.barra_progreso.setMaximum(len(self.filas_pago_actual))

        self.worker = SendWorker(self.filas_pago_actual, smtp_config, self.asunto_edit.text())
        self.worker.progreso.connect(self._actualizar_progreso)
        self.worker.log.connect(self.texto_log.appendPlainText)
        self.worker.terminado.connect(self._envio_terminado)

        self.btn_enviar.setEnabled(False)
        self.btn_detener.setEnabled(True)
        self.worker.start()

    def detener_envio(self):
        if self.worker:
            self.worker.detener()
            self.btn_detener.setEnabled(False)

    def _actualizar_progreso(self, actual, total):
        self.barra_progreso.setValue(actual)

    def _envio_terminado(self, ok_count, error_count):
        self.btn_enviar.setEnabled(True)
        self.btn_detener.setEnabled(False)
        QtWidgets.QMessageBox.information(
            self, "Proceso finalizado",
            f"Envío completado.\nExitosos: {ok_count}\nCon error: {error_count}"
        )
        self.cargar_logs()

    # -------------------- Tab Historial de Envíos --------------------
    def _crear_tab_logs(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        filtros = QtWidgets.QHBoxLayout()
        self.combo_estado = QtWidgets.QComboBox()
        self.combo_estado.addItems(["Todos", "ENVIADO", "ERROR"])
        self.buscar_edit = QtWidgets.QLineEdit()
        self.buscar_edit.setPlaceholderText("Buscar por cédula, nombre o correo...")
        btn_filtrar = QtWidgets.QPushButton("Filtrar")
        btn_refrescar_logs = QtWidgets.QPushButton("Refrescar")

        filtros.addWidget(QtWidgets.QLabel("Estado:"))
        filtros.addWidget(self.combo_estado)
        filtros.addWidget(self.buscar_edit)
        filtros.addWidget(btn_filtrar)
        filtros.addWidget(btn_refrescar_logs)

        self.tabla_logs = QtWidgets.QTableWidget()
        columnas = ["Fecha", "Cédula", "Nombre", "Correo", "Periodo", "Monto", "Asunto", "Estado", "Detalle"]
        self.tabla_logs.setColumnCount(len(columnas))
        self.tabla_logs.setHorizontalHeaderLabels(columnas)
        self.tabla_logs.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla_logs.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(filtros)
        layout.addWidget(self.tabla_logs)

        btn_filtrar.clicked.connect(self.cargar_logs)
        btn_refrescar_logs.clicked.connect(self.cargar_logs)

        return widget

    def cargar_logs(self):
        estado = self.combo_estado.currentText() if hasattr(self, "combo_estado") else "Todos"
        texto = self.buscar_edit.text().strip() if hasattr(self, "buscar_edit") else ""
        logs = PaymentController.obtener_historial(estado_filtro=estado, texto_busqueda=texto)

        self.tabla_logs.setRowCount(0)
        for log in logs:
            fila = self.tabla_logs.rowCount()
            self.tabla_logs.insertRow(fila)
            valores = [
                log["fecha_envio"], log["cedula"], log["nombre"], log["correo"],
                log["periodo"], log["monto"], log["asunto"], log["estado"], log["detalle"]
            ]
            for j, valor in enumerate(valores):
                item = QtWidgets.QTableWidgetItem(str(valor) if valor is not None else "")
                if log["estado"] == "ERROR":
                    item.setForeground(QtCore.Qt.red)
                self.tabla_logs.setItem(fila, j, item)
        self.tabla_logs.resizeColumnsToContents()
