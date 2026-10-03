"""
Vista: Conexiones de base de datos (Configuración > Conexiones de base de datos).
Permite administrar varias conexiones (SQL Server, SQLite, MySQL, PostgreSQL),
probarlas, migrar (crear las tablas), importar los datos locales y marcar la activa.
Solo habla con ConexionController; no accede a modelos ni a drivers directamente.
"""

from PyQt5 import QtCore, QtGui, QtWidgets

from controllers.conexion_controller import ConexionController
from views.import_dialog import ImportSourceDialog

_COLOR_OK = "#2e9e5b"
_COLOR_ERROR = "#d9534f"


class DatabaseDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, mensaje_inicial: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Conexiones de base de datos")
        self.setMinimumSize(820, 480)

        self._cargando = False
        self._prueba_ok = False
        self._pendientes = None
        self._nombre_original = None
        self._puerto_defecto_anterior = ""
        self._motores = {m["clave"]: m for m in ConexionController.listar_motores()}

        self._crear_controles()
        self._armar_layout(mensaje_inicial)
        self._conectar_senales()

        self._cargar_lista()
        self._al_cambiar_motor()
        self._actualizar_botones()

    # ==================== Construcción ====================
    def _crear_controles(self):
        self.lista_conexiones = QtWidgets.QListWidget()
        self.lista_conexiones.setMinimumWidth(230)

        self.nombre_edit = QtWidgets.QLineEdit()
        self.nombre_edit.setPlaceholderText("Ej. Producción")

        self.motor_combo = QtWidgets.QComboBox()
        for clave, motor in self._motores.items():
            self.motor_combo.addItem(motor["etiqueta"], clave)

        self.lbl_controlador_odbc = QtWidgets.QLabel("Controlador ODBC:")
        self.controlador_odbc_combo = QtWidgets.QComboBox()

        self.lbl_host = QtWidgets.QLabel("Servidor (host):")
        self.host_edit = QtWidgets.QLineEdit()
        self.host_edit.setPlaceholderText("localhost")
        self.lbl_puerto = QtWidgets.QLabel("Puerto:")
        self.puerto_edit = QtWidgets.QLineEdit()
        self.puerto_edit.setValidator(QtGui.QIntValidator(0, 65535, self))

        self.etiqueta_base = QtWidgets.QLabel("Base de datos:")
        self.base_edit = QtWidgets.QLineEdit()
        self.btn_examinar = QtWidgets.QPushButton("Examinar...")

        self.lbl_usuario = QtWidgets.QLabel("Usuario:")
        self.usuario_edit = QtWidgets.QLineEdit()
        self.lbl_password = QtWidgets.QLabel("Contraseña:")
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.btn_mostrar_password = QtWidgets.QPushButton("Mostrar")
        self.btn_mostrar_password.setCheckable(True)

        self.estado_label = QtWidgets.QLabel("")
        self.estado_label.setWordWrap(True)
        self.estado_label.setTextFormat(QtCore.Qt.RichText)

        self.btn_probar = QtWidgets.QPushButton("Probar conexión")
        self.btn_migrar = QtWidgets.QPushButton("Migrar")
        self.btn_importar = QtWidgets.QPushButton("Importar datos...")
        self.btn_nueva = QtWidgets.QPushButton("Nueva")
        self.btn_guardar = QtWidgets.QPushButton("Guardar")
        self.btn_eliminar = QtWidgets.QPushButton("Eliminar")
        self.btn_activar = QtWidgets.QPushButton("Marcar como activa")
        self.btn_cerrar = QtWidgets.QPushButton("Cerrar")

    def _armar_layout(self, mensaje_inicial: str):
        self.form = QtWidgets.QFormLayout()
        self.form.addRow("Nombre de la conexión:", self.nombre_edit)       # fila 0
        self.form.addRow("Motor de base de datos:", self.motor_combo)      # fila 1
        self.form.addRow(self.lbl_controlador_odbc, self.controlador_odbc_combo)  # fila 2
        self.form.addRow(self.lbl_host, self.host_edit)                    # fila 3
        self.form.addRow(self.lbl_puerto, self.puerto_edit)                # fila 4

        fila_base = QtWidgets.QHBoxLayout()
        fila_base.addWidget(self.base_edit)
        fila_base.addWidget(self.btn_examinar)
        self.form.addRow(self.etiqueta_base, fila_base)                    # fila 5

        self.form.addRow(self.lbl_usuario, self.usuario_edit)              # fila 6

        fila_password = QtWidgets.QHBoxLayout()
        fila_password.addWidget(self.password_edit)
        fila_password.addWidget(self.btn_mostrar_password)
        self.form.addRow(self.lbl_password, fila_password)                 # fila 6

        fila_operaciones = QtWidgets.QHBoxLayout()
        fila_operaciones.addWidget(self.btn_probar)
        fila_operaciones.addWidget(self.btn_migrar)
        fila_operaciones.addWidget(self.btn_importar)
        fila_operaciones.addStretch()

        fila_gestion = QtWidgets.QHBoxLayout()
        fila_gestion.addWidget(self.btn_nueva)
        fila_gestion.addWidget(self.btn_guardar)
        fila_gestion.addWidget(self.btn_eliminar)
        fila_gestion.addWidget(self.btn_activar)
        fila_gestion.addStretch()
        fila_gestion.addWidget(self.btn_cerrar)

        derecha = QtWidgets.QVBoxLayout()
        if mensaje_inicial:
            aviso = QtWidgets.QLabel(mensaje_inicial)
            aviso.setWordWrap(True)
            derecha.addWidget(aviso)
        derecha.addLayout(self.form)
        derecha.addWidget(self.estado_label)
        derecha.addLayout(fila_operaciones)
        derecha.addStretch()
        derecha.addLayout(fila_gestion)

        izquierda = QtWidgets.QVBoxLayout()
        izquierda.addWidget(QtWidgets.QLabel("Conexiones guardadas:"))
        izquierda.addWidget(self.lista_conexiones)

        principal = QtWidgets.QHBoxLayout(self)
        principal.addLayout(izquierda)
        principal.addLayout(derecha, 1)

    def _conectar_senales(self):
        self.lista_conexiones.itemSelectionChanged.connect(self._al_seleccionar_conexion)
        self.motor_combo.currentIndexChanged.connect(self._al_cambiar_motor)
        self.btn_mostrar_password.toggled.connect(self._alternar_password)
        self.btn_examinar.clicked.connect(self._examinar_archivo)

        for campo in (self.host_edit, self.puerto_edit, self.base_edit, self.usuario_edit, self.password_edit):
            campo.textChanged.connect(self._invalidar_prueba)
        self.motor_combo.currentIndexChanged.connect(self._invalidar_prueba)
        self.controlador_odbc_combo.currentIndexChanged.connect(self._invalidar_prueba)

        self.btn_probar.clicked.connect(self._probar)
        self.btn_migrar.clicked.connect(self._migrar)
        self.btn_importar.clicked.connect(self._importar)
        self.btn_nueva.clicked.connect(self._nueva)
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.btn_activar.clicked.connect(self._activar)
        self.btn_cerrar.clicked.connect(self.accept)

    # ==================== Utilidades de formulario ====================
    def _motor_actual(self) -> dict:
        return self._motores[self.motor_combo.currentData()]

    def _config_desde_formulario(self) -> dict:
        return {
            "nombre": self.nombre_edit.text().strip(),
            "motor": self.motor_combo.currentData(),
            "driver_odbc": self.controlador_odbc_combo.currentText().strip() if self.controlador_odbc_combo.isVisible() else "",
            "host": self.host_edit.text().strip(),
            "puerto": self.puerto_edit.text().strip(),
            "base_datos": self.base_edit.text().strip(),
            "usuario": self.usuario_edit.text().strip(),
            "password": self.password_edit.text(),
        }

    def _cargar_en_formulario(self, config: dict):
        self._cargando = True
        try:
            indice = self.motor_combo.findData(config.get("motor", ""))
            self.motor_combo.setCurrentIndex(max(indice, 0))
            self.nombre_edit.setText(config.get("nombre", ""))
            self.host_edit.setText(config.get("host", ""))
            self.puerto_edit.setText(str(config.get("puerto", "")))
            self.base_edit.setText(config.get("base_datos", ""))
            self.usuario_edit.setText(config.get("usuario", ""))
            self.password_edit.setText(config.get("password", ""))
            self._al_cambiar_motor()  # Rellena el puerto por defecto y drivers
            driver_guardado = config.get("driver_odbc", "")
            if driver_guardado:
                idx_drv = self.controlador_odbc_combo.findText(driver_guardado)
                if idx_drv >= 0:
                    self.controlador_odbc_combo.setCurrentIndex(idx_drv)
        finally:
            self._cargando = False
        self._invalidar_prueba()

    def _limpiar_formulario(self):
        self._cargar_en_formulario({"motor": self.motor_combo.itemData(0)})
        self.estado_label.setText("")

    def _mostrar_estado(self, texto: str, ok: bool = True):
        color = _COLOR_OK if ok else _COLOR_ERROR
        simbolo = "✔" if ok else "✖"
        texto_html = texto.replace("\n", "<br>")
        self.estado_label.setText(f"<span style='color:{color};'><b>{simbolo}</b> {texto_html}</span>")

    def _con_espera(self, funcion):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            return funcion()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _actualizar_botones(self):
        guardada = self._nombre_original is not None
        self.btn_migrar.setEnabled(self._prueba_ok)
        self.btn_importar.setEnabled(self._prueba_ok and self._pendientes == 0)
        self.btn_eliminar.setEnabled(guardada)
        self.btn_activar.setEnabled(guardada)

    # ==================== Eventos de formulario ====================
    def _al_cambiar_motor(self):
        motor = self._motor_actual()
        clave_motor = self.motor_combo.currentData()
        usa_archivo = motor["usa_archivo"]
        visible = not usa_archivo

        # Cargar lista de controladores específicos si el motor los soporta (ej. SQL Server con pyodbc)
        controladores = ConexionController.listar_controladores_motor(clave_motor)
        tiene_controladores = bool(controladores)

        texto_actual = self.controlador_odbc_combo.currentText()
        self.controlador_odbc_combo.blockSignals(True)
        self.controlador_odbc_combo.clear()
        if tiene_controladores:
            for c in controladores:
                self.controlador_odbc_combo.addItem(c, c)
            if texto_actual:
                idx_previo = self.controlador_odbc_combo.findText(texto_actual)
                if idx_previo >= 0:
                    self.controlador_odbc_combo.setCurrentIndex(idx_previo)
        self.controlador_odbc_combo.blockSignals(False)

        self.lbl_controlador_odbc.setVisible(tiene_controladores)
        self.controlador_odbc_combo.setVisible(tiene_controladores)

        for widget in (
            self.lbl_host, self.host_edit,
            self.lbl_puerto, self.puerto_edit,
            self.lbl_usuario, self.usuario_edit,
            self.lbl_password, self.password_edit,
            self.btn_mostrar_password,
        ):
            widget.setVisible(visible)

        self.btn_examinar.setVisible(usa_archivo)
        self.etiqueta_base.setText("Archivo de base de datos (.db):" if usa_archivo else "Base de datos:")

        puerto_nuevo = "" if usa_archivo or not motor["puerto"] else str(motor["puerto"])
        texto_puerto = self.puerto_edit.text().strip()
        if not texto_puerto or texto_puerto == self._puerto_defecto_anterior:
            self.puerto_edit.setText(puerto_nuevo)
        self._puerto_defecto_anterior = puerto_nuevo

    def _invalidar_prueba(self, *_):
        if self._cargando:
            return
        self._prueba_ok = False
        self._pendientes = None
        self._actualizar_botones()

    def _alternar_password(self, visible: bool):
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Normal if visible else QtWidgets.QLineEdit.Password)
        self.btn_mostrar_password.setText("Ocultar" if visible else "Mostrar")

    def _examinar_archivo(self):
        ruta, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Archivo de base de datos SQLite", self.base_edit.text(),
            "SQLite (*.db *.sqlite *.sqlite3);;Todos los archivos (*)",
            options=QtWidgets.QFileDialog.DontConfirmOverwrite,
        )
        if ruta:
            self.base_edit.setText(ruta)

    # ==================== Lista de conexiones ====================
    def _cargar_lista(self, seleccionar: str = None):
        activa = ConexionController.nombre_activa().strip().lower()
        self.lista_conexiones.blockSignals(True)
        self.lista_conexiones.clear()
        fila_a_seleccionar = -1
        for i, config in enumerate(ConexionController.listar()):
            etiqueta_motor = self._motores.get(config["motor"], {}).get("etiqueta", config["motor"])
            marca = "★ " if config["nombre"].strip().lower() == activa else ""
            item = QtWidgets.QListWidgetItem(f"{marca}{config['nombre']}  ({etiqueta_motor})")
            item.setData(QtCore.Qt.UserRole, config["nombre"])
            self.lista_conexiones.addItem(item)
            if seleccionar and config["nombre"] == seleccionar:
                fila_a_seleccionar = i
        self.lista_conexiones.blockSignals(False)
        if fila_a_seleccionar >= 0:
            self.lista_conexiones.setCurrentRow(fila_a_seleccionar)

    def _al_seleccionar_conexion(self):
        item = self.lista_conexiones.currentItem()
        if not item:
            return
        nombre = item.data(QtCore.Qt.UserRole)
        for config in ConexionController.listar():
            if config["nombre"] == nombre:
                self._nombre_original = nombre
                self._cargar_en_formulario(config)
                self.estado_label.setText("")
                self._actualizar_botones()
                return

    # ==================== Acciones ====================
    def _nueva(self):
        self.lista_conexiones.clearSelection()
        self._nombre_original = None
        self._limpiar_formulario()
        self._actualizar_botones()

    def _guardar(self):
        config = self._config_desde_formulario()
        try:
            ConexionController.guardar(config, self._nombre_original)
        except ValueError as error:
            QtWidgets.QMessageBox.warning(self, "Datos incompletos", str(error))
            return
        self._nombre_original = config["nombre"]
        self._cargar_lista(seleccionar=config["nombre"])
        self._mostrar_estado(f"Conexión '{config['nombre']}' guardada.")
        self._actualizar_botones()

    def _eliminar(self):
        if self._nombre_original is None:
            return
        respuesta = QtWidgets.QMessageBox.question(
            self, "Eliminar conexión", f"¿Eliminar la conexión '{self._nombre_original}'?"
        )
        if respuesta != QtWidgets.QMessageBox.Yes:
            return
        ConexionController.eliminar(self._nombre_original)
        self._nueva()
        self._cargar_lista()

    def _probar(self):
        config = self._config_desde_formulario()
        ok, mensaje = self._con_espera(lambda: ConexionController.probar(config))
        self._prueba_ok = ok
        self._pendientes = None
        if not ok:
            self._mostrar_estado(mensaje, ok=False)
            self._actualizar_botones()
            return

        try:
            pendientes = self._con_espera(lambda: ConexionController.pendientes(config))
            self._pendientes = len(pendientes)
            self._mostrar_estado(f"{mensaje}\nMigraciones pendientes en esta base: {self._pendientes}.")
        except Exception as error:
            self._mostrar_estado(f"{mensaje}\nNo se pudo verificar las migraciones: {error}", ok=False)
        self._actualizar_botones()

    def _migrar(self):
        config = self._config_desde_formulario()
        if self._pendientes == 0:
            QtWidgets.QMessageBox.information(self, "Migrar", "La base de datos ya está al día: no hay migraciones pendientes.")
            return
        respuesta = QtWidgets.QMessageBox.question(
            self, "Migrar",
            f"Se ejecutarán las migraciones pendientes en '{config['nombre'] or config['base_datos']}' "
            "(creación de tablas). ¿Desea continuar?",
        )
        if respuesta != QtWidgets.QMessageBox.Yes:
            return
        try:
            ejecutadas = self._con_espera(lambda: ConexionController.migrar(config))
        except Exception as error:
            self._mostrar_estado(str(error), ok=False)
            return
        self._pendientes = 0
        listado = "\n".join(f"• {nombre}" for nombre in ejecutadas) or "Sin cambios."
        self._mostrar_estado(f"Migración completada ({len(ejecutadas)}):\n{listado}")
        self._actualizar_botones()

    def _importar(self):
        config_destino = self._config_desde_formulario()
        nombre_actual = self.nombre_edit.text().strip()
        conexiones = ConexionController.listar()

        dialogo = ImportSourceDialog(
            conexiones_guardadas=conexiones,
            conexion_actual_nombre=nombre_actual,
            parent=self,
        )
        if dialogo.exec_() != QtWidgets.QDialog.Accepted:
            return

        origen = dialogo.obtener_datos_origen()
        try:
            resumen = self._con_espera(
                lambda: ConexionController.importar_desde_origen(config_destino, origen)
            )
            detalles = []
            if "empleados" in resumen:
                detalles.append(f"• Empleados importados: {resumen['empleados']}")
            if "envios" in resumen:
                detalles.append(f"• Envíos importados: {resumen['envios']}")
            if "smtp" in resumen:
                detalles.append(
                    f"• Configuración SMTP: {'Copiada / Configurada' if resumen['smtp'] else 'Omitida o no encontrada'}"
                )

            QtWidgets.QMessageBox.information(
                self,
                "Importación completada",
                f"Datos importados exitosamente desde '{resumen.get('origen', '')}':\n\n"
                + "\n".join(detalles),
            )
            self._mostrar_estado(
                f"Importación completada desde '{resumen.get('origen')}': "
                f"{resumen.get('empleados', 0)} emp, {resumen.get('envios', 0)} envíos."
            )
        except Exception as error:
            QtWidgets.QMessageBox.critical(self, "Error al importar datos", str(error))

    def _activar(self):
        if self._nombre_original is None:
            return
        try:
            self._con_espera(lambda: ConexionController.activar(self._nombre_original))
        except ValueError as error:
            self._mostrar_estado(str(error), ok=False)
            return
        self._cargar_lista(seleccionar=self._nombre_original)
        self._mostrar_estado(f"'{self._nombre_original}' es ahora la base de datos activa.")
