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
        'entity_name',
        'skill_name',
        'type',
        'source_details',
        'labels'
    }
    return {k: v for k, v in metadata.items() if k in relevant_fields}

try:
    # Get existing collection with the correct embedding function
    collection = client.get_collection(
        name="entity_skills",
        embedding_function=embedding_function
    )
    
    # Search for some SKILL
    skill_query = "AWS"
    all_results = collection.query(
        query_texts=[skill_query],
        n_results=20,  # Increase this to ensure we get enough results
        include=["documents", "metadatas", "distances"]
    )
    
    # Track entities and their best matching skills
    entity_results = {}
    
    # Process results and keep the best match per entity
    for idx, (skill_text, metadata, distance) in enumerate(zip(
        all_results['documents'][0],
        all_results['metadatas'][0],
        all_results['distances'][0]
    )):
        entity_name = metadata.get('entity_name')
        
        # If we haven't seen this entity or this is a better match
        if entity_name not in entity_results or distance < entity_results[entity_name]['distance']:
            entity_results[entity_name] = {
                'skill': skill_text,
                'metadata': metadata,
                'distance': distance
            }
    
    # Sort entities by their best match distance
    sorted_entities = sorted(entity_results.items(), key=lambda x: x[1]['distance'])
    
    print(f"\n=== Entities with {skill_query.title()}-related Skills ===\n")
    
    # Print the top 5 entities (or all if less than 5)
    for i, (entity_name, result) in enumerate(sorted_entities[:5], 1):
        print(f"\nResult {i} - Entity: {entity_name}")
        print(f"Skill: {result['skill']}")
        print(f"Metadata:", json.dumps(clean_metadata(result['metadata']), indent=2))
        print(f"Distance: {result['distance']:.4f}")
        print("-" * 80)
    
    print(f"\nTotal unique entities found: {len(entity_results)}")

except Exception as e:
    print(f"Error accessing collection: {str(e)}")
    raise