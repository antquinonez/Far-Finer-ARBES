import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize ChromaDB client with persistence
client = chromadb.PersistentClient(path="entity_skills_db")

# Initialize the OpenAI embedding function matching your setup
embedding_function = OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-large"
)

try:
    # Get existing collection with the correct embedding function
    collection = client.get_collection(
        name="entity_skills",
        embedding_function=embedding_function
    )
    
    # Example query - adjust the query text as needed
    query_results = collection.query(
        query_texts=["python programming"],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    # Print results
    for idx, (doc, metadata, distance) in enumerate(zip(
        query_results['documents'][0],
        query_results['metadatas'][0],
        query_results['distances'][0]
    )):
        print(f"\nResult {idx + 1}:")
        print(f"Document: {doc}")
        print(f"Metadata: {metadata}")
        print(f"Distance: {distance:.4f}")

except Exception as e:
    print(f"Error accessing collection: {str(e)}")