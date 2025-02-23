from langchain.vectorstores import Chroma

# Define path to existing Chroma database
CHROMA_PATH = "rag/Chroma"  # Update if necessary

# Load the existing Chroma database
db = Chroma(persist_directory=CHROMA_PATH)

# Fetch all stored metadata and associated documents
all_data = db._collection.get(include=["metadatas", "documents"])

# Check the number of stored chunks/vectors
print(f"Total stored chunks: {len(all_data['metadatas'])}")

# Choose a specific chunk index (e.g., first chunk)
chunk_index = 1000  # Change this to test other chunks

# Verify metadata retrieval
if chunk_index < len(all_data["metadatas"]):
    metadata = all_data["metadatas"][chunk_index]
    document = all_data["documents"][chunk_index]
    print(f"Metadata for Chunk {chunk_index + 1}: {metadata}")
    print(f"Document Snippet: {document[:200]}...")  # Print first 200 characters for context
else:
    print("Chunk index out of range.")