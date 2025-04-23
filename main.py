from codecarbon import OfflineEmissionsTracker
from internal.rag_utils import *
from internal.boe_utils import *
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
    # tracker.start()
    sumario = get_boe_sumario()
    items_filtrados = filtrar_items(sumario)
    # print("Items filtrados:")
    # print(items_filtrados)
    list_urls = []
    for name_boe, value in items_filtrados.items():
        list_urls.append(value['url_pdf']['texto'])
    
    summaries = load_documents_from_urls(list_urls)
    print("-" * 80)
    for url, summary in summaries.items():
            print(f"Resumen para {url}:")
            print(summary)
            print("-" * 80)

    # emissions = tracker.stop()
    # print(f"Emissions: {emissions} kg CO₂eq")
# TODO:
# Preparar directorio con 10 BOES (5 biodiversidad y 5 no biodiversidad) pdf y xml
# Prepara prueba para ejecutar los del directorio y los de URL por fecha.
# Documentar el código
# Logs
# Limpieza de codigo innecesario
# requirements.txt
# dockerfile
# Ejecucion Codecarbon
# README
# .env
# Contemplar casos de errores. (No hay BOE ese dia, no hay tematica ese dia, se publican mas tarde,...)
# prompting para enfocar mejor la notificacion.
