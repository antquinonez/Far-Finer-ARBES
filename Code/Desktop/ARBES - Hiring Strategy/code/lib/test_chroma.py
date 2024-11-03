import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize ChromaDB client with persistence
client = chromadb.PersistentClient(path="../entity_skills_db")

# Initialize the OpenAI embedding function
embedding_function = OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-large"
)

def clean_metadata(metadata):
    """Remove internal metadata and keep only relevant fields"""
    relevant_fields = {
        'metadata.entity_name',
        'metadata.skill_name',
        'metadata.type',
        'metadata.source_details',
        'metadata.labels'
    }
    return {k: v for k, v in metadata.items() if k in relevant_fields}

try:
    # Get existing collection with the correct embedding function
    collection = client.get_collection(
        name="entity_skills",
        embedding_function=embedding_function
    )
    
    # Query with where filter to ensure unique entities
    query_results = collection.query(
        query_texts=["python programming"],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    # Track seen entities to avoid duplicates
    seen_entities = set()
    
    print("\n=== Python Programming Skills Results ===\n")
    
    for idx, (doc, metadata, distance) in enumerate(zip(
        query_results['documents'][0],
        query_results['metadatas'][0],
        query_results['distances'][0]
    )):
        entity_name = metadata.get('metadata.entity_name')
        
        # Skip if we've already seen this entity
        if entity_name in seen_entities:
            continue
            
        seen_entities.add(entity_name)
        
        print(f"\nResult {len(seen_entities)}:")
        print(f"Document:\n{doc.strip()}")
        print(f"\nMetadata:", json.dumps(clean_metadata(metadata), indent=2))
        print(f"Distance: {distance:.4f}")
        print("-" * 80)

except Exception as e:
    print(f"Error accessing collection: {str(e)}")