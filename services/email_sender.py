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

        monto_str = str(datos_pago.get("Neto a pagar", datos_pago.get("Neto (Ventas - Gastos)", "N/A"))).strip()
        destino_correo = remitente_correo if remitente_correo else "contacto@empresa.com"
        
        # Determinar el periodo a usar en el asunto
        periodo_val = periodo if periodo else datos_pago.get("periodo", "")
        periodo_val = str(periodo_val).strip() if periodo_val else ""

        if periodo_val and periodo_val != "N/A":
            asunto_texto = f"Respuesta de Pago - {nombre} - {periodo_val}"
        else:
            asunto_texto = f"Respuesta de Pago - {nombre}"

        asunto_encoded = urllib.parse.quote(asunto_texto)


        # Asegurar prefijo de formato $.  si viene solo el número
        monto_formateado = monto_str
        if monto_formateado != "N/A" and not monto_formateado.startswith("$."):
            monto_formateado = f"$.  {monto_formateado}"

        # 1. Opción 1: Transferencia / Pago Móvil
        cuerpo_texto_op1 = (
            f"OPCIÓN DE PAGO: Transferencia / Pago Móvil\n\n"
            f"⚠️ POR FAVOR CORREGIR MONTOS ANTES DE ENVIAR EL CORREO ⚠️\n\n"
            f"Monto a Cobrar pago móvil :{monto_formateado}\n\n"
            f"Empleado: {nombre}\n\n"
            f"Confirmación enviada por el trabajador."
        )

        # 2. Opción 2: Efectivo en tienda
        cuerpo_texto_op2 = (
            f"OPCIÓN DE PAGO: Efectivo en tienda\n\n"
            f"⚠️ POR FAVOR CORREGIR MONTOS ANTES DE ENVIAR EL CORREO ⚠️\n\n"
            f"Monto a Cobrar Efectivo: {monto_formateado}\n\n"
            f"Empleado: {nombre}\n\n"
            f"Confirmación enviada por el trabajador."
        )

        # 3. Opción 3: Ahorro en caja
        cuerpo_texto_op3 = (
            f"OPCIÓN DE PAGO: Ahorro en caja\n\n"
            f"Monto guardado en caja (Ahorro): {monto_formateado}\n\n"
            f"Empleado: {nombre}\n\n"
            f"Confirmación enviada por el trabajador."
        )

        # 4. Opción 4 (NUEVO): Pago Mixto
        cuerpo_texto_op4 = (
            f"OPCIÓN DE PAGO:  Pago Móvil /Transferencia , o Efectivo $\n\n"
            f"⚠️ POR FAVOR CORREGIR MONTOS ANTES DE ENVIAR EL CORREO ⚠️\n\n"
            f"Monto a Cobrar  Efectivo   : {monto_formateado}\n"
            f"Monto a Cobrar pago móvil :{monto_formateado}\n\n"
            f"Empleado: {nombre}\n\n"
            f"Confirmación enviada por el trabajador."
        )


        mailto_op1 = f"mailto:{destino_correo}?subject={asunto_encoded}&body={urllib.parse.quote(cuerpo_texto_op1)}"
        mailto_op2 = f"mailto:{destino_correo}?subject={asunto_encoded}&body={urllib.parse.quote(cuerpo_texto_op2)}"
        mailto_op3 = f"mailto:{destino_correo}?subject={asunto_encoded}&body={urllib.parse.quote(cuerpo_texto_op3)}"
        mailto_op4 = f"mailto:{destino_correo}?subject={asunto_encoded}&body={urllib.parse.quote(cuerpo_texto_op4)}"


        return f"""
        <html>
        <body style="font-family:Arial, sans-serif; color:#333;">
            <p><b>Salam</b> Estimado(a) <b>{nombre}</b>,</p>

            <p>Por favor <b>confirmar el correo como recibido</b>.</p>
            <p>A continuación el detalle correspondiente a su pago:</p>
            <table style="border-collapse:collapse; margin-bottom:20px;">
                {filas_html}
            </table>
            
            <div id="contenedor-botones-respuesta" style="border:1px solid #ddd; padding:16px; border-radius:8px; background:#f9f9f9; max-width:270px; margin-top:20px;">
                <p style="margin-top:0; font-weight:bold; color:#333; font-size:15px;">Por favor seleccione su respuesta de pago:</p>
                
                <div style="margin-bottom:10px;">
                    <a href="{mailto_op1}" id="btn-opcion-transferencia" style="display:block; text-align:center; background:#007bff; color:#ffffff; text-decoration:none; padding:10px 8px; border-radius:5px; font-weight:bold; font-size:12px; white-space:nowrap;">
                        ✔ Transferencia / Pago Móvil
                    </a>
                </div>
                
                <div style="margin-bottom:10px;">
                    <a href="{mailto_op2}" id="btn-opcion-efectivo" style="display:block; text-align:center; background:#28a745; color:#ffffff; text-decoration:none; padding:10px 8px; border-radius:5px; font-weight:bold; font-size:12px; white-space:nowrap;">
                        ✔ Efectivo en tienda
                    </a>
                </div>

                <div style="margin-bottom:10px;">
                    <a href="{mailto_op4}" id="btn-opcion-mixto" style="display:block; text-align:center; background:#6f42c1; color:#ffffff; text-decoration:none; padding:10px 8px; border-radius:5px; font-weight:bold; font-size:12px; white-space:nowrap;">
                        ✔ Pago Mixto (Efectivo / Pago Móvil)
                    </a>
                </div>
                
                <div>
                    <a href="{mailto_op3}" id="btn-opcion-ahorro" style="display:block; text-align:center; background:#E0A96D; color:#ffffff; text-decoration:none; padding:10px 8px; border-radius:5px; font-weight:bold; font-size:12px; white-space:nowrap;">
                        ✔ Ahorro en caja
                    </a>
                </div>
            </div>



            <p style="margin-top:20px;margin-left:75px;font-size:12px;">
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
