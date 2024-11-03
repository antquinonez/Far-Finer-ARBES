from chromadb import PersistentClient
from llama_index.core import Document, Settings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.embeddings import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from typing import List, Dict, Optional
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

class EntitySkillsProcessor:
    def __init__(self, persist_dir: str = "./entity_skills_db", force_reset: bool = True):
        """
        Initialize the EntitySkillsProcessor
        
        Args:
            persist_dir: Directory for ChromaDB persistence
            force_reset: If True, forces a reset of the collection to ensure consistent embeddings
        """
        # Set up embedding function (using same model for both ChromaDB and LlamaIndex)
        self.embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        # Initialize ChromaDB with PersistentClient
        self.chroma_client = PersistentClient(path=persist_dir)
        
        # Force reset collection if requested
        if force_reset:
            try:
                self.chroma_client.delete_collection("entity_skills")
                print("Deleted existing collection to ensure consistent embeddings")
            except ValueError:
                pass
        
        # Initialize collection with the embedding function
        self.skills_collection = self.chroma_client.create_collection(
            name="entity_skills",
            get_or_create=True,
            embedding_function=self.embedding_function
        )
        
        self.vector_store = ChromaVectorStore(chroma_collection=self.skills_collection)
        
        # Set up LlamaIndex to use the same embedding model
        Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
        
        self.persist_dir = persist_dir

    def process_entity_skills(self, entity_json: Dict):
        """Process skills JSON maintaining entity relationship"""
        entity_name = entity_json.get('entity_name', 'Unknown Entity')
        skills = entity_json.get('skills_df', {}).get('value', [])
        
        # Delete existing entries for this entity
        try:
            # Get all documents with matching entity name
            existing_docs = self.skills_collection.get(
                where={"metadata.entity_name": entity_name}
            )
            
            if existing_docs and existing_docs['ids']:
                # Delete all documents for this entity
                self.skills_collection.delete(
                    ids=existing_docs['ids']
                )
                print(f"Deleted {len(existing_docs['ids'])} existing documents for entity: {entity_name}")
        except Exception as e:
            print(f"Warning: Error while trying to delete existing documents: {e}")
        
        enhanced_docs = []
        doc_ids = []
        metadatas = []
        documents = []
        
        for idx, skill_info in enumerate(skills):
            doc_id = f"{entity_name.replace(' ', '-')}-skill-{idx}"
            doc_ids.append(doc_id)
            
            # Create content
            content = f"""
            Entity: {entity_name}
            Skill: {skill_info.get('skill', '')}
            Type: {skill_info.get('type', '')}
            Evaluation: {skill_info.get('eval', '')}
            Source Details: {skill_info.get('source_details', '')}
            Labels: {', '.join(skill_info.get('labels', []))}
            """
            documents.append(content.strip())

            # Store metadata
            metadata = {
                'metadata.entity_name': entity_name,
                'metadata.skill_name': skill_info.get('skill', ''),
                'metadata.type': skill_info.get('type', ''),
                'metadata.source_details': skill_info.get('source_details', ''),
                'metadata.labels': ', '.join(skill_info.get('labels', [])),
            }
            metadatas.append(metadata)

            # Create document for LlamaIndex
            doc = Document(
                text=content.strip(),
                metadata=metadata,
                id_=doc_id
            )
            enhanced_docs.append(doc)

        # Add new documents to ChromaDB
        if documents:
            self.skills_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=doc_ids
            )
            print(f"Added {len(documents)} new documents for entity: {entity_name}")

        # Create storage context and index for LlamaIndex
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        index = VectorStoreIndex.from_documents(
            enhanced_docs,
            storage_context=storage_context,
            show_progress=True
        )
        
        return index