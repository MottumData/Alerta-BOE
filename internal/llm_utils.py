import os
import time
import logging
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from tqdm import tqdm

load_dotenv()

logger = logging.getLogger("mottum")


def classify_boe(items):

    template = """
        Eres un clasificador automático del Boletín Oficial del Estado.
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
    llm = OllamaLLM(#model="robbiemu/salamandra:2b-instruct_bf16",
                    model="hdnh2006/salamandra-7b-instruct:latest",
                    # model="gemma3:12b",
                    temperature=0.0,
                    base_url=os.getenv("BASE_URL"),
                    format="json")

    # 5. Monta un LLMChain que use el prompt anterior
    chain = prompt | llm | parser

    result = chain.invoke({"text": items})

    return result


def generate_summaries_from_documents(pdf_sources):
    """
    Carga documentos PDF desde una lista de URLs, genera un resumen para cada uno
    y devuelve un diccionario con los resultados.
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
            if num_pages > 15:
                logger.warning(
                    "El documento %s tiene %s páginas, excediendo el límite permitido de 15.", url, num_pages)
                summaries[url] = f"El número de páginas ({num_pages}) excede el límite permitido (15)."
            else:
                full_text = "\n\n".join([doc.page_content for doc in documents])
                summary = make_summary(full_text)
                summaries[url] = summary
        except Exception as e:
            logger.error("Error al procesar la URL %s: %s", url, str(e))
            summaries[url] = f"Error al cargar o procesar el documento: {str(e)}"

    logger.info("Carga y resumen de %d documentos completada.", len(summaries))
    return summaries


def make_summary(document):
    """
    Genera un resumen para un documento dado.
    # TODO - Documentar
    """
    logger.info("Generando resumen para el documento {}...".format(document))
    try:
        PROMPT_TEMPLATE = """
        Haz un resumen del documento.
        El resumen debe incluir los puntos más importantes y relevantes del documento.
        El resumen debe ser breve y conciso, pero lo suficientemente informativo como para que el
        lector entienda el contenido del documento.

        La respuesta debe ser en Castellano con la siguiente estructura:
        1. Título del documento.
        2. Resumen muy breve pero contenido con los enunciados de los cambios más relevantes.

        Documento:
        {document}
        """
        PROMPT_TEMPLATE = """
        Eres un asistente experto en legislación española. Te proporcionaré el texto completo de un
        Boletín Oficial del Estado (BOE). Tu tarea es extraer y presentar de forma concisa los puntos
        clave relacionados con:

        1. Metadatos básicos:
        - Número de BOE y fecha de publicación.
        - Tipo de disposición (Ley, Real Decreto, Orden Ministerial, Resolución, etc.).
        - Órgano emisor.

        2. Objeto y alcance:
        - Breve descripción del propósito principal de la norma.
        - Ámbito territorial y sectores afectados.

        3. Contenido esencial:
        - Principales artículos o apartados que introducen novedades relevantes.
        - Medidas, prohibiciones u obligaciones destacadas.
        - Plazos y fechas de entrada en vigor.

        4. Impacto en biodiversidad (si aplica):
        - Medidas específicas de conservación, restauración o gestión ambiental.
        - Referencia a espacios protegidos (p.ej. Red Natura 2000) o especies.

        5. Resumen ejecutivo:
        - En dos o tres frases, describe la esencia de la disposición y su relevancia.

        Instrucciones del formato de salida:
        - **IMPORTANTE: La respuesta completa NO DEBE EXCEDER las 150 palabras.**
        - Todo en un único párrafo, sin saltos de línea.
        - No añadas información que no esté en el texto proporcionado.
        - Sé breve y directo en cada punto.
        ---
        Texto completo del BOE:
        \"\"\"
        {document}
        \"\"\"

        """

        # PROMPT_TEMPLATE = """
        #  Role (Rol)
        #     Eres un experto legal especializado en legislación española vinculada a la biodiversidad.
        #     Tienes experiencia analizando disposiciones del Boletín Oficial del Estado (BOE) con un enfoque particular
        #     en normas que afectan al medio ambiente, la conservación de la naturaleza y la protección de especies o hábitats.

        # Instructions (Instrucciones)
        #     Analiza el texto completo de un BOE proporcionado y realiza las siguientes tareas:
        #     Identificación temática:
        #         Determina si la disposición está relacionada directa o indirectamente con la biodiversidad (conservación, restauración ambiental, especies protegidas, espacios naturales, etc.).
        #         Si no está relacionada, indícalo claramente al inicio y concluye el análisis.
        #     Extracción de puntos clave (solo si el BOE sí está relacionado):
        #         Metadatos básicos:
        #             Número de BOE y fecha de publicación.
        #             Tipo de disposición (Ley, Real Decreto, Orden Ministerial, etc.).
        #             Órgano emisor.
        #         Objeto y alcance:
        #             Breve descripción del propósito de la norma.
        #             Ámbito territorial y sectores afectados.
        #         Contenido esencial:
        #             Artículos que implican cambios legislativos, nuevos marcos regulatorios o medidas específicas sobre biodiversidad.
        #             Obligaciones, limitaciones, incentivos o sanciones relevantes.
        #             Fechas clave (entrada en vigor, plazos de cumplimiento).
        #         Impacto ambiental:
        #             Medidas de conservación, restauración ecológica o protección ambiental.
        #             Referencias a espacios protegidos (Red Natura 2000, ZEPAs, LICs) o a especies específicas.
        #         Resumen ejecutivo:
        #             En 2-3 frases, describe la relevancia de la disposición y su impacto sobre la biodiversidad o el medio natural.

        # Context (Contexto)
        #     Este asistente será utilizado para revisar disposiciones legales publicadas en el BOE, con el fin de detectar y sintetizar aquellas que impactan la legislación sobre biodiversidad. No todos los textos estarán relacionados con esta temática, por lo que también debe actuar como filtro.

        # Constraints (Restricciones)
        #     Longitud máxima: 150 palabras.
        #     Redacción en un único párrafo, sin espacios ni saltos de línea.
        #     No interpretar ni especular más allá de lo que dice el texto.
        #     Si el texto no tiene relación con la biodiversidad, dejarlo claro y no continuar con el análisis.
        #     Enfocar el análisis en medidas que introduzcan o modifiquen obligaciones legales, protecciones, restricciones o impactos sobre ecosistemas.

        # Texto completo del BOE:
        # \"\"\"
        # {document}
        # \"\"\"

        # """

        prompt = PromptTemplate(
            input_variables=["document"],
            template=PROMPT_TEMPLATE
        )
        llm = OllamaLLM(model="hdnh2006/salamandra-7b-instruct:latest",
                        base_url=os.getenv("BASE_URL"),
                        temperature=0.0,
                        max_tokens=150)

        chain = prompt | llm

        result = chain.invoke({"document": document})

        return result
    except Exception as e:
        return f"Error al generar el resumen: {str(e)}"
