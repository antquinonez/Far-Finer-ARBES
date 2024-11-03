from chromadb import PersistentClient
from llama_index.core import Document, Settings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from typing import List, Dict
import pandas as pd

class EntitySkillsProcessor:
    def __init__(self, persist_dir: str = "./entity_skills_db"):
        # Initialize ChromaDB with PersistentClient
        self.chroma_client = PersistentClient(path=persist_dir)
        self.skills_collection = self._get_or_create_collection("entity_skills")
        self.vector_store = ChromaVectorStore(chroma_collection=self.skills_collection)
        
        # Initialize LlamaIndex settings with OpenAI embeddings
        self.embed_model = OpenAIEmbedding()
        Settings.embed_model = self.embed_model
        
        self.persist_dir = persist_dir

    def _get_or_create_collection(self, name: str):
        # Using get_or_create=True to handle existing collections
        return self.chroma_client.create_collection(
            name=name,
            get_or_create=True
        )

    def process_entity_skills(self, entity_json: Dict):
        """Process skills JSON maintaining entity relationship"""
        entity_name = entity_json.get('entity_name', 'Unknown Entity')
        skills = entity_json.get('skills_df', {}).get('value', [])
        
        enhanced_docs = []
        
        for idx, skill_info in enumerate(skills):
            # Create rich text content including entity name
            content = f"""
            Entity: {entity_name}
            Skill: {skill_info.get('skill', '')}
            Type: {skill_info.get('type', '')}
            Evaluation: {skill_info.get('eval', '')}
            Source Details: {skill_info.get('source_details', '')}
            Labels: {', '.join(skill_info.get('labels', []))}
            """

            # Store metadata with proper field names for ChromaDB querying
            metadata = {
                'metadata.entity_name': entity_name,
                'metadata.skill_name': skill_info.get('skill', ''),
                'metadata.type': skill_info.get('type', ''),
                'metadata.source_details': skill_info.get('source_details', ''),
                'metadata.labels': ', '.join(skill_info.get('labels', [])),
            }

            # Create document
            doc = Document(
                text=content.strip(),
                metadata=metadata,
                id_=f"{entity_name.replace(' ', '-')}-skill-{idx}"
            )
            enhanced_docs.append(doc)

        # Create storage context and index
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        index = VectorStoreIndex.from_documents(
            enhanced_docs,
            storage_context=storage_context,
            show_progress=True
        )