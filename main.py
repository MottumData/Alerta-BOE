import os
from dotenv import load_dotenv
import logging
from codecarbon import OfflineEmissionsTracker
import time
from internal.llm_utils import *
from internal.boe_utils import *
from internal.notification_utils import send_boe_notification_email, read_json_receivers
import json


# Logger
log_format = '[%(name)s %(levelname)s @ %(asctime)s]   %(message)s'
date_format = '%H:%M:%S'
logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("mottum")

# ENV VARS
load_dotenv()

# Definimos argumentos para el remitente del mensaje
remitente = os.getenv("SMTP_USER")
clave = os.getenv("SMTP_PASS")
body = "Un BOE diario al año nunca hace daño ;)"


# Configuracion CodeCarbon
pue = 1.12
country_iso_code = "ESP"
region = "ESP"
cloud_provider = "gcp"
cloud_region = "europe-southwest1"
country_2letter_iso_code = "ES"
emission_output_file = "codecarbon_emissions.csv"

tracker = OfflineEmissionsTracker(
    country_iso_code=country_iso_code,
    region=region,
    cloud_provider=cloud_provider,
    cloud_region=cloud_region,
    country_2letter_iso_code=country_2letter_iso_code,
    pue=pue,
    output_file=emission_output_file
)

if __name__ == "__main__":
    tracker.start()
    logger.info("Iniciando el script...")
    start_time = time.time()

    # Para la ejecución desde la API:
    sumario = get_boe_sumario(fecha="20250423")
    boe_paths = [value['url_pdf'] for value in filtrar_items(sumario).values()]

    # Para la ejecución en local desde el directorio:
    # boe_files = os.listdir("BOE")
    # boe_paths = [os.path.join("BOE", f) for f in boe_files]

    summaries = generate_summaries_from_documents(boe_paths)

    # Guardamos los resumenes en summaries.json
    output_json_file = "summaries.json"
    try:
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=4)
        logger.info(f"Summaries saved to {output_json_file}")
    except Exception as e:
        logger.error(f"Error saving summaries to JSON: {e}")

    # Formatear el diccionario de resúmenes en una cadena para el cuerpo del email
    email_body_parts = ["Resúmenes del BOE del día:\n\n"]
    for url, summary_text in summaries.items():
        if not isinstance(summary_text, str):
            summary_text = str(summary_text)

        cleaned_summary = summary_text.strip()
        email_body_parts.append(f"URL: {url}\nResumen:\n{cleaned_summary}\n\n---\n")

    email_body_string = "\n".join(email_body_parts)

    # Enviamos el email con los resumenes diarios del BOE
    receivers = read_json_receivers()
    send_boe_notification_email(
        receivers=receivers,
        body=email_body_string,
        attachment_paths=None,
        sender_email=remitente,
        password=clave
    )

    emissions = tracker.stop()
    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info("Emissions: %s kg CO₂eq", emissions)
    logger.info("Tiempo de ejecución: %.2f segundos", elapsed_time)

# TODO:
# Documentar el código (B)
# Limpieza de código innecesario (A, B)
# requirements.txt (B)
# dockerfile (A)
# Ejecucion Codecarbon  (B)
# README (A)
# Contemplar casos de errores. (No hay BOE ese dia, no hay temática ese dia, se publican mas tarde,...) (A,B)
# prompting para enfocar mejor la notificación. (A)
# prompting para estandarizar el resumen del BOE. (B)