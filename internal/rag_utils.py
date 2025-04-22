
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate


def load_documents_from_urls(urls):
    """
    Carga documentos desde una lista de URLs y devuelve un diccionario con los resúmenes.
    """
    summaries = {}
    for url in urls:
        try:
            print(f"Cargando documento desde la URL: {url}")
            loader = PyPDFLoader(url)
            print("Cargando documento...")
            documents = loader.load()
            num_pages = len(documents)
            print(f"Número de páginas: {num_pages}")

            if num_pages > 6:
                print("Número de páginas excede el límite permitido.")
                summaries[url] = "Número de páginas excede el límite permitido."
            else:
                print("Número de páginas dentro del límite permitido.")
                summaries[url] = make_summary(documents)
        except Exception as e:
            summaries[url] = f"Error al cargar el documento: {str(e)}"

    return summaries


def make_summary(document):
    """
    Genera un resumen para un documento dado.
    """
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

        prompt = PromptTemplate(
            input_variables=["document"],
            template=PROMPT_TEMPLATE
        )
        # 4. Inicializa tu LLM de Ollama
        llm = OllamaLLM(model="hdnh2006/salamandra-7b-instruct:latest",
                        base_url="http://192.168.1.134:11434",
                        temperature=0.2)

        chain = prompt | llm

        result = chain.invoke({"document": document})

        return result
    except Exception as e:
        return f"Error al generar el resumen: {str(e)}"


if __name__ == "__main__":
    document_path = "BOE\\BOE-A-2025-4822.pdf"
    document_urls = ["https://www.boe.es/boe/dias/2025/01/24/pdfs/BOE-A-2025-1299.pdf",
                     "https://www.boe.es/boe/dias/2025/03/12/pdfs/BOE-A-2025-4822.pdf"]
    print("Cargando documento desde la URL...")
    summaries = load_documents_from_urls(document_urls)
    for url, summary in summaries.items():
        print(f"Resumen para {url}:")
        print(summary)
        print("-" * 80)
