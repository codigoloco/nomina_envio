"""
Servicio: envío de correos vía SMTP.
Adapta la lógica de smtplib/email a algo simple de usar desde los
controladores.
"""

import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSendError(Exception):
    """Se lanza cuando el envío de un correo falla, con el detalle del error."""
    pass


class EmailService:

    @staticmethod
    def _extract_numeric_amount(valor):
        if not valor or valor == "N/A":
            return 0.0
        try:
            val_clean = str(valor).replace("$.", "").replace("$", "").replace(" ", "").strip()
            if "," in val_clean and "." in val_clean:
                val_clean = val_clean.replace(".", "").replace(",", ".")
            elif "," in val_clean:
                val_clean = val_clean.replace(",", ".")
            return float(val_clean)
        except Exception:
            return 0.0

    @staticmethod
    def build_payment_email_html(nombre, datos_pago, remitente_correo="", periodo=""):
        """
        Construye el cuerpo HTML del correo con el detalle del pago ordenado y
        los botones de opción con enlaces mailto precargados.
        """
        orden_email = [
            ("unidad_administrativa", "Unidad administrativa.(tienda)"),
            ("periodo", "Periodo"),
            ("TOTAL VENTA", "Total ventas"),
            ("Gastos deducibles", "Gasto deducible"),
            ("Neto (Ventas - Gastos)", "Neto venta -gastos"),
            ("Vales", "Vales"),
            ("Sueldo", "Sueldo"),
            ("Bonificacion", "Bonificacion"),
            ("Comision encargado", "Comision encargado"),
            ("% Comision", "Porcentaje comision"),
            ("Neto a pagar", "Neto a cobrar")
        ]

        filas_html = ""
        for clave, etiqueta in orden_email:
            valor = datos_pago.get(clave, "N/A")
            
            # Tratamiento especial para el porcentaje
            if clave == "% Comision":
                valor_limpio = str(valor).replace("$.", "").replace("$", "").replace(" ", "").strip()
                if valor_limpio and valor_limpio != "N/A":
                    valor = f"{valor_limpio}%"
                else:
                    valor = "N/A"

            filas_html += (
                f"<tr>"
                f"<td style='padding:6px 12px;border:1px solid #ddd;background:#f7f7f7;'><b>{etiqueta}</b></td>"
                f"<td style='padding:6px 12px;border:1px solid #ddd;'>{valor}</td>"
                f"</tr>"
            )

        # Determinar el periodo a usar
        periodo_val = periodo if periodo else datos_pago.get("periodo", "")
        periodo_val = str(periodo_val).strip() if periodo_val else ""

        # Extraer y formatear variables para la ficha estructurada de WhatsApp
        tienda_val = datos_pago.get("unidad_administrativa", "N/A")
        total_ventas_val = datos_pago.get("TOTAL VENTA", "N/A")
        gastos_val = datos_pago.get("Gastos deducibles", "N/A")
        neto_ventas_val = datos_pago.get("Neto (Ventas - Gastos)", "N/A")
        vales_val = datos_pago.get("Vales", "N/A")
        sueldo_val = datos_pago.get("Sueldo", "N/A")
        bono_val = datos_pago.get("Bonificacion", "N/A")
        comision_val = datos_pago.get("Comision encargado", "N/A")

        pct_raw = str(datos_pago.get("% Comision", "N/A")).replace("$.", "").replace("$", "").replace(" ", "").strip()
        pct_val = f"{pct_raw}%" if pct_raw and pct_raw != "N/A" else "N/A"

        neto_cobrar_val = datos_pago.get("Neto a pagar", "N/A")
        if neto_cobrar_val == "N/A":
            neto_cobrar_val = neto_ventas_val

        mensaje_whatsapp = (
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃      REPORTE DE PAGO        ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
            f"👤 *Empleado:* {nombre}\n"
            f"🏬 *Tienda:* {tienda_val}\n"
            f"📅 *Periodo:* {periodo_val if periodo_val else 'N/A'}\n"
            "───────────────────────────────\n"
            f"• *Total ventas:* {total_ventas_val}\n"
            f"• *Gasto deducible:* {gastos_val}\n"
            f"• *Neto venta - gastos:* {neto_ventas_val}\n"
            f"• *Vales:* {vales_val}\n"
            f"• *Sueldo:* {sueldo_val}\n"
            f"• *Bonificación:* {bono_val}\n"
            f"• *Comisión encargado:* {comision_val}\n"
            f"• *Porcentaje comisión:* {pct_val}\n"
            "───────────────────────────────\n"
            f"🟢 *NETO A COBRAR:* {neto_cobrar_val}\n"
            "───────────────────────────────\n"
            "Confirmación enviada por el trabajador."
        )

        numero_whatsapp = "584228012307"
        whatsapp_encoded = urllib.parse.quote(mensaje_whatsapp)
        enlace_whatsapp = f"https://wa.me/{numero_whatsapp}?text={whatsapp_encoded}"

        return f"""
        <html>
        <body style="font-family:Arial, sans-serif; color:#333;">
            <p><b>Salam</b> Estimado(a) <b>{nombre}</b>,</p>

            <p>Por favor <b>confirmar el correo como recibido</b>.</p>
            <p>A continuación el detalle correspondiente a su pago:</p>
            <table style="border-collapse:collapse; margin-bottom:20px;">
                {filas_html}
            </table>
   
            <div id="contenedor-boton-whatsapp" style="margin-top:20px; margin-bottom:20px;">
                <a href="{enlace_whatsapp}" target="_blank" id="btn-confirmar-whatsapp" style="display:inline-block; background-color:#25D366; color:#ffffff; font-weight:bold; font-size:14px; text-decoration:none; padding:12px 22px; border-radius:6px; box-shadow:0 2px 4px rgba(0,0,0,0.15); font-family:Arial, sans-serif;">
                    💬 Solicitar tu pago AQUI.
                </a>
            </div>

            <p style="margin-top:20px;margin-left:75px;font-size:12px;">
                <b>¡ÉXITOS Y BENDICIONES!</b>
            </p>
        </body>
        </html>
        """

    @staticmethod
    def build_custom_message_html(nombre, cuerpo_texto):
        """
        Construye el cuerpo HTML de un comunicado o mensaje masivo.
        Preserva saltos de línea y formato limpio.
        """
        import html
        cuerpo_escapado = html.escape(cuerpo_texto).replace("\n", "<br>")

        return f"""
        <html>
        <body style="font-family:Arial, sans-serif; color:#333; line-height:1.6; padding:15px;">
            <p><b>Salam</b> Estimado(a) <b>{html.escape(nombre)}</b>,</p>
            <div style="margin:20px 0; font-size:14px; color:#333;">
                {cuerpo_escapado}
            </div>
            <p style="margin-top:25px; font-size:12px; color:#555;">
                <b>¡ÉXITOS Y BENDICIONES!</b>
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
