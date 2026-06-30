from PyPDF2 import PdfReader
import requests
from io import BytesIO
from langchain_community.document_loaders import PyPDFLoader

list_extracted = []

def pdf_extract_content(url_withext_pdf):
    extracted_pdf = ""
    response = requests.get(url_withext_pdf)
    response.raise_for_status()
    
    pdf_content = BytesIO(response.content)

    reader = PdfReader(pdf_content)
    for page in reader.pages:
        extracted_pdf += page.extract_text()
        list_extracted.append(extracted_pdf)

    return list_extracted
