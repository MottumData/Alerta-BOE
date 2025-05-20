
from dotenv import load_dotenv
import logging
import smtplib
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json


logger = logging.getLogger("mottum")


def read_json_receivers():
    """
    Lee un fichero JSON y devuelve la lista de destinatarios de correo.

    Args:
        json_path (str): Ruta al fichero JSON que contiene la clave "receivers"
                         con la lista de direcciones de email.

    Returns:
        List[str]: Lista de correos extraídos del campo "receivers".
                   Si la lista está vacía o no existe, lanza ValueError.
    """

    json_path = "destinatarios.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        receivers: List[str] = data.get("receivers", [])
        if not receivers:
            raise ValueError(f"No se encontraron destinatarios en {json_path}")
        return receivers


def send_boe_notification_email(
    attachment_paths: List[str],
    sender_email: str,
    password: str,
    body: str,
    subject: str = "Notificación diaria del Boletín Oficial del Estado (BOE)",
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    receivers: List[str] = read_json_receivers(),
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
    # for path in attachment_paths:
    #     part = MIMEBase("application", "octet-stream")
    #     with open(path, "rb") as f:
    #         part.set_payload(f.read())
    #     encoders.encode_base64(part)
    #     part.add_header(
    #         "Content-Disposition",
    #         f'attachment; filename="{os.path.basename(path)}"'
    #     )
    #     msg.attach(part)

    # Establecemos conexión con el servidor SMTP y enviamos
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receivers, msg.as_string())
        logger.info(f"Correo enviado a: {', '.join(receivers)}")


def save_summaries_to_file(summaries: dict) -> None:
    """
    Guarda los resúmenes en un archivo JSON.

    Args:
        summaries (dict): Diccionario con los resúmenes a guardar.

    Returns:
        None
    """

    output_json_file = "summaries.json"
    try:
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=4)
            logger.info("Summaries saved to %s", output_json_file)
    except Exception as e:
        logger.error("Error saving summaries to JSON: %s", e)


def create_email_template(date, summaries, depts) -> str:
    # Formatear el diccionario de resúmenes en una cadena para el cuerpo del email
    email_body_parts = [f"Resúmenes del día {date} para {len(summaries.items())} BOE\n\n",
                        depts,
                        "\n\n*********************************\n"]
    for url, summary_text in summaries.items():
        if not isinstance(summary_text, str):
            summary_text = str(summary_text)  # Convierte a cadena si no lo es

        cleaned_summary = summary_text.strip()

        email_body_parts.append(
            f"BOE: {url}\n{cleaned_summary}\n\n*********************************\n")

    email_body_string = "\n".join(email_body_parts)
    return email_body_string

# TODO-Adjuntar BOE de los del resumen
