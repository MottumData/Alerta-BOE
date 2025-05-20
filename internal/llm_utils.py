import os
import time
import logging
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import Document
from tqdm import tqdm
from typing import List, Dict, Any
from langchain_huggingface.llms import HuggingFacePipeline
import torch

load_dotenv()

logger = logging.getLogger("mottum")

# llm = HuggingFacePipeline.from_model_id(
#     model_id="google/gemma-3-4b-it",
#     task="text-generation",
#     pipeline_kwargs={"return_full_text": False, "max_new_tokens": 400},
#     # model_kwargs={
#     #     "torch_dtype": torch.float16,  # Usar float16 para reducir memoria
#     #     "load_in_8bit": True,
#     # },
#     device_map="auto",
# )


def classify_boe(
    items: Dict[str, Any]
) -> List[Dict[str, bool]]:
    """
    Clasifica disposiciones del BOE según su relación con biodiversidad.

    Args:
        items (Dict[str, Any]): Diccionario donde cada clave es el identificador de un BOE y su valor es
                                un subdiccionario con metadatos, incluyendo 'titulo' y 'epigrafe'.

    Returns:
        List[Dict[str, bool]]: Lista de diccionarios JSON, cada uno en la forma
                               {'<identificador>': <True|False>}, indicando si la disposición
                               está relacionada con biodiversidad.
    """

    template = """
        Eres un clasificador automático del Boletín Oficial del Estado.
        Recibirás un diccionario en JSON, donde cada clave es el identificador de un BOE y su valor es
        un objeto con metadatos, por ejemplo:
        
        ```json
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
        ```

        Tu tarea es, **solo** y **únicamente** basándote en los campos `titulo` y `epigrafe` , decidir para cada BOE si
        está relacionado con biodiversidad (o temas muy afines: conservación, especies protegidas,
        espacios naturales, Red Natura 2000, ecosistema, fauna, flora, hábitat, conservación, especies
        protegidas, restauración ecológica, parques naturales, sostenibilidad ambiental, etc...).

        - Si está relacionado, devuelve `true`.
        - Si no está relacionado, devuelve `false`.

        **Formato de salida**: únicamente una lista o array JSON de objetos, cada uno con la forma:
        ```json
        [
        {{"BOE-A-2025-8144": true}},
        {{"BOE-A-2025-8145": false}},
        ...
        ]
        ```

        Aquí tiene la entrada (json) sobre la que debe trabajar:
        ```json
        {text}
        ```
    """

    prompt = PromptTemplate(
        input_variables=["text"],
        template=template
    )

    parser = JsonOutputParser()
    # 4. Inicializa tu LLM de Ollama
    llm = OllamaLLM(  # model="robbiemu/salamandra:2b-instruct_bf16",
        model="llama3.1:8b-instruct-q4_K_M",
        # model="gemma3:12b",
        temperature=0.0,
        base_url=os.getenv("BASE_URL"),
    )
    # llm = HuggingFacePipeline.from_model_id(
    #     model_id="google/gemma-3-4b-it",
    #     task="text-generation",
    #     pipeline_kwargs={"return_full_text": False},
    #     # model_kwargs={
    #     #     "torch_dtype": torch.float16,  # Usar float16 para reducir memoria
    #     #     "load_in_8bit": True,
    #     # },
    #     device_map="auto",
    # )

    # 5. Monta un LLMChain que use el prompt anterior
    chain = prompt | llm | parser

    result = chain.invoke({"text": items})

    return result


def generate_summaries_from_documents(
    pdf_sources: List[str]
) -> Dict[str, str]:
    """
    Carga documentos desde una lista de URLs y devuelve un diccionario con los resúmenes.

    Args:
        urls (List[str]): Lista de URLs de los documentos a cargar.

    Returns:
        Dict[str, str]: Diccionario donde la clave es la URL y el valor es el resumen
                        generado o un mensaje de error si la carga o el resumen fallan.
    """

    summaries = {}
    total_urls = len(pdf_sources)
    logger.info(
        "Iniciando la carga y resumen de %d documentos del BOE desde la API ...", total_urls)
    for url in tqdm(pdf_sources, desc="[Procesando BOE]: ", unit="doc"):

        try:
            loader = PyPDFLoader(url)
            documents = loader.load()
            num_pages = len(documents)
            if num_pages > 25:
                logger.warning(
                    "El documento %s tiene %s páginas, excediendo el límite permitido de 25.", url, num_pages)
                summaries[url] = f"El número de páginas ({num_pages}) excede el límite permitido (25)."
            else:
                full_text = "\n\n".join(
                    [doc.page_content for doc in documents])
                summary = make_summary(full_text)
                summaries[url] = summary
        except Exception as e:
            logger.error("Error al procesar la URL %s: %s", url, str(e))
            summaries[url] = f"Error al cargar o procesar el documento: {str(e)}"

    logger.info("Carga y resumen de %d documentos completada.", len(summaries))
    return summaries


