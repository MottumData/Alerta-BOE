import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama.llms import OllamaLLM

from internal.prompt_utils import load_single_pdf
from internal.prompt_utils import load_prompt

from schema.parser_models import BiodiversitySummaryParser, BOEClassificationResponse
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from internal.boe_utils import get_boe_sumario, filtrar_items


# template = """
# Role:
# Eres un analista de datos jurídicos experto en legislación ambiental y biodiversidad.
# Tu tarea es analizar títulos de documentos oficiales del BOE para determinar su relación con la biodiversidad.

# Instructions:
# Analiza un diccionario de entradas del BOE en formato dict, donde cada clave es un identificador tipo 'BOE-A-2025-XXXX' y el valor es otro diccionario con los datos del documento. Tu tarea es:
# -Extraer el identificador de cada documento.
# -Analizar el campo titulo de cada documento.
# -Determinar si el título está relacionado o no con la temática de biodiversidad.
# -Considera como relacionados aquellos títulos que incluyan términos como: ecosistema, fauna, flora, hábitat, conservación, especies protegidas, restauración ecológica, parques naturales, sostenibilidad ambiental, etc.
# -Generar como salida un JSON con la siguiente estructura para cada documento (json):

#   "identificador": "BOE-A-2025-XXXX",
#   "Biodiversidad": "sí" | "no"

# -Devuelve una lista de JSONs, uno por cada entrada.

# Context:
# Puedes agregar aquí más contexto sobre:
# -Palabras clave que consideras relacionadas con biodiversidad.
# -Si quieres entrenar un modelo sobre este análisis en el futuro.
# -En caso de que haya ambiguedad, es decir no sepas responder si el contenido trata sobre temas relacionados con la biodiversidad, responde que sí trata sobre biodiversidad.

# Constraints:
# -La salida debe ser válida en formato JSON.
# -Solo dos valores válidos para el campo "Biodiversidad": "sí" o "no".
# -No es necesario analizar el contenido del PDF, solo el título.
# -No generar explicaciones ni comentarios, solo la lista de JSONs.

# Examples:
# Entrada (json):

#   "identificador": "BOE-A-2025-8001",
#   "titulo": "Resolución sobre restauración del hábitat en zonas naturales protegidas"


# Salida (json):

#   "identificador": "BOE-A-2025-8001",
#   "Biodiversidad": "sí"

# El siguiente json del cual necesitas extraer la información es el siguiente:
# {text}

# """

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
                temperature=0.0, base_url="http://192.168.1.134:11434")

print("llm inicializado")

# 5. Monta un LLMChain que use el prompt anterior
chain = prompt | llm | parser

print("iniciando Invocación ...")

sumario = get_boe_sumario()
items_filtrados = filtrar_items(sumario)
# print(items_filtrados)

result = chain.invoke({"text": items_filtrados})

print(result)
print(type(result))
