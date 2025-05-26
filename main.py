import os
from dotenv import load_dotenv
import logging
from codecarbon import OfflineEmissionsTracker
import time
from internal.llm_utils import *
from internal.boe_utils import *
from internal.notification_utils import *
import json
from pprint import pprint

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

    # Parámetros de entrada
    FECHA = time.strftime('%Y%m%d')

    # Ejecución desde la API
    sumario = get_boe_sumario(fecha=FECHA)
    FECHA = None if not FECHA else time.strftime('%d/%m/%Y')
    sumario_filtrado = filtrar_items(sumario)
    boe_paths = [value['url_pdf'] for value in filtrar_items(sumario).values()]
    # Fin ejecución desde la API

    # clasificacion = classify_boe(sumario_filtrado)
    # pprint(clasificacion)

    # Ejecución con los PDFs locales.
    # boe_files = os.listdir("BOE\\PDF")
    # boe_paths = [os.path.join("BOE\\PDF", f) for f in boe_files]
    # Fin ejecución con los PDFs locales.

    # Notificación
    summaries = generate_summaries_from_documents(boe_paths)

    save_summaries_to_file(summaries)

    mail_template = create_email_template(date=FECHA,
                                          summaries=summaries,
                                          depts=target_depts_to_string())

    send_boe_notification_email(
        receivers=read_json_receivers(),
        body=mail_template,
        attachment_paths=None,
        sender_email=remitente,
        password=clave
    )

    emissions = tracker.stop()
    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info("Emissions: %s kg CO₂eq", emissions)
    logger.info("Tiempo de ejecución: %.2f segundos", elapsed_time)
