import os
import logging
from codecarbon import OfflineEmissionsTracker
import time
from internal.llm_utils import *
from internal.boe_utils import *
import json


log_format = '[%(name)s %(levelname)s @ %(asctime)s]   %(message)s'
date_format = '%H:%M:%S'
logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("mottum")

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

    
    # Descomentar para ejecutar desde la API
    sumario = get_boe_sumario(fecha="20250422")
    # clasificacion = classify_boe(sumario)
    # print(clasificacion)
    boe_paths = [value['url_pdf'] for value in filtrar_items(sumario).values()]

    # Descomentar para ejecutar desde el directorio
    # boe_files = os.listdir("BOE")
    # boe_paths = [os.path.join("BOE", f) for f in boe_files]

    summaries = generate_summaries_from_documents(boe_paths)

    # Save summaries to a JSON file
    output_json_file = "summaries.json"
    try:
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=4)
        logger.info(f"Summaries saved to {output_json_file}")
    except Exception as e:
        logger.error(f"Error saving summaries to JSON: {e}")

    emissions = tracker.stop()
    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info("Emissions: %s kg CO₂eq", emissions)
    logger.info("Tiempo de ejecución: %.2f segundos", elapsed_time)
# TODO:
# Preparar directorio con 10 BOES (5 biodiversidad y 5 no biodiversidad) pdf y xml (B)
# Documentar el código (B)
# Limpieza de código innecesario (A, B)
# requirements.txt (B)
# dockerfile (A)
# Ejecucion Codecarbon  (B)
# README (A)
# .env (B)
# Contemplar casos de errores. (No hay BOE ese dia, no hay temática ese dia, se publican mas tarde,...) (A,B)
# prompting para enfocar mejor la notificación. (A)
