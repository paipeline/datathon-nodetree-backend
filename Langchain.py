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
import math

from load_documents import load_documents

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Path to the directory to save Chroma database
CHROMA_PATH = "chroma"

# Ensure the database directory exists
if not os.path.exists(CHROMA_PATH):
    os.makedirs(CHROMA_PATH)  # Create the directory if it doesn't exist
    print(f"Created directory: {CHROMA_PATH}")

embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002", 
    disallowed_special=()  # Allow all special tokens
)

db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

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
  # print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

  # Print example of page content and metadata for a chunk
  # document = chunks[0]
  # print(document.page_content)
  # print(document.metadata)

  return chunks

def save_to_chroma(chunks: list[Document], batch_size=400):
  """
  Save the given list of Document objects to a Chroma database.
  Args:
  chunks (list[Document]): List of Document objects representing text chunks to save.
  Returns:
  None
  """

  # # Clear out the existing database directory if it exists
  # if os.path.exists(CHROMA_PATH):
  #   shutil.rmtree(CHROMA_PATH)

  num_batches = math.ceil(len(chunks) / batch_size)
    
  for i in range(num_batches):
    batch = chunks[i * batch_size : (i + 1) * batch_size]
    db.add_documents(batch)
    db.persist()
  print('Finish saving')

def generate_data_store(query, max_results):
  """
  Function to generate vector database in chroma from documents.
  """
  documents = load_documents(query, max_results) # Load documents from a source
  chunks = split_text(documents) # Split documents into manageable chunks
  save_to_chroma(chunks) # Save the processed data to a data store
  # return db

# Generate the data store
keyword_list = ['health policy', 'healthcare costs', 'disease prediction', 
                'risk factors for diseases', 'cardiovascular disease management', 
                'AI-driven disease diagnosis', 'FDA-approved drugs', 
                'depression and anxiety treatment', 'diabetes treatment', 
                'opioid crisis and management', 'predictive analytics in healthcare', 
                'infectious disease outbreaks', 'early disease detection', 
                'large language models in healthcare', 'COVID-19 treatments', 
                'pharmaceutical regulations', 'Medicaid and Medicare data', 
                'antibiotic resistance', 'diabetes', 'Alzheimer', 'lung cancer', 
                'impact of stress on health']
for key in keyword_list:
  generate_data_store(key, 200)
# retrieved_docs = db.similarity_search("machine learning applications in healthcare", k=3)
# for doc in retrieved_docs:
#     print(f"Metadata: {doc.metadata}")
#     print(f"Content: {doc.page_content[:300]}...")  # Print first 300 characters