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

            nombre_encargado = str(fila.get("nombre_encargado", "")).strip()
            cedula = str(fila.get("cedula", "")).strip()

            if cedula:
                empleado = EmployeeModel.get_by_cedula(cedula)
                id_para_log = cedula
                tipo_id = "Cédula"
            else:
                empleado = EmployeeModel.get_by_nombre(nombre_encargado)
                id_para_log = nombre_encargado
                tipo_id = "Nombre"

            datos_pago = {k: v for k, v in fila.items() if k not in ("cedula", "nombre_encargado")}
            periodo = fila.get("periodo", self.periodo_default)
            monto = fila.get("monto_a_pagar", fila.get("monto", fila.get("neto_a_pagar", "")))

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
                    detalle=mensaje
                )
                error_count += 1
                self.progreso.emit(idx, total)
                continue

            # Usamos los datos correctos del empleado de la BD
            nombre_dest = empleado["nombre"]
            correo_dest = empleado["correo"]
            cedula_dest = empleado["cedula"]

            try:
                asunto = self.asunto_template.format(periodo=periodo or "", nombre=nombre_dest)
            except Exception:
                asunto = self.asunto_template

            cuerpo_html = EmailService.build_payment_email_html(nombre_dest, datos_pago)

            try:
                EmailService.send_email(self.smtp_config, correo_dest, asunto, cuerpo_html)
                self.log.emit(f"[OK] Correo enviado a {nombre_dest} ({correo_dest})")
                EnvioModel.add_log(
                    empleado_id=empleado["id"],
                    cedula=cedula_dest,
                    nombre=nombre_dest,
                    correo=correo_dest,
                    periodo=periodo,
                    monto=monto,
                    asunto=asunto,
                    estado="ENVIADO",
                    detalle="OK"
                )
                ok_count += 1
            except EmailSendError as e:
                self.log.emit(f"[ERROR] No se pudo enviar a {nombre_dest} ({correo_dest}): {e}")
                EnvioModel.add_log(
                    empleado_id=empleado["id"],
                    cedula=cedula_dest,
                    nombre=nombre_dest,
                    correo=correo_dest,
                    periodo=periodo,
                    monto=monto,
                    asunto=asunto,
                    estado="ERROR",
                    detalle=str(e)
                )
                error_count += 1

            self.progreso.emit(idx, total)

        self.terminado.emit(ok_count, error_count)
