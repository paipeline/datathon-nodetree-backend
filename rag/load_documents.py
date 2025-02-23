# Langchain dependencies
from langchain.document_loaders.pdf import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores.chroma import Chroma
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
import os
import shutil
import requests
import feedparser
import tempfile
import PyPDF2

from rag.scraper_pubMed import scrape

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Directory where PDFs will be temporarily stored (can be ignored)
DATA_PATH = "./arxiv_pdfs/"  
os.makedirs(DATA_PATH, exist_ok=True)  # Ensure the directory exists

def search_arxiv(query, max_results=5):
    """
    Searches ArXiv using API and retrieves metadata & PDF URLs.
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        feed = feedparser.parse(response.text)
        papers = []
        
        for entry in feed.entries:
            papers.append({
                "id": entry.id.split("/")[-1],  # Extract paper ID
                "title": entry.title,
                "summary": entry.summary,
                "authors": ", ".join([author.name for author in entry.authors]) if "authors" in entry else "Unknown",
                "published": entry.published[:10] if "published" in entry else "Unknown",
                "pdf_url": entry.id.replace("http://arxiv.org/abs/", "http://arxiv.org/pdf/") + ".pdf" #with AI generated output for pdf
            })
        
        return papers
    else:
        print(f"Error: {response.status_code}")
        return []

def download_and_extract_text_pypdf2(pdf_url):
    """
    Downloads a PDF from ArXiv and extracts full text using PyPDF2.
    """
    response = requests.get(pdf_url)
    
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(response.content)
            temp_pdf_path = temp_pdf.name

        # Extract text using PyPDF2
        full_text = []
        with open(temp_pdf_path, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)

        return "\n".join(full_text).strip()
    
    return None

def load_arxiv_documents(query, max_results=5):
    """
    Fetches ArXiv papers, extracts PDF text, and returns LangChain Document objects.
    """
    papers = search_arxiv(query, max_results)

    documents = []
    for paper in papers:
        full_text = download_and_extract_text_pypdf2(paper["pdf_url"])
        
        if full_text:
            documents.append(
                Document(
                    page_content=full_text,  # Store full-text from PDF
                    metadata={
                        "title": paper["title"],
                        "authors": paper["authors"],
                        "published": paper["published"],
                        "pdf_url": paper["pdf_url"]
                    }
                )
            )
            print(f"Loaded: {paper['title']}")
        else:
            print(f"Failed to extract: {paper['title']}")
    
    return documents

# get all data sources from the internet
def load_documents(query, limit):
    arxiv_documents = load_arxiv_documents(query, limit)
    pubmed_documents = scrape(query, limit)
    documents = arxiv_documents + pubmed_documents
    return documents