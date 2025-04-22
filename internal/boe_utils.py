import requests
from datetime import date
from typing import Union, Dict, Any, List

BASE_URL = "https://www.boe.es/datosabiertos/api"

TARGET_DEPTS = {
    "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO",
    "DIRECCIÓN GENERAL DE BIODIVERSIDAD, BOSQUES Y DESERTIFICACIÓN",
    "DIRECCIÓN GENERAL DE CALIDAD Y EVALUACIÓN AMBIENTAL",
    "MINISTERIO DE AGRICULTURA, PESCA Y ALIMENTACIÓN",
    "DIRECCIÓN GENERAL DE DESARROLLO RURAL, INNOVACIÓN Y POLÍTICA FORESTAL",
    "MINISTERIO DE CIENCIA E INNOVACIÓN",
}

def ensure_list(x):
    """Convierte x a lista si es dict o None."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

def get_boe_sumario(fecha: Union[str, date] = None, formato: str = "json") -> Dict[str, Any]:
    if fecha is None:
        fecha = date.today()
    fecha_str = fecha.strftime("%Y%m%d") if isinstance(fecha, date) else fecha
    url = f"{BASE_URL}/boe/sumario/{fecha_str}"
    resp = requests.get(url, headers={"Accept": f"application/{formato}"})
    resp.raise_for_status()
    return resp.json() if formato=="json" else resp.text

def filtrar_items(sumario: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    resultados: Dict[str, Dict[str, Any]] = {}
    for diario in ensure_list(
        sumario.get("data", {}).get("sumario", {}).get("diario")
    ):
        for seccion in ensure_list(diario.get("seccion")):
            for dept in ensure_list(seccion.get("departamento")):
                dept_name = (
                    (dept.get("@nombre") or dept.get("nombre", ""))
                    .strip()
                    .upper()
                )
                if dept_name in TARGET_DEPTS:
                    for epig in ensure_list(dept.get("epigrafe")):
                        for item in ensure_list(epig.get("item")):
                            identificador = item.get("identificador")
                            # Construye tu objeto de salida
                            item_dict = {
                                "departamento": dept_name,
                                "epigrafe": epig.get("@nombre") or epig.get("nombre"),
                                "identificador": identificador,
                                "titulo": item.get("titulo"),
                                "url_pdf": (
                                    (item.get("url_pdf") or {}).get("#text")
                                    or item.get("url_pdf")
                                ),
                            }
                            # Asigna al dict por clave identificador
                            resultados[identificador] = item_dict
    return resultados



if __name__ == "__main__":
    sumario = get_boe_sumario()           
    items_filtrados = filtrar_items(sumario)
    print (items_filtrados)