def make_summary(
    document: Document
) -> str:
    """
    Genera un resumen para un único documento Langchain.

    Args:
        document (Document): Objeto Document de Langchain que contiene 
                             todo el texto del BOE en su atributo `page_content`.

    Returns:
        str: Resumen generado según la plantilla definida, o un mensaje de error 
             si ocurre una excepción durante la generación.
    """
    # logger.info("Generando resumen para el documento {}...".format(document))
    try:

        PROMPT_TEMPLATE = """
        Role (Rol)
            Eres un experto legal especializado en legislación española vinculada a la biodiversidad, por tanto DEBES RESPONDER EN ESPAÑOL. 
            Tienes experiencia analizando disposiciones del Boletín Oficial del Estado (BOE) con un enfoque particular 
            en normas que afectan al medio ambiente, la conservación de la naturaleza y la protección de especies o hábitats.

        Instructions (Instrucciones)
            Extracción de puntos clave:
                Metadatos básicos:
                    Número de BOE y fecha de publicación.
                    Tipo de disposición (Ley, Real Decreto, Orden Ministerial, etc.).
                    Órgano emisor.
                Objeto y alcance:
                    Breve descripción del propósito de la norma.
                    Ámbito territorial y sectores afectados.
                Contenido esencial:
                    Artículos que implican cambios legislativos, nuevos marcos regulatorios o medidas específicas sobre biodiversidad.
                    Obligaciones, limitaciones, incentivos o sanciones relevantes.
                    Fechas clave (entrada en vigor, plazos de cumplimiento).
                Impacto ambiental:
                    Medidas de conservación, restauración ecológica o protección ambiental.
                    Referencias a espacios protegidos (Red Natura 2000, ZEPAs, LICs) o a especies específicas.
                Resumen ejecutivo:
                    En 2-3 frases, describe la relevancia de la disposición y su impacto sobre la biodiversidad o el medio natural.


        Context (Contexto)
            Este asistente será utilizado para revisar disposiciones legales publicadas en el BOE, con el fin de detectar y sintetizar aquellas que impactan la legislación sobre biodiversidad. No todos los textos estarán relacionados con esta temática, por lo que también debe actuar como filtro.

        Constraints (Restricciones)
            Longitud máxima: 150 palabras.
            Redacción en un único párrafo, sin espacios ni saltos de línea.
            No interpretar ni especular más allá de lo que dice el texto.
            Si el texto no tiene relación con la biodiversidad, dejarlo claro y no continuar con el análisis.
            Enfocar el análisis en medidas que introduzcan o modifiquen obligaciones legales, protecciones, restricciones o impactos sobre ecosistemas.
            Formato de texto: La respuesta debe ser en texto plano, sin utilizar ningún tipo de formato Markdown (por ejemplo, evitar el uso de `*`, `_`, `#`, `[]()`, etc.). La salida debe ser expresamente para ser mostrada directamente como texto sin formato.

        Ejemplos:
            A continuación recibirás el contenido completo de una disposición legal publicada en el Boletín Oficial del Estado (BOE).
            Los campos requeridos en la respuesta son: Título, URL, Resumen.
            
            Ejemplo del formato de respuesta tras analizar TODO un BOE:
            
            Título: Resolución de 13 de enero de 2025, de la Dirección General de Biodiversidad, Bosques y Desertificación, sobre modificación de ZEPAs marinas en la RAMPE. 
            Resumen: Se integra en la Red de Áreas Marinas Protegidas de España (RAMPE) dos nuevas ZEPAs marinas (ES0000554 y ESZZ12004) y se suprimen seis anteriores por absorción territorial. La disposición responde al artículo 6 del Real Decreto 1599/2011, modificando delimitaciones y ajustando la red a criterios UICN de categoría IV. El objetivo es reforzar la protección de corredores migratorios de aves y mejorar la coherencia ecológica de la Red Natura 2000 en aguas españolas, especialmente en Galicia y Cádiz.

        Texto completo del BOE:  
        \"\"\"  
        {document}
        \"\"\"

        """

        prompt = PromptTemplate(
            input_variables=["document"],
            template=PROMPT_TEMPLATE
        )

        llm = OllamaLLM(model="llama3.1:8b-instruct-q4_K_M",
                        base_url=os.getenv("BASE_URL"),
                        temperature=0.0,
                        max_tokens=150)
        # llm = HuggingFacePipeline.from_model_id(
        #     model_id="google/gemma-3-4b-it",
        #     task="text-generation",
        #     pipeline_kwargs={"return_full_text": False},
        #     # model_kwargs={
        #     #     "torch_dtype": torch.float16,  # Usar float16 para reducir memoria
        #     #     "load_in_8bit": True,
        #     # },
        #     # device_map="auto",
        # )

        chain = prompt | llm

        result = chain.invoke({"document": document})

        return result
    except Exception as e:
        return f"Error al generar el resumen: {str(e)}"
