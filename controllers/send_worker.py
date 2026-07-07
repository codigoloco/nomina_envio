"""
Controlador (en segundo plano): envío masivo de correos.
Es un QThread porque necesita correr sin congelar la interfaz, pero
cumple el rol de un controlador: orquesta EmployeeModel, EmailService
y EnvioModel según la lista de pagos leída del Excel.
"""

from PyQt5 import QtCore

from models.employee_model import EmployeeModel
from models.envio_model import EnvioModel
from services.email_sender import EmailService, EmailSendError


class SendWorker(QtCore.QThread):

    progreso = QtCore.pyqtSignal(int, int)   # (actual, total)
    log = QtCore.pyqtSignal(str)
    terminado = QtCore.pyqtSignal(int, int)  # (enviados_ok, enviados_error)

    def __init__(self, filas_pago, smtp_config, asunto_template, periodo_default=""):
        super().__init__()
        self.filas_pago = filas_pago
        self.smtp_config = smtp_config
        self.asunto_template = asunto_template
        self.periodo_default = periodo_default
        self._detener = False

    def detener(self):
        self._detener = True

    def run(self):
        total = len(self.filas_pago)
        ok_count = 0
        error_count = 0

        for idx, fila in enumerate(self.filas_pago, start=1):
            if self._detener:
                self.log.emit("Proceso detenido por el usuario.")
                break

            cedula = str(fila.get("cedula", "")).strip()
            empleado = EmployeeModel.get_by_cedula(cedula)

            datos_pago = {k: v for k, v in fila.items() if k != "cedula"}
            periodo = fila.get("periodo", self.periodo_default)
            monto = fila.get("monto", fila.get("neto_a_pagar", ""))

            if not empleado:
                mensaje = f"No se encontró un empleado registrado con la cédula '{cedula}'"
                self.log.emit(f"[ERROR] Cédula {cedula}: {mensaje}")
                EnvioModel.add_log(
                    empleado_id=None, cedula=cedula, nombre="(desconocido)", correo="",
                    periodo=periodo, monto=monto, asunto="", estado="ERROR", detalle=mensaje
                )
                error_count += 1
                self.progreso.emit(idx, total)
                continue

            try:
                asunto = self.asunto_template.format(periodo=periodo or "", nombre=empleado["nombre"])
            except Exception:
                asunto = self.asunto_template

            cuerpo_html = EmailService.build_payment_email_html(empleado["nombre"], datos_pago)

            try:
                EmailService.send_email(self.smtp_config, empleado["correo"], asunto, cuerpo_html)
                self.log.emit(f"[OK] Correo enviado a {empleado['nombre']} ({empleado['correo']})")
                EnvioModel.add_log(
                    empleado_id=empleado["id"], cedula=cedula, nombre=empleado["nombre"],
                    correo=empleado["correo"], periodo=periodo, monto=monto,
                    asunto=asunto, estado="ENVIADO", detalle="OK"
                )
                ok_count += 1
            except EmailSendError as e:
                self.log.emit(f"[ERROR] No se pudo enviar a {empleado['nombre']} ({empleado['correo']}): {e}")
                EnvioModel.add_log(
                    empleado_id=empleado["id"], cedula=cedula, nombre=empleado["nombre"],
                    correo=empleado["correo"], periodo=periodo, monto=monto,
                    asunto=asunto, estado="ERROR", detalle=str(e)
                )
                error_count += 1

            self.progreso.emit(idx, total)

        self.terminado.emit(ok_count, error_count)
