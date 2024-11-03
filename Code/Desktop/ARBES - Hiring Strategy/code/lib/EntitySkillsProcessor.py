from chromadb import PersistentClient
from llama_index.core import Document, Settings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from typing import List, Dict, Optional
import pandas as pd
import chromadb
import os

from dotenv import load_dotenv

load_dotenv()

class EntitySkillsProcessor:
    def __init__(self, persist_dir: str = "./entity_skills_db", openai_api_key: Optional[str] = None):
        # Initialize ChromaDB with PersistentClient
        self.chroma_client = PersistentClient(path=persist_dir)
        
        # Initialize collection without specifying embedding function - ChromaDB will use default
        self.skills_collection = self._get_or_create_collection("entity_skills")
        self.vector_store = ChromaVectorStore(chroma_collection=self.skills_collection)
        
        # Initialize LlamaIndex settings with OpenAI embeddings if API key provided
        if openai_api_key:
            self.embed_model = OpenAIEmbedding(api_key=openai_api_key)
            Settings.embed_model = self.embed_model
        
        self.persist_dir = persist_dir

    def _get_or_create_collection(self, name: str):
        # Using get_or_create=True and letting ChromaDB use default embedding function
        return self.chroma_client.create_collection(
            name=name,
            get_or_create=True
        )

    def _reset_collection(self, name: str):
        """Delete and recreate the collection"""
        try:
            self.chroma_client.delete_collection(name)
        except Exception:
            pass
        return self._get_or_create_collection(name)

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
            # If we hit a dimension mismatch, reset the collection
            if isinstance(e, chromadb.errors.InvalidDimensionException):
                print("Resetting collection due to dimension mismatch...")
                self.skills_collection = self._reset_collection("entity_skills")
        
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