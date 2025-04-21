""" Módulo con funciones para la gestión de prompts"""

import logging
from fastapi import HTTPException
import orjson as json
from .path_utils import SYSTEM_PROMPT_PATH
from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def load_single_pdf(file_path: str) -> Document:
    """
    Carga un archivo PDF, concatena todo su contenido en un único Document y, si es necesario,
    trunca el texto para que no exceda el número máximo de caracteres especificado.
    
    Args:
        file_path (str): Ruta completa del archivo PDF.
        max_chars (int): Número máximo de caracteres a incluir del PDF (por defecto: 2000).

    Returns:
        Document: Objeto Document de LangChain con el contenido del PDF.
    """
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    full_text = "\n\n".join(d.page_content for d in docs)

    metadata = docs[0].metadata.copy()
    metadata["source"] = file_path

    return Document(page_content=full_text, metadata=metadata)

if __name__ == "__main__":
    pdf_path = "./BOE/BOE-A-2025-1299.pdf" 
    documento = load_single_pdf(pdf_path)
    print("Contenido del documento (truncado a 2000 caracteres):")
    print(documento)

def divide_document_into_chunks(document: Document, chunk_size: int = 6000, chunk_overlap: int = 1000) -> list:
    """
    Divide un objeto Document en múltiples 'chunks' (fragmentos) usando RecursiveCharacterTextSplitter.

    Args:
        document (Document): Documento completo a dividir.
        chunk_size (int, opcional): Número máximo de caracteres por chunk. Por defecto 1000.
        chunk_overlap (int, opcional): Cantidad de solapamiento entre chunks para preservar contexto. Por defecto 200.

    Returns:
        List[Document]: Lista de objetos Document, cada uno representando un chunk del documento original.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # La función split_documents espera una lista de Document, por lo tanto encapsulamos 'document'.
    docs_split = splitter.split_documents([document])
    return docs_split


if __name__ == "__main__":
    pdf_path = "./BOE/BOE-A-2007-21490-consolidado.pdf"
    documento = load_single_pdf(pdf_path)
    chunks = divide_document_into_chunks(documento, chunk_size=6000, chunk_overlap=1000)
    
    print("Documento dividido en chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(chunk.page_content)


def load_prompt(file_path: str = SYSTEM_PROMPT_PATH, prompt_name: str = None):
    """ Lee un prompt o esquema específico del sistema desde un archivo JSON."""
    try:
        with open(file_path, 'rb') as file:
            prompts = json.loads(file.read())

            if prompt_name:
                logger.info("Prompt -> %s", prompt_name)
                return prompts.get(prompt_name, None)
            return prompts
    except FileNotFoundError:
        logger.info("El archivo %s no se encontró.", file_path)
        return None
    except json.JSONDecodeError:
        logger.info(
            "Error al decodificar el archivo JSON %s.", file_path)
        return None


def show_prompt(prompt_name: str = None):
    """ Muestra un prompt específico del sistema desde un archivo JSON. 
        Si no se especifica un nombre, muestra todos los prompts."""
    try:
        with open(SYSTEM_PROMPT_PATH, 'rb') as file:
            data = json.loads(file.read())
        logger.info("Prompt consultado -> %s", prompt_name)

        if prompt_name:
            logger.info("Prompt consultado -> %s", prompt_name)
            return data.get(prompt_name, None)
        logger.info("Prompts consultados -> %s", data.keys())
        return data
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"El archivo {SYSTEM_PROMPT_PATH} no se encontró.") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Error al decodificar el archivo JSON {SYSTEM_PROMPT_PATH}.") from exc