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
    return resp.json() if formato == "json" else resp.text


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

# if __name__ == "__main__":
#     sumario = get_boe_sumario(20250421)
#     items_filtrados = filtrar_items(sumario)
#     item_clasificados = classify_items(items_filtrados)
#     print(item_clasificados)
