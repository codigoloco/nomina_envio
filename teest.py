import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Configuración de los datos del servidor (revisa tu cPanel para los puertos)
smtp_server = "smtp.gmail.com"
port = 465  # Puerto estándar para SMTP con SSL en cPanel
sender_email = "enderbl1996@gmail.com"  # Tu usuario completo
password = "jkzscnzxdjhqdqiz"  # Tu contraseña de cPanel

receiver_email = "analista.sistemas@tiendasnuala.com"

# 2. Crear el mensaje
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = "Correo de prueba desde Python"
body = "Hola, este es un correo autenticado desde mi script de Python."
message.attach(MIMEText(body, "plain"))

try:
    # 3. CONEXIÓN SEGURA: Nos conectamos al servidor usando SSL
    server = smtplib.SMTP_SSL(smtp_server, port)
    
    # 4. AUTENTICACIÓN: Esto es lo que te exige cPanel
    server.login(sender_email, password)
    
    # 5. Enviar y cerrar
    server.sendmail(sender_email, receiver_email, message.as_string())
    print("¡Correo enviado con éxito!")

except Exception as e:
    print(f"Error al conectar o autenticar: {e}")

finally:
    try:
        server.quit()
    except:
        pass