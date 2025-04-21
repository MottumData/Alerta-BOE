from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from internal.prompt_utils import load_single_pdf
from internal.prompt_utils import divide_document_into_chunks
from langchain.chains.summarize import load_summarize_chain

pdf_path = "./BOE/BOE-A-2025-1299.pdf"
documento = load_single_pdf(pdf_path)
#chunks = divide_document_into_chunks(documento)

model = OllamaLLM(model="hdnh2006/salamandra-7b-instruct:latest")

chain = load_summarize_chain(model, chain_type="stuff")

resultado = chain.invoke({"input_documents": documento})

print(resultado)