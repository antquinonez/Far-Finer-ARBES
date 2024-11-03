from chromadb import PersistentClient
from llama_index.core import Document, Settings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from typing import List, Dict, Optional
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
import logging
import shutil
from chromadb.errors import InvalidDimensionException

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class EntitySkillsProcessor:
    EMBEDDING_MODEL = "text-embedding-3-large"
    EMBEDDING_DIMENSION = 1536  # Fixed dimension for text-embedding-3-large

    def __init__(self, 
                 persist_dir: str = "../entity_skills_db", 
                 force_reset: bool = False, 
                 delete_entity_names: Optional[List[str]] = None):
        """
        Initialize the EntitySkillsProcessor
        
        Args:
            persist_dir: Directory for ChromaDB persistence
            force_reset: If True, forces a reset of the entire collection. Defaults to False.
            delete_entity_names: List of entity names whose data should be deleted during initialization
        """
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        
        self.persist_dir = persist_dir
        
        # Initialize OpenAI embedding for both ChromaDB and LlamaIndex
        self.openai_ef = OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=self.EMBEDDING_MODEL
        )
        
        self.llama_ef = OpenAIEmbedding(
            model=self.EMBEDDING_MODEL,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Set the embedding model in Settings
        Settings.embed_model = self.llama_ef
        
        self._initialize_collection(force_reset)
        
        # Delete entity data if entity names are provided
        if delete_entity_names:
            for entity_name in delete_entity_names:
                self.delete_entity_data(entity_name)

    def delete_entity_data(self, entity_name: str) -> None:
        """
        Delete all data associated with a specific entity
        
        Args:
            entity_name: Name of the entity whose data should be deleted
        """
        try:
            existing_docs = self.skills_collection.get(
                where={"entity_name": entity_name}
            )
            
            if existing_docs and existing_docs['ids']:
                self.skills_collection.delete(
                    ids=existing_docs['ids']
                )
                logger.info(f"Deleted {len(existing_docs['ids'])} existing documents for entity: {entity_name}")
            else:
                logger.info(f"No existing documents found for entity: {entity_name}")
        except Exception as e:
            logger.error(f"Error while trying to delete documents for entity {entity_name}: {e}")
            raise

    def _initialize_collection(self, force_reset: bool) -> None:
        """Initialize the ChromaDB collection with proper error handling."""
        collection_name = "entity_skills"
        
        try:
            # Force delete the persist directory if force_reset
            if force_reset and os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir)
                logger.warning(f"Deleted persistence directory: {self.persist_dir}")
        except Exception as e:
            logger.error(f"Error deleting persistence directory: {e}")
            raise
        
        # Initialize ChromaDB client
        self.chroma_client = PersistentClient(path=self.persist_dir)
        
        try:
            # Always try to delete existing collection first if force_reset
            if force_reset:
                try:
                    self.chroma_client.delete_collection(collection_name)
                    logger.warning("Deleted existing collection")
                except ValueError:
                    pass
            
            # Create new collection or get existing
            self.skills_collection = self.chroma_client.create_collection(
                name=collection_name,
                embedding_function=self.openai_ef,
                metadata={"dimension": self.EMBEDDING_DIMENSION},
                get_or_create=True
            )
            
            # Verify dimension
            if self.skills_collection.metadata.get("dimension") != self.EMBEDDING_DIMENSION:
                logger.warning("Dimension mismatch detected. Forcing collection reset.")
                self.chroma_client.delete_collection(collection_name)
                self.skills_collection = self.chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=self.openai_ef,
                    metadata={"dimension": self.EMBEDDING_DIMENSION}
                )
            
        except Exception as e:
            logger.error(f"Error during collection initialization: {e}")
            raise

        self.vector_store = ChromaVectorStore(chroma_collection=self.skills_collection)

    def process_entity_skills(self, entity_json: Dict):
        """Process skills JSON maintaining entity relationship"""
        entity_name = entity_json.get('entity_name', 'Unknown Entity')
        skills = entity_json.get('skills_df', {}).get('value', [])
        
        # Delete existing entries for this entity
        self.delete_entity_data(entity_name)
        
        # Prepare new documents
        doc_ids = []
        metadatas = []
        documents = []
        
        for idx, skill_info in enumerate(skills):
            doc_id = f"{entity_name.replace(' ', '-')}-skill-{idx}"
            doc_ids.append(doc_id)
            
            content = f"""
            Entity: {entity_name}
            Skill: {skill_info.get('skill', '')}
            Type: {skill_info.get('type', '')}
            Evaluation: {skill_info.get('eval', '')}
            Source Details: {skill_info.get('source_details', '')}
            Labels: {', '.join(skill_info.get('labels', []))}
            """
            documents.append(content.strip())

            metadata = {
                'entity_name': entity_name,
                'skill_name': skill_info.get('skill', ''),
                'type': skill_info.get('type', ''),
                'source_details': skill_info.get('source_details', ''),
                'labels': ', '.join(skill_info.get('labels', [])),
            }
            metadatas.append(metadata)

        # Add new documents to ChromaDB
        if documents:
            self.skills_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=doc_ids
            )
            logger.info(f"Added {len(documents)} new documents for entity: {entity_name}")

        # Create vector store and index using the same embedding model
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        enhanced_docs = [
            Document(
                text=doc,
                metadata=meta,
                id_=id_
            ) for doc, meta, id_ in zip(documents, metadatas, doc_ids)
        ]
        
        index = VectorStoreIndex.from_documents(
            enhanced_docs,
            storage_context=storage_context,
            embed_model=self.llama_ef,
            show_progress=True
        )
        
        return index