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
from controllers.mass_mail_controller import MassMailController
from controllers.mass_send_worker import MassSendWorker

from views.employee_dialog import EmployeeDialog
from views.settings_dialog import SettingsDialog
from views.google_drive_dialog import GoogleDriveDialog
from views.loading_dialog import LoadingDialog


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Nómina - Envío de Pagos por Correo")
        self.resize(1050, 680)

        self.filas_pago_actual = []
        self.destinatarios_masivo_actual = []
        self.worker = None
        self.worker_masivo = None

        self._crear_menu()
        self._crear_tabs()

        self.cargar_empleados()
        self.cargar_ultimos_destinatarios_masivo()
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
        tabs.addTab(self._crear_tab_mensajes_masivos(), "Mensajes Masivos")
        tabs.addTab(self._crear_tab_logs(), "Historial de Envíos")


    # -------------------- Tab Empleados --------------------
    def _crear_tab_empleados(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        botones_layout = QtWidgets.QHBoxLayout()
        self.chk_seleccionar_todo_emp = QtWidgets.QCheckBox("Seleccionar / Deseleccionar todo")
        self.chk_seleccionar_todo_emp.setChecked(True)
        btn_nuevo = QtWidgets.QPushButton("Nuevo empleado")
        btn_editar = QtWidgets.QPushButton("Editar")
        btn_eliminar = QtWidgets.QPushButton("Eliminar seleccionados")
        btn_refrescar = QtWidgets.QPushButton("Refrescar")
        btn_plantilla = QtWidgets.QPushButton("Generar plantilla")
        btn_importar = QtWidgets.QPushButton("Importar desde Excel")

        botones_layout.addWidget(self.chk_seleccionar_todo_emp)
        botones_layout.addWidget(btn_nuevo)
        botones_layout.addWidget(btn_editar)
        botones_layout.addWidget(btn_eliminar)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_plantilla)
        botones_layout.addWidget(btn_importar)
        botones_layout.addWidget(btn_refrescar)

        self.tabla_empleados = QtWidgets.QTableWidget()
        columnas = ["Seleccionar", "Cédula", "Nombre", "Teléfono", "Correo"]
        self.tabla_empleados.setColumnCount(len(columnas))
        self.tabla_empleados.setHorizontalHeaderLabels(columnas)
        self.tabla_empleados.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tabla_empleados.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tabla_empleados.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla_empleados.horizontalHeader().setSectionsMovable(True)
        self.tabla_empleados.horizontalHeader().setDragEnabled(True)
        self.tabla_empleados.setSortingEnabled(True)

        layout.addLayout(botones_layout)
        layout.addWidget(self.tabla_empleados)

        self.chk_seleccionar_todo_emp.stateChanged.connect(self._toggle_seleccionar_todo_empleados)
        btn_nuevo.clicked.connect(self.nuevo_empleado)
        btn_editar.clicked.connect(self.editar_empleado)
        btn_eliminar.clicked.connect(self.eliminar_empleado)
        btn_refrescar.clicked.connect(self.cargar_empleados)
        btn_plantilla.clicked.connect(self.generar_plantilla_empleados)
        btn_importar.clicked.connect(self.importar_empleados_excel)

        return widget

    def _toggle_seleccionar_todo_empleados(self, state):
        nuevo_estado = QtCore.Qt.Checked if state == QtCore.Qt.Checked else QtCore.Qt.Unchecked
        self.tabla_empleados.blockSignals(True)
        for i in range(self.tabla_empleados.rowCount()):
            item = self.tabla_empleados.item(i, 0)
            if item:
                item.setCheckState(nuevo_estado)
        self.tabla_empleados.blockSignals(False)

    def cargar_empleados(self):
        self.tabla_empleados.setSortingEnabled(False)
        empleados = EmployeeController.listar_empleados()
        self.tabla_empleados.setRowCount(0)

        estado_chk = QtCore.Qt.Checked if self.chk_seleccionar_todo_emp.isChecked() else QtCore.Qt.Unchecked

        for empleado in empleados:
            fila = self.tabla_empleados.rowCount()
            self.tabla_empleados.insertRow(fila)

            # Columna 0: Checkbox
            item_chk = QtWidgets.QTableWidgetItem()
            item_chk.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item_chk.setCheckState(estado_chk)
            item_chk.setData(QtCore.Qt.UserRole, empleado)
            self.tabla_empleados.setItem(fila, 0, item_chk)

            # Columnas 1 a 4: Cédula, Nombre, Teléfono, Correo
            self.tabla_empleados.setItem(fila, 1, QtWidgets.QTableWidgetItem(str(empleado["cedula"])))
            self.tabla_empleados.setItem(fila, 2, QtWidgets.QTableWidgetItem(str(empleado["nombre"])))
            self.tabla_empleados.setItem(fila, 3, QtWidgets.QTableWidgetItem(str(empleado["telefono"] or "")))
            self.tabla_empleados.setItem(fila, 4, QtWidgets.QTableWidgetItem(str(empleado["correo"])))

        self.tabla_empleados.resizeColumnsToContents()
        self.tabla_empleados.setSortingEnabled(True)

    def _empleado_seleccionado(self):
        fila = self.tabla_empleados.currentRow()
        if fila < 0:
            return None
        item_chk = self.tabla_empleados.item(fila, 0)
        if item_chk:
            return item_chk.data(QtCore.Qt.UserRole)
        return None

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
        # Recopilar todos los empleados marcados en la lista de verificación
        seleccionados = []
        for i in range(self.tabla_empleados.rowCount()):
            item_chk = self.tabla_empleados.item(i, 0)
            if item_chk and item_chk.checkState() == QtCore.Qt.Checked:
                emp = item_chk.data(QtCore.Qt.UserRole)
                if emp:
                    seleccionados.append(emp)

        if not seleccionados:
            emp_cursor = self._empleado_seleccionado()
            if emp_cursor:
                seleccionados = [emp_cursor]

        if not seleccionados:
            QtWidgets.QMessageBox.information(
                self, "Selección requerida",
                "Debe marcar la casilla de verificación de al menos un empleado para eliminar."
            )
            return

        respuesta = QtWidgets.QMessageBox.question(
            self, "Confirmar eliminación masiva",
            f"¿Está seguro de eliminar {len(seleccionados)} empleado(s) seleccionado(s)?"
        )
        if respuesta != QtWidgets.QMessageBox.Yes:
            return

        eliminados = 0
        omitidos = 0

        for emp in seleccionados:
            try:
                EmployeeController.eliminar_empleado(emp["id"])
                eliminados += 1
            except Exception:
                omitidos += 1

        self.cargar_empleados()

        msg = f"Eliminación completada.\nEmpleados eliminados exitosamente: {eliminados}"
        if omitidos > 0:
            msg += f"\nOmitidos (por tener envíos registrados en el historial): {omitidos}"

        QtWidgets.QMessageBox.information(self, "Resultado de eliminación", msg)

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
        btn_cargar_drive = QtWidgets.QPushButton("Cargar desde Google Drive")
        btn_config_drive = QtWidgets.QPushButton("Cambiar URL Drive...")
        btn_limpiar = QtWidgets.QPushButton("Limpiar")
        self.btn_ajustar_columnas = QtWidgets.QPushButton("Ajustar columnas")
        self.btn_ajustar_columnas.setEnabled(False)
        self.label_archivo = QtWidgets.QLabel("Ningún archivo cargado")
        fila_superior.addWidget(btn_cargar_excel)
        fila_superior.addWidget(btn_cargar_drive)
        fila_superior.addWidget(btn_config_drive)
        fila_superior.addWidget(btn_limpiar)
        fila_superior.addWidget(self.btn_ajustar_columnas)
        fila_superior.addWidget(self.label_archivo)
        fila_superior.addStretch()

        fila_asunto = QtWidgets.QHBoxLayout()
        fila_asunto.addWidget(QtWidgets.QLabel("Asunto del correo:"))
        self.asunto_edit = QtWidgets.QLineEdit("Reporte de pago - {periodo}")
        self.asunto_edit.setToolTip("Puede usar {periodo} y {nombre} como variables")
        fila_asunto.addWidget(self.asunto_edit)

        self.tabla_preview = QtWidgets.QTableWidget()
        self.tabla_preview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla_preview.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tabla_preview.setSortingEnabled(True)
        self.tabla_preview.horizontalHeader().setSectionsMovable(True)
        self.tabla_preview.horizontalHeader().setDragEnabled(True)

        fila_botones = QtWidgets.QHBoxLayout()
        self.chk_seleccionar_todo = QtWidgets.QCheckBox("Seleccionar / Deseleccionar todo")
        self.chk_seleccionar_todo.setChecked(True)
        self.chk_seleccionar_todo.setEnabled(False)
        self.btn_enviar = QtWidgets.QPushButton("Enviar correos")
        self.btn_enviar.setEnabled(False)
        self.btn_detener = QtWidgets.QPushButton("Detener")
        self.btn_detener.setEnabled(False)
        fila_botones.addWidget(self.chk_seleccionar_todo)
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

        self.tabla_preview.horizontalHeader().sectionMoved.connect(lambda *args: self._guardar_estado_columnas())

        btn_cargar_excel.clicked.connect(self.seleccionar_excel)
        btn_cargar_drive.clicked.connect(self.cargar_desde_drive)
        btn_config_drive.clicked.connect(self.cambiar_url_drive)
        btn_limpiar.clicked.connect(self.limpiar_datos_pagos)
        self.btn_ajustar_columnas.clicked.connect(self.ajustar_columnas_pagos)
        self.chk_seleccionar_todo.stateChanged.connect(self._toggle_seleccionar_todo)
        self.btn_enviar.clicked.connect(self.enviar_correos)
        self.btn_detener.clicked.connect(self.detener_envio)

        return widget

    def limpiar_datos_pagos(self):
        self.filas_pago_actual = []
        self.label_archivo.setText("Ningún archivo cargado")
        self.tabla_preview.setSortingEnabled(False)
        self.tabla_preview.clear()
        self.tabla_preview.setRowCount(0)
        self.tabla_preview.setColumnCount(0)
        self.btn_ajustar_columnas.setEnabled(False)
        self.btn_enviar.setEnabled(False)
        self.btn_detener.setEnabled(False)
        self.chk_seleccionar_todo.setEnabled(False)
        self.chk_seleccionar_todo.blockSignals(True)
        self.chk_seleccionar_todo.setChecked(True)
        self.chk_seleccionar_todo.blockSignals(False)
        self.barra_progreso.setValue(0)
        self.texto_log.clear()

    def ajustar_columnas_pagos(self):
        if self.tabla_preview.columnCount() > 0:
            self.tabla_preview.resizeColumnsToContents()

    def seleccionar_excel(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de pagos", "", "Excel (*.xlsx *.xls)"
        )
        if not ruta:
            return

        dialogo = LoadingDialog("excel", ruta, parent=self)
        if dialogo.exec_() == QtWidgets.QDialog.Accepted and dialogo.resultado_filas is not None:
            filas = dialogo.resultado_filas
            self.filas_pago_actual = filas
            self.label_archivo.setText(ruta.split("/")[-1])
            self._mostrar_preview(filas)
            self.btn_enviar.setEnabled(len(filas) > 0)
        elif dialogo.error_mensaje:
            QtWidgets.QMessageBox.critical(self, "Error al leer el Excel", dialogo.error_mensaje)

    def cargar_desde_drive(self):
        url_guardada = SettingsController.obtener_drive_url()
        if not url_guardada:
            dialogo = GoogleDriveDialog(self)
            if dialogo.exec_() != QtWidgets.QDialog.Accepted:
                return

            url_o_id = dialogo.get_url_or_id()
            if not url_o_id:
                QtWidgets.QMessageBox.warning(
                    self, "Campo vacío", "Debe ingresar una URL o ID de Google Sheets."
                )
                return

            SettingsController.guardar_drive_url(url_o_id)
            url_guardada = url_o_id

        dialogo = LoadingDialog("drive", url_guardada, parent=self)
        if dialogo.exec_() == QtWidgets.QDialog.Accepted and dialogo.resultado_filas is not None:
            filas = dialogo.resultado_filas
            self.filas_pago_actual = filas
            self.label_archivo.setText("Google Sheets (Cargado)")
            self._mostrar_preview(filas)
            self.btn_enviar.setEnabled(len(filas) > 0)
        elif dialogo.error_mensaje:
            QtWidgets.QMessageBox.critical(
                self, "Error al cargar Google Sheets", dialogo.error_mensaje
            )

    def cambiar_url_drive(self):
        url_actual = SettingsController.obtener_drive_url()
        dialogo = GoogleDriveDialog(self, url_inicial=url_actual)
        if dialogo.exec_() != QtWidgets.QDialog.Accepted:
            return

        nueva_url = dialogo.get_url_or_id()
        if not nueva_url:
            QtWidgets.QMessageBox.warning(
                self, "Campo vacío", "Debe ingresar una URL o ID de Google Sheets."
            )
            return

        SettingsController.guardar_drive_url(nueva_url)
        QtWidgets.QMessageBox.information(
            self, "URL guardada", "La URL de Google Drive ha sido guardada encriptada de forma segura."
        )

        # Cargar automáticamente con la nueva URL
        self.cargar_desde_drive()

    def _toggle_seleccionar_todo(self, state):
        nuevo_estado = QtCore.Qt.Checked if state == QtCore.Qt.Checked else QtCore.Qt.Unchecked
        self.tabla_preview.blockSignals(True)
        for i in range(self.tabla_preview.rowCount()):
            item = self.tabla_preview.item(i, 0)
            if item:
                item.setCheckState(nuevo_estado)
        self.tabla_preview.blockSignals(False)

    def _guardar_estado_columnas(self):
        state = self.tabla_preview.horizontalHeader().saveState()
        settings = QtCore.QSettings("NominaApp", "TablaPreview")
        settings.setValue("header_state", state)

    def _restaurar_estado_columnas(self):
        settings = QtCore.QSettings("NominaApp", "TablaPreview")
        state = settings.value("header_state")
        if state is not None:
            self.tabla_preview.horizontalHeader().restoreState(state)

    def _mostrar_preview(self, filas):
        self.tabla_preview.setSortingEnabled(False)
        self.tabla_preview.clear()
        if not filas:
            self.tabla_preview.setRowCount(0)
            self.tabla_preview.setColumnCount(0)
            self.chk_seleccionar_todo.setEnabled(False)
            self.btn_ajustar_columnas.setEnabled(False)
            return

        self.chk_seleccionar_todo.setEnabled(True)
        self.btn_ajustar_columnas.setEnabled(True)
        self.chk_seleccionar_todo.blockSignals(True)
        self.chk_seleccionar_todo.setChecked(True)
        self.chk_seleccionar_todo.blockSignals(False)

        columnas_datos = list(filas[0].keys())
        encabezados_completos = ["Enviar"] + columnas_datos

        self.tabla_preview.setColumnCount(len(encabezados_completos))
        self.tabla_preview.setHorizontalHeaderLabels(encabezados_completos)
        self.tabla_preview.setRowCount(len(filas))

        for i, fila in enumerate(filas):
            # Columna 0: Checkbox de selección
            item_chk = QtWidgets.QTableWidgetItem()
            item_chk.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item_chk.setCheckState(QtCore.Qt.Checked)
            item_chk.setData(QtCore.Qt.UserRole, fila)
            self.tabla_preview.setItem(i, 0, item_chk)

            # Columnas 1 en adelante: datos reales de la nómina
            for j, col in enumerate(columnas_datos):
                val_str = str(fila.get(col, ""))
                self.tabla_preview.setItem(i, j + 1, QtWidgets.QTableWidgetItem(val_str))

        self._restaurar_estado_columnas()
        self.tabla_preview.resizeColumnsToContents()
        self.tabla_preview.setSortingEnabled(True)

    def enviar_correos(self):
        # Filtrar únicamente las filas donde la casilla de verificación esté marcada (True)
        filas_a_enviar = []
        for i in range(self.tabla_preview.rowCount()):
            item_chk = self.tabla_preview.item(i, 0)
            if item_chk and item_chk.checkState() == QtCore.Qt.Checked:
                fila_data = item_chk.data(QtCore.Qt.UserRole)
                if fila_data:
                    filas_a_enviar.append(fila_data)

        if not filas_a_enviar:
            QtWidgets.QMessageBox.warning(
                self, "Sin destinatarios",
                "Debe seleccionar al menos un registro (marcar el casilla de verificación) para realizar el envío."
            )
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
            f"Se enviarán {len(filas_a_enviar)} correos a los destinatarios seleccionados. ¿Desea continuar?"
        )
        if confirmacion != QtWidgets.QMessageBox.Yes:
            return

        self.texto_log.clear()
        self.barra_progreso.setValue(0)
        self.barra_progreso.setMaximum(len(filas_a_enviar))

        self.worker = SendWorker(filas_a_enviar, smtp_config, self.asunto_edit.text())
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

    # -------------------- Tab Mensajes Masivos --------------------
    def _crear_tab_mensajes_masivos(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Fila superior de herramientas de destinatarios
        fila_herramientas = QtWidgets.QHBoxLayout()
        btn_cargar_ultimos = QtWidgets.QPushButton("Cargar últimos destinatarios")
        btn_cargar_empleados = QtWidgets.QPushButton("Cargar desde lista de empleados")
        self.buscar_masivo_edit = QtWidgets.QLineEdit()
        self.buscar_masivo_edit.setPlaceholderText("Filtrar por cédula, nombre o correo...")
        self.label_total_masivo = QtWidgets.QLabel("0 destinatarios")

        fila_herramientas.addWidget(btn_cargar_ultimos)
        fila_herramientas.addWidget(btn_cargar_empleados)
        fila_herramientas.addWidget(self.buscar_masivo_edit)
        fila_herramientas.addWidget(self.label_total_masivo)

        # Fila Asunto y ayuda de variables
        fila_asunto = QtWidgets.QHBoxLayout()
        fila_asunto.addWidget(QtWidgets.QLabel("Asunto del correo:"))
        self.asunto_masivo_edit = QtWidgets.QLineEdit("Comunicado importante - {nombre}")
        self.asunto_masivo_edit.setToolTip("Variables disponibles: {nombre}, {cedula}, {correo}")
        fila_asunto.addWidget(self.asunto_masivo_edit, stretch=2)
        lbl_ayuda = QtWidgets.QLabel("Variables: <b>{nombre}</b>, <b>{cedula}</b>, <b>{correo}</b>")
        fila_asunto.addWidget(lbl_ayuda)

        # Campo Cuerpo del Mensaje
        layout_cuerpo = QtWidgets.QVBoxLayout()
        layout_cuerpo.addWidget(QtWidgets.QLabel("Cuerpo del mensaje (personalizable):"))
        self.cuerpo_masivo_edit = QtWidgets.QPlainTextEdit()
        self.cuerpo_masivo_edit.setMaximumHeight(130)
        self.cuerpo_masivo_edit.setPlainText(
            "Estimado(a) {nombre},\n\n"
            "Por medio del presente correo le informamos lo siguiente:\n\n"
            "[Escriba aquí el contenido del mensaje masivo]\n\n"
            "Saludos cordiales."
        )
        layout_cuerpo.addWidget(self.cuerpo_masivo_edit)

        # Tabla de destinatarios con checkbox
        self.tabla_masivo = QtWidgets.QTableWidget()
        columnas = ["Enviar", "Cédula", "Nombre", "Correo"]
        self.tabla_masivo.setColumnCount(len(columnas))
        self.tabla_masivo.setHorizontalHeaderLabels(columnas)
        self.tabla_masivo.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tabla_masivo.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tabla_masivo.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla_masivo.horizontalHeader().setSectionsMovable(True)
        self.tabla_masivo.horizontalHeader().setDragEnabled(True)
        self.tabla_masivo.setSortingEnabled(True)

        # Fila de botones de envío
        fila_acciones = QtWidgets.QHBoxLayout()
        self.chk_seleccionar_todo_masivo = QtWidgets.QCheckBox("Seleccionar / Deseleccionar todo")
        self.chk_seleccionar_todo_masivo.setChecked(True)
        self.btn_enviar_masivo = QtWidgets.QPushButton("Enviar correos masivos")
        self.btn_detener_masivo = QtWidgets.QPushButton("Detener")
        self.btn_detener_masivo.setEnabled(False)

        fila_acciones.addWidget(self.chk_seleccionar_todo_masivo)
        fila_acciones.addWidget(self.btn_enviar_masivo)
        fila_acciones.addWidget(self.btn_detener_masivo)
        fila_acciones.addStretch()

        # Barra de progreso y consola de log
        self.barra_progreso_masivo = QtWidgets.QProgressBar()
        self.texto_log_masivo = QtWidgets.QPlainTextEdit()
        self.texto_log_masivo.setReadOnly(True)
        self.texto_log_masivo.setMaximumBlockCount(2000)

        # Agregar todo al layout principal
        layout.addLayout(fila_herramientas)
        layout.addLayout(fila_asunto)
        layout.addLayout(layout_cuerpo)
        layout.addWidget(self.tabla_masivo, stretch=2)
        layout.addLayout(fila_acciones)
        layout.addWidget(self.barra_progreso_masivo)
        layout.addWidget(self.texto_log_masivo, stretch=1)

        # Conexión de señales
        btn_cargar_ultimos.clicked.connect(self.cargar_ultimos_destinatarios_masivo)
        btn_cargar_empleados.clicked.connect(self.cargar_empleados_masivo)
        self.buscar_masivo_edit.textChanged.connect(self._filtrar_destinatarios_masivo)
        self.chk_seleccionar_todo_masivo.stateChanged.connect(self._toggle_seleccionar_todo_masivo)
        self.btn_enviar_masivo.clicked.connect(self.enviar_correos_masivos)
        self.btn_detener_masivo.clicked.connect(self.detener_envio_masivo)

        return widget

    def cargar_ultimos_destinatarios_masivo(self):
        destinatarios = MassMailController.obtener_ultimos_destinatarios()
        if not destinatarios:
            destinatarios = MassMailController.obtener_todos_los_empleados()
        self._mostrar_destinatarios_masivo(destinatarios, origen="Últimos remitentes/destinatarios")

    def cargar_empleados_masivo(self):
        empleados = MassMailController.obtener_todos_los_empleados()
        self._mostrar_destinatarios_masivo(empleados, origen="Lista de empleados")

    def _mostrar_destinatarios_masivo(self, lista, origen=""):
        self.tabla_masivo.setSortingEnabled(False)
        self.tabla_masivo.setRowCount(0)
        self.destinatarios_masivo_actual = lista

        estado_chk = QtCore.Qt.Checked if self.chk_seleccionar_todo_masivo.isChecked() else QtCore.Qt.Unchecked

        for fila_idx, dest in enumerate(lista):
            self.tabla_masivo.insertRow(fila_idx)

            # Columna 0: Checkbox
            item_chk = QtWidgets.QTableWidgetItem()
            item_chk.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item_chk.setCheckState(estado_chk)
            item_chk.setData(QtCore.Qt.UserRole, dest)
            self.tabla_masivo.setItem(fila_idx, 0, item_chk)

            # Columnas 1 a 3: Cédula, Nombre, Correo
            self.tabla_masivo.setItem(fila_idx, 1, QtWidgets.QTableWidgetItem(str(dest.get("cedula", "") or "")))
            self.tabla_masivo.setItem(fila_idx, 2, QtWidgets.QTableWidgetItem(str(dest.get("nombre", "") or "")))
            self.tabla_masivo.setItem(fila_idx, 3, QtWidgets.QTableWidgetItem(str(dest.get("correo", "") or "")))

        self.tabla_masivo.resizeColumnsToContents()
        self.tabla_masivo.setSortingEnabled(True)

        total = len(lista)
        texto_origen = f" ({origen})" if origen else ""
        self.label_total_masivo.setText(f"{total} destinatario(s){texto_origen}")
        self._filtrar_destinatarios_masivo()

    def _filtrar_destinatarios_masivo(self):
        texto = self.buscar_masivo_edit.text().strip().lower()
        for i in range(self.tabla_masivo.rowCount()):
            if not texto:
                self.tabla_masivo.setRowHidden(i, False)
                continue

            cedula = (self.tabla_masivo.item(i, 1).text() if self.tabla_masivo.item(i, 1) else "").lower()
            nombre = (self.tabla_masivo.item(i, 2).text() if self.tabla_masivo.item(i, 2) else "").lower()
            correo = (self.tabla_masivo.item(i, 3).text() if self.tabla_masivo.item(i, 3) else "").lower()

            coincide = (texto in cedula) or (texto in nombre) or (texto in correo)
            self.tabla_masivo.setRowHidden(i, not coincide)

    def _toggle_seleccionar_todo_masivo(self, state):
        nuevo_estado = QtCore.Qt.Checked if state == QtCore.Qt.Checked else QtCore.Qt.Unchecked
        self.tabla_masivo.blockSignals(True)
        for i in range(self.tabla_masivo.rowCount()):
            if not self.tabla_masivo.isRowHidden(i):
                item = self.tabla_masivo.item(i, 0)
                if item:
                    item.setCheckState(nuevo_estado)
        self.tabla_masivo.blockSignals(False)

    def enviar_correos_masivos(self):
        filas_a_enviar = []
        for i in range(self.tabla_masivo.rowCount()):
            item_chk = self.tabla_masivo.item(i, 0)
            if item_chk and item_chk.checkState() == QtCore.Qt.Checked:
                dest_data = item_chk.data(QtCore.Qt.UserRole)
                if dest_data:
                    filas_a_enviar.append(dest_data)

        if not filas_a_enviar:
            QtWidgets.QMessageBox.warning(
                self, "Sin destinatarios",
                "Debe seleccionar al menos un destinatario (marcar su casilla de verificación) para realizar el envío."
            )
            return

        asunto = self.asunto_masivo_edit.text().strip()
        cuerpo = self.cuerpo_masivo_edit.toPlainText().strip()

        if not asunto:
            QtWidgets.QMessageBox.warning(self, "Asunto requerido", "Por favor ingrese el asunto del correo.")
            self.asunto_masivo_edit.setFocus()
            return

        if not cuerpo:
            QtWidgets.QMessageBox.warning(self, "Mensaje requerido", "Por favor ingrese el cuerpo del mensaje.")
            self.cuerpo_masivo_edit.setFocus()
            return

        smtp_config = SettingsController.get_smtp_config()
        if not smtp_config["host"] or not smtp_config["user"] or not smtp_config["password"]:
            QtWidgets.QMessageBox.warning(
                self, "Configuración requerida",
                "Debe configurar el servidor SMTP en el menú Configuración antes de enviar correos."
            )
            return

        confirmacion = QtWidgets.QMessageBox.question(
            self, "Confirmar envío masivo",
            f"Se enviarán {len(filas_a_enviar)} correos electrónicos personalizados a los destinatarios seleccionados.\n¿Desea continuar?"
        )
        if confirmacion != QtWidgets.QMessageBox.Yes:
            return

        self.texto_log_masivo.clear()
        self.barra_progreso_masivo.setValue(0)
        self.barra_progreso_masivo.setMaximum(len(filas_a_enviar))

        self.worker_masivo = MassSendWorker(filas_a_enviar, smtp_config, asunto, cuerpo)
        self.worker_masivo.progreso.connect(self._actualizar_progreso_masivo)
        self.worker_masivo.log.connect(self.texto_log_masivo.appendPlainText)
        self.worker_masivo.terminado.connect(self._envio_masivo_terminado)

        self.btn_enviar_masivo.setEnabled(False)
        self.btn_detener_masivo.setEnabled(True)
        self.worker_masivo.start()

    def detener_envio_masivo(self):
        if self.worker_masivo:
            self.worker_masivo.detener()
            self.btn_detener_masivo.setEnabled(False)

    def _actualizar_progreso_masivo(self, actual, total):
        self.barra_progreso_masivo.setValue(actual)

    def _envio_masivo_terminado(self, ok_count, error_count):
        self.btn_enviar_masivo.setEnabled(True)
        self.btn_detener_masivo.setEnabled(False)
        QtWidgets.QMessageBox.information(
            self, "Envío masivo finalizado",
            f"Proceso de envío masivo completado.\nExitosos: {ok_count}\nCon error: {error_count}"
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
        columnas = [
            "Fecha", "Estado", "Nombre", "Cédula", "Correo", "Tienda", "Mes",
            "% Comisión", "Bonificación", "Comisión encargado", "Sueldo",
            "TOTAL VENTA", "Gastos deducibles", "Neto (Ventas - Gastos)",
            "Vales", "Pagos realizados", "Neto a pagar", "Asunto", "Detalle"
        ]
        self.tabla_logs.setColumnCount(len(columnas))
        self.tabla_logs.setHorizontalHeaderLabels(columnas)
        self.tabla_logs.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla_logs.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tabla_logs.horizontalHeader().setSectionsMovable(True)
        self.tabla_logs.horizontalHeader().setDragEnabled(True)
        self.tabla_logs.setSortingEnabled(True)

        layout.addLayout(filtros)
        layout.addWidget(self.tabla_logs)

        btn_filtrar.clicked.connect(self.cargar_logs)
        btn_refrescar_logs.clicked.connect(self.cargar_logs)

        return widget

    def cargar_logs(self):
        import json
        self.tabla_logs.setSortingEnabled(False)
        estado = self.combo_estado.currentText() if hasattr(self, "combo_estado") else "Todos"
        texto = self.buscar_edit.text().strip() if hasattr(self, "buscar_edit") else ""
        logs = PaymentController.obtener_historial(estado_filtro=estado, texto_busqueda=texto)

        self.tabla_logs.setRowCount(0)
        for log in logs:
            fila = self.tabla_logs.rowCount()
            self.tabla_logs.insertRow(fila)

            # Intentar parsear el JSON completo de los datos enviados de la nómina
            datos_pago = {}
            if log.get("datos_json"):
                try:
                    datos_pago = json.loads(log["datos_json"])
                except Exception:
                    datos_pago = {}

            valores = [
                log.get("fecha_envio", ""),
                log.get("estado", ""),
                log.get("nombre", datos_pago.get("nombre", "")),
                log.get("cedula", datos_pago.get("cedula", "")),
                log.get("correo", ""),
                datos_pago.get("unidad_administrativa", ""),
                log.get("periodo", datos_pago.get("periodo", "")),
                datos_pago.get("% Comision", ""),
                datos_pago.get("Bonificacion", ""),
                datos_pago.get("Comision encargado", ""),
                datos_pago.get("Sueldo", ""),
                datos_pago.get("TOTAL VENTA", ""),
                datos_pago.get("Gastos deducibles", ""),
                datos_pago.get("Neto (Ventas - Gastos)", ""),
                datos_pago.get("Vales", ""),
                datos_pago.get("Pagos realizados", ""),
                log.get("monto", datos_pago.get("Neto a pagar", "")),
                log.get("asunto", ""),
                log.get("detalle", "")
            ]

            for j, valor in enumerate(valores):
                item = QtWidgets.QTableWidgetItem(str(valor) if valor is not None else "")
                if log.get("estado") == "ERROR":
                    item.setForeground(QtCore.Qt.red)
                self.tabla_logs.setItem(fila, j, item)

        self.tabla_logs.resizeColumnsToContents()
        self.tabla_logs.setSortingEnabled(True)

