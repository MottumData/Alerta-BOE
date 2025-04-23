import smtplib
import os
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import json

def send_boe_notification_email(
    receivers: List[str],
    attachment_paths: List[str],
    sender_email: str,
    password: str,
    body: str,
    subject: str = "Notificación diaria: BOEs de biodiversidad",
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587
) -> None:
    """
    Envía un email con varios adjuntos a una lista de destinatarios.

    Args:
        receivers (List[str]): Lista de direcciones de correo de los destinatarios.
        attachment_paths (List[str]): Lista de rutas de archivos a adjuntar.
        sender_email (str): Dirección de correo del remitente.
        password (str): Contraseña o token de la cuenta de correo del remitente.
        subject (str, opcional): Asunto del correo. Por defecto "Notificación diaria: BOEs de biodiversidad".
        body (str, opcional): Cuerpo del mensaje en texto plano. Por defecto "Nuevo día, nuevo BOE biodiversidad en lo alto".
        smtp_server (str, opcional): Servidor SMTP. Por defecto "smtp.gmail.com".
        smtp_port (int, opcional): Puerto del servidor SMTP. Por defecto 587.

    Returns:
        None: Envía el correo y no devuelve nada. Lanza excepción en caso de error de envío.
    """
    # Construcción del mensaje multipart
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(receivers)
    msg["Subject"] = subject

    # Añadimos el cuerpo del mensaje
    msg.attach(MIMEText(body, "plain"))

    # Adjuntamos cada archivo de la lista
    for path in attachment_paths:
        part = MIMEBase("application", "octet-stream")
        with open(path, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(path)}"'
        )
        msg.attach(part)

    # Establecemos conexión con el servidor SMTP y enviamos
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receivers, msg.as_string())
        print(f"Correo enviado a: {', '.join(receivers)}")

if __name__ == "__main__":

    load_dotenv()

    json_path = os.path.join(os.path.dirname(__file__), "destinatarios.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        receivers: List[str] = data.get("receivers", [])
        if not receivers:
            raise ValueError(f"No se encontraron destinatarios en {json_path}")
        
    mis_adjuntos = [
        "./BOE/BOE-A-2025-1299.pdf",
        "./BOE/BOE-A-2025-4822.pdf"
    ]

    remitente = os.getenv("SMTP_USER")
    clave = os.getenv("SMTP_PASS")

    body = "Un BOE diario al año nunca hace daño ;)"

    send_boe_notification_email(
        receivers=receivers,
        body = body,
        attachment_paths=mis_adjuntos,
        sender_email=remitente,
        password=clave
    )
