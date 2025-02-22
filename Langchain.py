# Langchain dependencies
from langchain.document_loaders.pdf import PyPDFDirectoryLoader # Importing PDF loader from Langchain
from langchain.text_splitter import RecursiveCharacterTextSplitter # Importing text splitter from Langchain
from langchain.embeddings import OpenAIEmbeddings # Importing OpenAI embeddings from Langchain
from langchain.schema import Document # Importing Document schema from Langchain
from langchain.vectorstores.chroma import Chroma # Importing Chroma vector store from Langchain
from dotenv import load_dotenv # Importing dotenv to get API key from .env file
from langchain.chat_models import ChatOpenAI # Import OpenAI LLM
import os # Importing os module for operating system functionalities
import shutil # Importing shutil module for high-level file operations
import requests
import feedparser
import tempfile
import PyPDF2

## TODO: get the OpenAI API key from the .env file
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
                "pdf_url": entry.id.replace("http://arxiv.org/abs/", "http://arxiv.org/pdf/") + ".pdf"
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

def split_text(documents: list[Document]):
  """
  Split the text content of the given list of Document objects into smaller chunks.
  Args:
    documents (list[Document]): List of Document objects containing text content to split.
  Returns:
    list[Document]: List of Document objects representing the split text chunks.
  """
  # Initialize text splitter with specified parameters
  text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300, # Size of each chunk in characters
    chunk_overlap=100, # Overlap between consecutive chunks
    length_function=len, # Function to compute the length of the text
    add_start_index=True, # Flag to add start index to each chunk
  )

  # Split documents into smaller chunks using text splitter
  chunks = text_splitter.split_documents(documents)
  print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

  # Print example of page content and metadata for a chunk
  document = chunks[0]
  print(document.page_content)
  print(document.metadata)

  return chunks

# Path to the directory to save Chroma database
CHROMA_PATH = "chroma"
def save_to_chroma(chunks: list[Document]):
  """
  Save the given list of Document objects to a Chroma database.
  Args:
  chunks (list[Document]): List of Document objects representing text chunks to save.
  Returns:
  None
  """

  # Clear out the existing database directory if it exists
  if os.path.exists(CHROMA_PATH):
    shutil.rmtree(CHROMA_PATH)

  # Create a new Chroma database from the documents using OpenAI embeddings
  db = Chroma.from_documents(
    chunks,
    OpenAIEmbeddings(),
    persist_directory=CHROMA_PATH
  )

  # Persist the database to disk
  db.persist()
  print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")
  return db

def generate_data_store(query, max_results):
  """
  Function to generate vector database in chroma from documents.
  """
  documents = load_arxiv_documents(query, max_results) # Load documents from a source
  chunks = split_text(documents) # Split documents into manageable chunks
  db = save_to_chroma(chunks) # Save the processed data to a data store
  return db

# Generate the data store
db = generate_data_store("machine learning in healthcare", 3)
retrieved_docs = db.similarity_search("machine learning applications in healthcare", k=3)
# for doc in retrieved_docs:
#     print(f"Metadata: {doc.metadata}")
#     print(f"Content: {doc.page_content[:300]}...")  # Print first 300 characters
# generate_data_store()


print(retrieved_docs)