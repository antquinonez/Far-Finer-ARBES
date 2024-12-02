import os
import json
import logging
from typing import Set, Dict, Any
from pathlib import Path
from EntitySkillsProcessor import EntitySkillsProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EvaluationResultsProcessor:
    def __init__(self, 
                results_dir: str = "../evaluation_results",
                db_dir: str = "../entity_skills_db",
                processed_log: str = "../processed_entities.txt"):
        """
        Initialize the evaluation results processor
        
        Args:
            results_dir: Directory containing evaluation result JSON files
            db_dir: Directory for ChromaDB persistence
            processed_log: File to track processed entity IDs
        """
        self.results_dir = Path(results_dir)
        self.processed_log = Path(processed_log)
        self.processed_entities: Set[str] = self._load_processed_entities()
        
        # Initialize the EntitySkillsProcessor
        self.skills_processor = EntitySkillsProcessor(
            persist_dir=db_dir,
            force_reset=False
        )

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

    def _extract_skills_from_evaluation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract skills data from evaluation result JSON into required format
        
        Args:
            data: Parsed evaluation result JSON
        
        Returns:
            Dict containing entity name and skills in required format
        """
        entity_id = data.get('content', {}).get('entity_id', {}).get('value', 'Unknown')
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
            "entity_name": entity_id,
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
                
                # Extract entity ID
                entity_id = data.get('content', {}).get('entity_id', {}).get('value')
                if not entity_id:
                    logger.warning(f"No entity ID found in file: {file_path}")
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
#     # Initialize and run processor
#     processor = EvaluationResultsProcessor()
#     processor.process_files()