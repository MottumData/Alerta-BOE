from codecarbon import OfflineEmissionsTracker
import time
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
    output_file=emission_output_file,
    default_cpu_power=35
)

if __name__ == "__main__":
    tracker.start()
    time.sleep(5)
    emissions = tracker.stop()
    print(f"Emissions: {emissions} kg CO₂eq")
