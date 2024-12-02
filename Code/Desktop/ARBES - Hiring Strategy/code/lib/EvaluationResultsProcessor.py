import os
import json
import logging
from typing import Set, Dict, Any, List, Optional
from pathlib import Path
from EntitySkillsProcessor import EntitySkillsProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EvaluationResultsProcessor:
    def __init__(self, 
                results_dir: str = "../evaluation_results",
                db_dir: str = "../entity_skills_db",
                processed_log: str = "../processed_entities.txt",
                force_reset: bool = False,
                delete_entity_names: Optional[List[str]] = None):
        """
        Initialize the evaluation results processor
        
        Args:
            results_dir: Directory containing evaluation result JSON files
            db_dir: Directory for ChromaDB persistence
            processed_log: File to track processed entity IDs
            force_reset: If True, forces a reset of the entire collection
            delete_entity_names: List of entity names to delete (can be entity_id, uuid, or preferred_name)
        """
        self.results_dir = Path(results_dir)
        self.processed_log = Path(processed_log)
        
        # If force_reset, clear the processed log
        if force_reset and self.processed_log.exists():
            self.processed_log.unlink()
            
        self.processed_entities: Set[str] = self._load_processed_entities()
        
        # Resolve any provided entity names to their canonical forms
        resolved_delete_names = None
        if delete_entity_names:
            resolved_delete_names = self._resolve_entity_names(delete_entity_names)
        
        # Initialize the EntitySkillsProcessor
        self.skills_processor = EntitySkillsProcessor(
            persist_dir=db_dir,
            force_reset=force_reset,
            delete_entity_names=resolved_delete_names
        )

    def _resolve_entity_names(self, entity_names: List[str]) -> List[str]:
        """
        Resolve provided entity names to their canonical forms by checking evaluation files
        
        Args:
            entity_names: List of entity names to resolve (could be entity_id, uuid, or preferred_name)
            
        Returns:
            List of resolved canonical entity names
        """
        resolved_names = set()
        name_mapping = {}
        
        # First, build a mapping of all possible identifiers to canonical names
        for file_path in self.results_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                content = data.get('content', {})
                
                # Get all possible identifiers
                identifiers = {
                    content.get('entity_id', {}).get('value', ''),
                    content.get('uuid', {}).get('value', ''),
                    content.get('preferred_name', {}).get('value', '')
                }
                
                # Remove empty strings
                identifiers.discard('')
                
                if identifiers:
                    # Use entity_id as canonical if available, else uuid, else preferred_name
                    canonical = (content.get('entity_id', {}).get('value') or 
                               content.get('uuid', {}).get('value') or 
                               content.get('preferred_name', {}).get('value'))
                    
                    # Map all identifiers to the canonical form
                    for identifier in identifiers:
                        name_mapping[identifier] = canonical
                        
            except Exception as e:
                logger.error(f"Error processing file {file_path} during name resolution: {e}")
                continue
        
        # Now resolve each provided name
        for name in entity_names:
            if name in name_mapping:
                resolved_names.add(name_mapping[name])
            else:
                logger.warning(f"Could not resolve entity name: {name}")
                # Include the original name as fallback
                resolved_names.add(name)
                
        return list(resolved_names)

    def _load_processed_entities(self) -> Set[str]:
        """Load the set of already processed entity IDs"""
        if not self.processed_log.exists():
            return set()
            
        with open(self.processed_log, 'r') as f:
            return set(line.strip() for line in f)

    def _save_processed_entity(self, entity_id: str) -> None:
        """Save an entity ID to the processed log"""
        with open(self.processed_log, 'a') as f:
            f.write(f"{entity_id}\n")
        self.processed_entities.add(entity_id)

    def _get_entity_identifier(self, data: Dict[str, Any]) -> str:
        """
        Get entity identifier with fallback options
        
        Args:
            data: Parsed evaluation result JSON
        
        Returns:
            Entity identifier string
        """
        content = data.get('content', {})
        
        # Try entity_id first
        entity_id = content.get('entity_id', {}).get('value')
        if entity_id:
            return entity_id
            
        # Try uuid next
        uuid = content.get('uuid', {}).get('value')
        if uuid:
            return uuid
            
        # Finally, try preferred_name
        preferred_name = content.get('preferred_name', {}).get('value')
        if preferred_name:
            return preferred_name
            
        # If none found, raise exception
        raise ValueError("No valid entity identifier found in evaluation data")

    def _extract_skills_from_evaluation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract skills data from evaluation result JSON into required format
        
        Args:
            data: Parsed evaluation result JSON
        
        Returns:
            Dict containing entity name and skills in required format
        """
        entity_name = self._get_entity_identifier(data)
        skills_df = data.get('content', {}).get('skills_df', {}).get('value', [])
        
        # Transform skills data into required format
        formatted_skills = []
        for skill in skills_df:
            skill_data = {
                "skill": skill.get("skill", ""),
                "type": skill.get("type", ""),
                "eval": skill.get("eval", ""),
                "source_details": ", ".join(skill.get("source_detail", [])),
                "labels": []
            }
            
            # # Add labels based on score and sub_type
            # if skill.get("score", 0) >= 8:
            #     skill_data["labels"].append("expert")
            # elif skill.get("score", 0) >= 6:
            #     skill_data["labels"].append("advanced")
            # elif skill.get("score", 0) >= 4:
            #     skill_data["labels"].append("intermediate")
            # else:
            #     skill_data["labels"].append("beginner")
                
            # if skill.get("sub_type") == "verified":
            #     skill_data["labels"].append("verified")
                
            formatted_skills.append(skill_data)
            
        return {
            "entity_name": entity_name,
            "skills_df": {
                "value": formatted_skills
            }
        }

    def process_files(self) -> None:
        """Process all JSON files in the results directory"""
        if not self.results_dir.exists():
            logger.error(f"Results directory not found: {self.results_dir}")
            return
            
        for file_path in self.results_dir.glob("*.json"):
            try:
                # Load and parse JSON
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Get entity identifier using fallback logic
                try:
                    entity_id = self._get_entity_identifier(data)
                except ValueError as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue
                    
                # Skip if already processed
                if entity_id in self.processed_entities:
                    logger.info(f"Skipping already processed entity: {entity_id}")
                    continue
                
                # Extract and format skills data
                formatted_data = self._extract_skills_from_evaluation(data)
                
                # Process the skills
                self.skills_processor.process_entity_skills(formatted_data)
                
                # Mark as processed
                self._save_processed_entity(entity_id)
                logger.info(f"Successfully processed entity: {entity_id}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue

# if __name__ == "__main__":
#     # Example usage with options
#     processor = EvaluationResultsProcessor(
#         force_reset=False,
#         delete_entity_names=["Someone]"]
#     )
#     processor.process_files()