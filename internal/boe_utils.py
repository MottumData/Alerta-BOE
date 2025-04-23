import requests
from typing import Union, Dict, Any
from datetime import date
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate

BASE_URL = "https://www.boe.es/datosabiertos/api"

TARGET_DEPTS = {
    "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO",
    "DIRECCIÓN GENERAL DE BIODIVERSIDAD, BOSQUES Y DESERTIFICACIÓN",
    "DIRECCIÓN GENERAL DE CALIDAD Y EVALUACIÓN AMBIENTAL",
    "MINISTERIO DE AGRICULTURA, PESCA Y ALIMENTACIÓN",
    "DIRECCIÓN GENERAL DE DESARROLLO RURAL, INNOVACIÓN Y POLÍTICA FORESTAL",
    "MINISTERIO DE CIENCIA E INNOVACIÓN",
}

def ensure_list(x: Any) -> List[Any]:
    """
    Convierte un valor en lista, para unificar el tratamiento de nodos simples y múltiples.

    Args:
        x (Any): Valor que puede ser None, dict o list.

    Returns:
        List[Any]: Si x es None devuelve [], si es lista la devuelve tal cual, 
                   y si es dict o cualquier otro tipo lo encapsula en una lista de un elemento.
    """
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def get_boe_sumario(fecha: Union[str, date] = None, formato: str = "json") -> Dict[str, Any]:
    """
    Obtiene el resumen diario del BOE para una fecha concreta, llamando a la API de datos abiertos.

    Args:
        fecha (str o date, opcional): Fecha para la que queremos el sumario en formato 'YYYYMMDD' 
                                       o objeto date. Por defecto, hoy.
        formato (str, opcional): Formato de respuesta: "json" o "xml". Por defecto "json".

    Returns:
        Dict[str, Any]: Estructura de datos JSON con todo el sumario del BOE para la fecha indicada.
    """
    if fecha is None:
        fecha = date.today()
    fecha_str = fecha.strftime("%Y%m%d") if isinstance(fecha, date) else fecha
    url = f"{BASE_URL}/boe/sumario/{fecha_str}"
    resp = requests.get(url, headers={"Accept": f"application/{formato}"})
    resp.raise_for_status()
    return resp.json() if formato == "json" else resp.text

def _procesar_item(dest: Dict[str, Dict[str, Any]],
                   dept_name: str,
                   epig_name: Union[str, None],
                   item: Dict[str, Any]) -> None:
    """
    Extrae los campos relevantes de un <item> y lo añade al diccionario de resultados.

    Args:
        dest (dict): Diccionario donde acumular los ítems filtrados.
        dept_name (str): Nombre normalizado del departamento al que pertenece este ítem.
        epig_name (str o None): Nombre del epígrafe bajo el que aparece el ítem, 
                                o None si aparece “a pie” del departamento.
        item (dict): Nodo con la información del BOE (identificador, título, URLs...).

    Returns:
        None: Añade una nueva entrada en `dest` bajo la clave del identificador.
    """
    identificador = item.get("identificador")
    raw_pdf = item.get("url_pdf")
    # Algunas respuestas traen url_pdf como dict con "#text"
    if isinstance(raw_pdf, dict):
        url_pdf = raw_pdf.get("#text") or raw_pdf.get("@url")
    else:
        url_pdf = raw_pdf

    dest[identificador] = {
        "departamento": dept_name,
        "epigrafe": epig_name,
        "identificador": identificador,
        "titulo": item.get("titulo"),
        "url_pdf": url_pdf,
    }

def filtrar_items(sumario: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Filtra del sumario BOE solo los ítems que pertenezcan a los departamentos de interés.

    Recorre todas las secciones y departamentos de la respuesta, y para cada departamento
    en TARGET_DEPTS extrae:
      1) Los ítems dentro de cada <epigrafe>
      2) Los ítems definidos directamente bajo <departamento> (caso anuncios, licitaciones...)

    Args:
        sumario (dict): Estructura JSON obtenida de get_boe_sumario().

    Returns:
        Dict[str, Dict[str, Any]]: Mapa {identificador → datos del ítem}, donde cada valor
                                   incluye departamento, epígrafe (o None), título y URL PDF.
    """
    resultados: Dict[str, Dict[str, Any]] = {}

    diarios = ensure_list(sumario.get("data", {}) \
                             .get("sumario", {}) \
                             .get("diario"))
    for diario in diarios:
        for seccion in ensure_list(diario.get("seccion")):
            for dept in ensure_list(seccion.get("departamento")):
                # Normalizo y comparo el nombre
                dept_name = ((dept.get("@nombre") or dept.get("nombre", "")) \
                                .strip().upper())
                if dept_name not in TARGET_DEPTS:
                    continue

                # 1) Procesa todos los ítems dentro de cada epígrafe
                for epig in ensure_list(dept.get("epigrafe")):
                    epig_name = epig.get("@nombre") or epig.get("nombre")
                    for item in ensure_list(epig.get("item")):
                        _procesar_item(resultados, dept_name, epig_name, item)

def classify_items(items):

    template = """
        Eres un clasificador automático de disposiciones del BOE.  
        Recibirás un diccionario en JSON, donde cada clave es el identificador de un BOE y su valor es 
        un objeto con metadatos, por ejemplo:

        {{
        "BOE-A-2025-8144": {{
            "departamento": "...",
            "epigrafe": "...",
            "identificador": "BOE-A-2025-8144",
            "titulo": "...",
            "url_pdf": {{ ... }}
        }},
        // más entradas
        }}

        Tu tarea es, **solo** basándote en los campos `titulo` y `epigrafe`, decidir para cada BOE si 
        está relacionado con biodiversidad (o temas muy afines: conservación, especies protegidas, 
        espacios naturales, Red Natura 2000, ecosistema, fauna, flora, hábitat, conservación, especies 
        protegidas, restauración ecológica, parques naturales, sostenibilidad ambiental, etc...).  
        
        - Si lo está, devuelve `true`. En caso de que tengas dudas, también devuelve `true`. 
        - Si no, devuelve `false`.  

        **Formato de salida**: únicamente una lista o array JSON de objetos, cada uno con la forma:
        ```json
        [
        {{"BOE-A-2025-8144": true}},
        {{"BOE-A-2025-8145": false}},
        ...
        ]
        ```

    Aquí tiene la entrada (json):

    {text}
    
    """

    # system_prompt = load_prompt(prompt_name="ricce_prompt_para_resumen_de_pdf")

    prompt = PromptTemplate(
        input_variables=["text"],
        template=template
    )

    parser = JsonOutputParser()
    # 4. Inicializa tu LLM de Ollama
    llm = OllamaLLM(model="hdnh2006/salamandra-7b-instruct:latest",
                    temperature=0.0, 
                    base_url="http://192.168.1.134:11434")

    # 5. Monta un LLMChain que use el prompt anterior
    chain = prompt | llm | parser

    result = chain.invoke({"text": items})

    return result


if __name__ == "__main__":
    # Obtengo el sumario del BOE de hoy
    sumario = get_boe_sumario()
    # Filtrar solo los ítems de mis departamentos objetivo
    items_filtrados = filtrar_items(sumario)
    # Imprimo cada identificador con su título y enlace al PDF
    for ident, info in items_filtrados.items():
        print(f"{ident}: {info['titulo']} → {info['url_pdf']}")
