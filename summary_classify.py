import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama.llms import OllamaLLM

from internal.prompt_utils import load_single_pdf
from internal.prompt_utils import load_prompt

from schema.parser_models import BiodiversitySummaryParser
from langchain_core.output_parsers.pydantic import PydanticOutputParser

pdf_path = "./BOE/BOE-A-2025-1299.pdf"
documento = load_single_pdf(pdf_path)

print(documento.page_content)

system_prompt = """
Eres un asistente experto en extraer información y generar resúmenes de documentos en español, 
especialmente en formato PDF. Tienes un conocimiento avanzado en temas medioambientales, incluyendo biodiversidad.
Cuando recibas un archivo PDF en español, debes:
1. Leer el contenido completo del documento.
2. Elaborar un resumen claro y conciso del contenido general.
3. Identificar si el documento menciona el concepto de biodiversidad.
- Si sí, especifica en qué contexto aparece y qué términos relacionados se utilizan. 
- Si no, indícalo explícitamente.
4. Entregar siempre la respuesta en formato JSON, con dos claves: 
- \"Biodiversidad\": \"Sí\" o \"No\"
- \"Resumen\": Un párrafo breve resumiendo el documento.

La respuesta debe estar redactada en español. El formato de salida debe ser exclusivamente JSON. No incluyas comentarios adicionales fuera del JSON.
Ejemplos:
\"Biodiversidad\": \"Sí\",\n  \"Resumen\": \"El documento analiza políticas públicas relacionadas con la conservación ambiental en América Latina. Se menciona la biodiversidad como un eje clave para el desarrollo sostenible, destacando términos como 'ecosistemas', 'riqueza biológica' y 'servicios ecosistémicos'. 
\"Biodiversidad\": \"No\",\n  \"Resumen\": \"El documento se enfoca en la evolución del comercio internacional entre países hispanohablantes durante la última década. No se abordan temas relacionados con biodiversidad o medio ambiente.\"
"""

#system_prompt = load_prompt(prompt_name="ricce_prompt_para_resumen_de_pdf")

parser = PydanticOutputParser(pydantic_object=BiodiversitySummaryParser)
format_instructions = parser.get_format_instructions()

template = """
{system_prompt}

{format_instructions}

{text}
"""

prompt = PromptTemplate(
    input_variables=["text"],
    partial_variables={
        "system_prompt": system_prompt,
        "format_instructions": format_instructions
    },
    template=template
)

# 4. Inicializa tu LLM de Ollama
llm = OllamaLLM(model="hdnh2006/salamandra-7b-instruct:latest",
                temperature=0.0)

print("llm inicializado")

# 5. Monta un LLMChain que use el prompt anterior
chain = prompt | llm  

print("iniciando Invocación ...")
# 6. Ejecuta el chain pasándole todo el texto
result = chain.invoke({"text": documento.page_content})

# 7. Parsea la salida JSON
#output = json.loads(result["json_output"])

# 8. Muestra o devuelve el dict
print(result)
