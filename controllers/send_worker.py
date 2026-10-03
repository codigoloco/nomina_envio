"""
Controlador (en segundo plano): envío masivo de correos.
Es un QThread porque necesita correr sin congelar la interfaz, pero
cumple el rol de un controlador: orquesta EmployeeModel, EmailService
y EnvioModel según la lista de pagos leída del Excel.
"""

import json
from PyQt5 import QtCore

from models.auditoria_model import registrar_auditoria
from models.employee_model import EmployeeModel
from models.envio_model import EnvioModel
from services.email_sender import EmailService, EmailSendError


class SendWorker(QtCore.QThread):

    progreso = QtCore.pyqtSignal(int, int)   # (actual, total)
    log = QtCore.pyqtSignal(str)
    terminado = QtCore.pyqtSignal(int, int)  # (enviados_ok, enviados_error)

    def __init__(self, filas_pago, smtp_config, asunto_template, periodo_default="", correo_prueba: str = None):
        super().__init__()
        self.filas_pago = filas_pago
        self.smtp_config = smtp_config
        self.asunto_template = asunto_template
        self.periodo_default = periodo_default
        self.correo_prueba = (correo_prueba or "").strip()
        self._detener = False

    def detener(self):
        self._detener = True

    def run(self):
        total = len(self.filas_pago)
        ok_count = 0
        error_count = 0
        es_prueba = bool(self.correo_prueba)

        for idx, fila in enumerate(self.filas_pago, start=1):
            if self._detener:
                self.log.emit("Proceso detenido por el usuario.")
                break

            nombre_encargado = str(fila.get("nombre", fila.get("nombre_encargado", ""))).strip()
            cedula = str(fila.get("cedula", "")).strip()
            datos_json = json.dumps(fila, ensure_ascii=False)

            if cedula and cedula != "N/A":
                empleado = EmployeeModel.get_by_cedula(cedula)
                id_para_log = cedula
                tipo_id = "Cédula"
            else:
                empleado = EmployeeModel.get_by_nombre(nombre_encargado)
                id_para_log = nombre_encargado
                tipo_id = "Nombre"

            datos_pago = {k: v for k, v in fila.items() if k not in ("cedula", "nombre", "nombre_encargado")}
            periodo = fila.get("periodo", self.periodo_default)
            monto = fila.get("Neto a pagar", fila.get("monto_a_pagar", fila.get("monto", "")))

            if not empleado:
                mensaje = f"No se encontró un empleado registrado con el {tipo_id.lower()} '{id_para_log}'"
                self.log.emit(f"[ERROR] {tipo_id} {id_para_log}: {mensaje}")
                EnvioModel.add_log(
                    empleado_id=None,
                    cedula=cedula if not nombre_encargado else "",
                    nombre=nombre_encargado or "(desconocido)",
                    correo="",
                    periodo=periodo,
                    monto=monto,
                    asunto="",
                    estado="ERROR",
                    detalle=mensaje,
                    datos_json=datos_json
                )
                error_count += 1
                self.progreso.emit(idx, total)
                continue

            nombre_dest = empleado["nombre"]
            correo_dest_real = empleado["correo"]
            cedula_dest = empleado["cedula"]
            correo_dest_efectivo = self.correo_prueba if es_prueba else correo_dest_real

            try:
                asunto = self.asunto_template.format(periodo=periodo or "", nombre=nombre_dest)
            except Exception:
                asunto = self.asunto_template

            if es_prueba:
                asunto = f"[PRUEBA] {asunto}"

            remitente_correo = self.smtp_config.get("user", "")
            cuerpo_html = EmailService.build_payment_email_html(
                nombre_dest, datos_pago, remitente_correo=remitente_correo, periodo=periodo
            )

            try:
                EmailService.send_email(self.smtp_config, correo_dest_efectivo, asunto, cuerpo_html)
                if es_prueba:
                    self.log.emit(f"[PRUEBA] Recibo de {nombre_dest} enviado a '{correo_dest_efectivo}'")
                    registrar_auditoria(
                        "envio_correo_prueba",
                        entidad=correo_dest_efectivo,
                        detalle=f"empleado={nombre_dest}, cedula={cedula_dest}, periodo={periodo}"
                    )
                else:
                    self.log.emit(f"[OK] Correo enviado a {nombre_dest} ({correo_dest_efectivo})")

                EnvioModel.add_log(
                    empleado_id=empleado["id"],
                    cedula=cedula_dest,
                    nombre=nombre_dest,
                    correo=correo_dest_efectivo,
                    periodo=periodo,
                    monto=monto,
                    asunto=asunto,
                    estado="PRUEBA_OK" if es_prueba else "ENVIADO",
                    detalle=f"Prueba enviada a {correo_dest_efectivo}" if es_prueba else "OK",
                    datos_json=datos_json
                )
                ok_count += 1
            except EmailSendError as e:
                tag = "[ERROR-PRUEBA]" if es_prueba else "[ERROR]"
                self.log.emit(f"{tag} No se pudo enviar a {correo_dest_efectivo}: {e}")
                EnvioModel.add_log(
                    empleado_id=empleado["id"],
                    cedula=cedula_dest,
                    nombre=nombre_dest,
                    correo=correo_dest_efectivo,
                    periodo=periodo,
                    monto=monto,
                    asunto=asunto,
                    estado="PRUEBA_ERROR" if es_prueba else "ERROR",
                    detalle=str(e),
                    datos_json=datos_json
                )
                error_count += 1

            self.progreso.emit(idx, total)

        self.terminado.emit(ok_count, error_count)
