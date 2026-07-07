"""
Servicio: envío de correos vía SMTP.
Adapta la lógica de smtplib/email a algo simple de usar desde los
controladores.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSendError(Exception):
    """Se lanza cuando el envío de un correo falla, con el detalle del error."""
    pass


class EmailService:

    @staticmethod
    def build_payment_email_html(nombre, datos_pago):
        """
        Construye el cuerpo HTML del correo con el detalle del pago.
        datos_pago: dict con las columnas del Excel (sin la columna 'cedula').
        """
        filas_html = ""
        for clave, valor in datos_pago.items():
            etiqueta = clave.replace("_", " ").capitalize()
            filas_html += (
                f"<tr>"
                f"<td style='padding:6px 12px;border:1px solid #ddd;background:#f7f7f7;'><b>{etiqueta}</b></td>"
                f"<td style='padding:6px 12px;border:1px solid #ddd;'>{valor}</td>"
                f"</tr>"
            )

        return f"""
        <html>
        <body style="font-family:Arial, sans-serif; color:#333;">
            <p>Estimado(a) <b>{nombre}</b>,</p>
            <p>A continuación el detalle correspondiente a su pago:</p>
            <table style="border-collapse:collapse;">
                {filas_html}
            </table>
            <p style="margin-top:20px;font-size:12px;color:#888;">
                Este es un correo generado automáticamente, por favor no responder.
            </p>
        </body>
        </html>
        """

    @staticmethod
    def send_email(smtp_config, destinatario, asunto, cuerpo_html):
        """
        smtp_config: dict con host, port, user, password, use_tls (bool), remitente_nombre.
        Lanza EmailSendError con el detalle si algo falla.
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        remitente_nombre = smtp_config.get("remitente_nombre") or smtp_config["user"]
        msg["From"] = f'{remitente_nombre} <{smtp_config["user"]}>'
        msg["To"] = destinatario
        msg.attach(MIMEText(cuerpo_html, "html"))

        host = smtp_config["host"]
        port = int(smtp_config["port"])
        user = smtp_config["user"]
        password = smtp_config["password"]
        use_tls = smtp_config.get("use_tls", True)

        server = None
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=20)
            else:
                server = smtplib.SMTP(host, port, timeout=20)
                if use_tls:
                    server.starttls()

            server.login(user, password)
            server.sendmail(user, [destinatario], msg.as_string())
        except Exception as e:
            raise EmailSendError(str(e))
        finally:
            if server is not None:
                try:
                    server.quit()
                except Exception:
                    pass
