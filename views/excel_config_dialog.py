"""
Vista: Diálogo de configuración de carga de Excel.
Permite al usuario seleccionar:
1. La hoja de trabajo (solo hojas visibles).
2. Las columnas a incluir mediante un checklist interactivo.
3. El mes / período a procesar (extraído de la hoja o su slicer).
Recuerda automáticamente la última configuración utilizada.
"""

from PyQt5 import QtCore, QtWidgets

from models.config_carga_excel_model import ConfigCargaExcelModel


class ExcelConfigDialog(QtWidgets.QDialog):

    def __init__(self, estructura_info: dict, parent=None):
        """
        @param estructura_info: dict devuelto por ExcelReader.inspeccionar_estructura:
               {
                   "hojas_visibles": ["Pagos encargados", ...],
                   "hojas_info": {
                       "Pagos encargados": {
                           "columnas": ["Encargado", "Tienda", ...],
                           "meses": ["sept", ...],
                           "mes_slicer": "sept"
                       }
                   }
               }
        """
        super().__init__(parent)
        self.setWindowTitle("Configuración de Carga de Excel")
        self.setMinimumSize(540, 520)

        self.estructura = estructura_info
        self.hojas_visibles = estructura_info.get("hojas_visibles", [])
        self.hojas_info = estructura_info.get("hojas_info", {})

        self.config_recordada = ConfigCargaExcelModel.obtener_ultima()

        self._crear_controles()
        self._armar_layout()
        self._conectar_senales()

        self._inicializar_valores()

    def _crear_controles(self):
        # 1. Selector de Hoja
        self.combo_hoja = QtWidgets.QComboBox()
        for h in self.hojas_visibles:
            self.combo_hoja.addItem(h, h)

        # 2. Selector de Mes
        self.combo_mes = QtWidgets.QComboBox()

        # 3. Lista de Columnas con Checkboxes
        self.lista_columnas = QtWidgets.QListWidget()
        self.lista_columnas.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.btn_marcar_todas = QtWidgets.QPushButton("Marcar todas")
        self.btn_desmarcar_todas = QtWidgets.QPushButton("Desmarcar todas")

        # 4. Botones Aceptar / Cancelar
        self.btn_aceptar = QtWidgets.QPushButton("Cargar datos seleccionados")
        self.btn_aceptar.setDefault(True)
        self.btn_cancelar = QtWidgets.QPushButton("Cancelar")

    def _armar_layout(self):
        form = QtWidgets.QFormLayout()
        form.addRow("Hoja de cálculo:", self.combo_hoja)
        form.addRow("Mes / Período a procesar:", self.combo_mes)

        fila_checks = QtWidgets.QHBoxLayout()
        fila_checks.addWidget(QtWidgets.QLabel("<b>Columnas a procesar:</b>"))
        fila_checks.addStretch()
        fila_checks.addWidget(self.btn_marcar_todas)
        fila_checks.addWidget(self.btn_desmarcar_todas)

        fila_botones = QtWidgets.QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(self.btn_cancelar)
        fila_botones.addWidget(self.btn_aceptar)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addSpacing(6)
        layout.addLayout(fila_checks)
        layout.addWidget(self.lista_columnas, 1)

        nota = QtWidgets.QLabel(
            "<i>Solo se exportarán e incluirán las columnas marcadas. "
            "La configuración elegida se recordará automáticamente para futuras cargas.</i>"
        )
        nota.setWordWrap(True)
        layout.addWidget(nota)
        layout.addSpacing(6)
        layout.addLayout(fila_botones)

    def _conectar_senales(self):
        self.combo_hoja.currentIndexChanged.connect(self._al_cambiar_hoja)
        self.btn_marcar_todas.clicked.connect(self._marcar_todas)
        self.btn_desmarcar_todas.clicked.connect(self._desmarcar_todas)
        self.btn_aceptar.clicked.connect(self._aceptar)
        self.btn_cancelar.clicked.connect(self.reject)

    def _inicializar_valores(self):
        hoja_guardada = self.config_recordada.get("hoja", "")
        indice = self.combo_hoja.findData(hoja_guardada)
        if indice >= 0:
            self.combo_hoja.setCurrentIndex(indice)
        elif self.combo_hoja.count() > 0:
            self.combo_hoja.setCurrentIndex(0)

        self._al_cambiar_hoja()

    def _al_cambiar_hoja(self):
        hoja = self.combo_hoja.currentData()
        info = self.hojas_info.get(hoja, {})

        # Actualizar selector de Meses
        meses_disponibles = info.get("meses", [])
        mes_slicer = info.get("mes_slicer", "")
        mes_guardado = self.config_recordada.get("mes", "")

        self.combo_mes.blockSignals(True)
        self.combo_mes.clear()

        # Añadir opción 'Todos los meses'
        self.combo_mes.addItem("(Todos los registros / Sin filtro de mes)", "")

        for m in meses_disponibles:
            self.combo_mes.addItem(str(m).capitalize(), str(m).lower())

        # Seleccionar mes preferido: 1. slicer de esta hoja, 2. recordado
        mes_objetivo = mes_slicer or mes_guardado
        if mes_objetivo:
            idx = self.combo_mes.findData(mes_objetivo.lower())
            if idx >= 0:
                self.combo_mes.setCurrentIndex(idx)
            elif self.combo_mes.count() > 1:
                self.combo_mes.setCurrentIndex(1)
        self.combo_mes.blockSignals(False)

        # Actualizar Checklist de Columnas
        columnas = info.get("columnas", [])
        cols_guardadas = set(self.config_recordada.get("columnas", []))

        self.lista_columnas.blockSignals(True)
        self.lista_columnas.clear()

        usar_guardadas = (hoja == self.config_recordada.get("hoja")) and bool(cols_guardadas)

        for col in columnas:
            item = QtWidgets.QListWidgetItem(col)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            if usar_guardadas:
                marcado = col in cols_guardadas
            else:
                marcado = True  # Por defecto todas seleccionadas

            item.setCheckState(QtCore.Qt.Checked if marcado else QtCore.Qt.Unchecked)
            self.lista_columnas.addItem(item)

        self.lista_columnas.blockSignals(False)

    def _marcar_todas(self):
        for i in range(self.lista_columnas.count()):
            self.lista_columnas.item(i).setCheckState(QtCore.Qt.Checked)

    def _desmarcar_todas(self):
        for i in range(self.lista_columnas.count()):
            self.lista_columnas.item(i).setCheckState(QtCore.Qt.Unchecked)

    def obtener_configuracion(self) -> dict:
        """
        Retorna la configuración elegida:
        {
            "hoja": str,
            "columnas": [str, ...],
            "mes": str
        }
        """
        hoja = self.combo_hoja.currentData()
        mes = self.combo_mes.currentData()
        columnas = []
        for i in range(self.lista_columnas.count()):
            item = self.lista_columnas.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                columnas.append(item.text())

        return {
            "hoja": hoja,
            "columnas": columnas,
            "mes": mes,
        }

    def _aceptar(self):
        config = self.obtener_configuracion()
        if not config["columnas"]:
            QtWidgets.QMessageBox.warning(
                self, "Sin columnas seleccionadas",
                "Debe marcar al menos una columna para procesar."
            )
            return

        # Guardar configuración para recordarla en el futuro
        ConfigCargaExcelModel.guardar(
            hoja=config["hoja"],
            columnas=config["columnas"],
            mes=config["mes"]
        )

        self.accept()
