"""
Controlador en segundo plano: envío masivo de mensajes o comunicados personalizados.
Hereda de QThread para ejecutar la tarea sin bloquear la interfaz gráfica.
Cumple con principios SOLID y MVC.
"""

from PyQt5 import QtCore

from models.envio_model import EnvioModel
from services.email_sender import EmailService, EmailSendError


class MassSendWorker(QtCore.QThread):

    progreso = QtCore.pyqtSignal(int, int)   # (actual, total)
    log = QtCore.pyqtSignal(str)
    terminado = QtCore.pyqtSignal(int, int)  # (enviados_ok, enviados_error)

    def __init__(self, destinatarios, smtp_config, asunto_template, cuerpo_template):
        super().__init__()
        self.destinatarios = destinatarios
        self.smtp_config = smtp_config
        self.asunto_template = asunto_template
        self.cuerpo_template = cuerpo_template
        self._detener = False

    def detener(self):
        self._detener = True

    def _personalizar_texto(self, texto, nombre, cedula, correo):
        """
        Reemplaza las etiquetas dinámicas en el texto de forma segura
        e insensible a mayúsculas/minúsculas en el nombre del tag.
        """
        resultado = texto
        tags = {
            "{nombre}": nombre,
            "{cedula}": cedula,
            "{correo}": correo
        }
        for tag, val in tags.items():
            # Reemplazar tanto en minúsculas como en mayúsculas
            resultado = resultado.replace(tag, val)
            resultado = resultado.replace(tag.upper(), val)
            resultado = resultado.replace(tag.capitalize(), val)
        return resultado

    def run(self):
        total = len(self.destinatarios)
        ok_count = 0
        error_count = 0

        for idx, dest in enumerate(self.destinatarios, start=1):
            if self._detener:
                self.log.emit("Proceso de envío masivo detenido por el usuario.")
                break

            nombre = str(dest.get("nombre", "")).strip()
            cedula = str(dest.get("cedula", "")).strip()
            correo = str(dest.get("correo", "")).strip()
            empleado_id = dest.get("empleado_id", dest.get("id"))

            if not correo:
                self.log.emit(f"[ERROR] El destinatario '{nombre}' no posee un correo electrónico válido.")
                error_count += 1
                self.progreso.emit(idx, total)
                continue

            asunto_personalizado = self._personalizar_texto(
                self.asunto_template, nombre, cedula, correo
            )
            cuerpo_personalizado = self._personalizar_texto(
                self.cuerpo_template, nombre, cedula, correo
            )

            cuerpo_html = EmailService.build_custom_message_html(nombre, cuerpo_personalizado)

            try:
                EmailService.send_email(self.smtp_config, correo, asunto_personalizado, cuerpo_html)
                self.log.emit(f"[OK] Correo masivo enviado a {nombre} ({correo})")
                EnvioModel.add_log(
                    empleado_id=empleado_id,
                    cedula=cedula,
                    nombre=nombre,
                    correo=correo,
                    periodo="Mensaje masivo",
                    monto="N/A",
                    asunto=asunto_personalizado,
                    estado="ENVIADO",
                    detalle="OK"
                )
                ok_count += 1
            except EmailSendError as e:
                self.log.emit(f"[ERROR] No se pudo enviar a {nombre} ({correo}): {e}")
                EnvioModel.add_log(
                    empleado_id=empleado_id,
                    cedula=cedula,
                    nombre=nombre,
                    correo=correo,
                    periodo="Mensaje masivo",
                    monto="N/A",
                    asunto=asunto_personalizado,
                    estado="ERROR",
                    detalle=str(e)
                )
                error_count += 1
            except Exception as e:
                self.log.emit(f"[ERROR] Error inesperado enviando a {nombre} ({correo}): {e}")
                EnvioModel.add_log(
                    empleado_id=empleado_id,
                    cedula=cedula,
                    nombre=nombre,
                    correo=correo,
                    periodo="Mensaje masivo",
                    monto="N/A",
                    asunto=asunto_personalizado,
                    estado="ERROR",
                    detalle=str(e)
                )
                error_count += 1

            self.progreso.emit(idx, total)

        self.terminado.emit(ok_count, error_count)
