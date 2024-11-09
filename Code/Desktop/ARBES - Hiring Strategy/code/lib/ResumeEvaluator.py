from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import sys
import os
import json
import logging
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import Document

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..', '..')))

from lib.AI.FFAnthropicCached import FFAnthropicCached

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class ResumeEvaluator:
    """Class to evaluate resumes using Claude and specified evaluation rules."""
    
    SUPPORTED_EXTENSIONS: Set[str] = {'.pdf', '.doc', '.docx', '.txt'}
    
    def __init__(self, evaluation_rules_path: str, evaluation_steps_path: str, output_dir: str):
        """
        Initialize the resume evaluator with evaluation rules and steps.
        
        Args:
            evaluation_rules_path (str): Path to evaluation rules JSON
            evaluation_steps_path (str): Path to evaluation steps JSON
            output_dir (str): Directory for evaluation results
        """
        self.evaluation_rules = self._load_json(evaluation_rules_path)
        self.evaluation_steps = self._load_json(evaluation_steps_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.document_index = None
        self.resume_text = None
        self.current_resume_path = None
        self.stage_results = self._init_stage_results()
        
        # Initialize LLM with system instructions
        system_instructions = self._get_system_instructions()

        self.llm = FFAnthropicCached(
            config={
                "model": 'claude-3-5-haiku-latest',
                "system_instructions": system_instructions
            }
        )

    def _init_stage_results(self) -> Dict:
        """Initialize empty stage results structure."""
        return {
            1: {},  # Stage 1 results
            2: {},  # Stage 2 results
            3: {}   # Stage 3 results
        }

    def _get_system_instructions(self) -> str:
        """Extract system instructions from evaluation steps."""
        for step_name, step_info in self.evaluation_steps.items():
            if (step_info.get('Type') == 'System Instruction' and 
                step_info.get('Stage') == 0):

                system_instructions = step_info.get('Instruction', '')

                logger.debug(f"System Instruction: {system_instructions}")
                return system_instructions
        raise ValueError("System instructions not found in evaluation steps")

    def _load_json(self, file_path: str) -> Dict:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            raise

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if the file is a supported resume format."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def load_resume(self, resume_path: str) -> bool:
        """
        Load and index a resume document.
        
        Returns:
            bool: True if resume was loaded successfully, False otherwise
        """
        try:
            documents = SimpleDirectoryReader(input_files=[resume_path]).load_data()
            self.document_index = VectorStoreIndex.from_documents(documents)
            self.resume_text = "\n".join([doc.text for doc in documents])
            self.current_resume_path = resume_path
            logger.info(f"Successfully loaded and indexed resume from {resume_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading resume {resume_path}: {str(e)}")
            return False

    def _get_preferred_name(self) -> str:
        """
        Extract preferred name from evaluation results or generate a fallback name.
        
        Returns:
            str: Preferred name from evaluation or formatted timestamp if not found
        """
        # Try to get preferred name from stage 1 results
        preferred_name = self.stage_results[1].get('preferred_name', {}).get('value')
        
        if not preferred_name:
            # Fallback to the original filename without extension
            preferred_name = Path(self.current_resume_path).stem
            
        # Clean the name for file system use
        safe_name = "".join(c for c in preferred_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        return safe_name

    def evaluate_directory(self, resume_dir: str) -> List[Dict]:
        """
        Evaluate all supported resume files in the specified directory.
        
        Args:
            resume_dir (str): Directory containing resume files
            
        Returns:
            List[Dict]: List of evaluation results for each resume
        """
        resume_dir_path = Path(resume_dir)
        if not resume_dir_path.is_dir():
            raise NotADirectoryError(f"{resume_dir} is not a directory")

        results = []
        
        # Process all supported files in directory
        for file_path in resume_dir_path.iterdir():
            if self._is_supported_file(file_path):
                logger.info(f"Processing resume: {file_path}")
                
                # Reset stage results for new resume
                self.stage_results = self._init_stage_results()
                
                # Try to process the resume
                if self.load_resume(str(file_path)):
                    try:
                        # Evaluate the resume
                        evaluation_result = self.evaluate_resume()
                        results.append(evaluation_result)
                        
                        # Export results with preferred name
                        preferred_name = self._get_preferred_name()
                        output_path = self.output_dir / f"{preferred_name}_evaluation.json"
                        self.export_results(str(output_path))
                        
                    except Exception as e:
                        logger.error(f"Error evaluating resume {file_path}: {str(e)}")
                        continue

        return results

    def _prepare_evaluation_prompt(self, eval_type: str) -> str:
        """Prepare the evaluation prompt for a specific type."""
        rules = {
            name: rule for name, rule in self.evaluation_rules.items()
            if rule.get('Type') == eval_type
        }
        
        eval_instruction = next(
            (step_info.get('Instruction', '') 
             for step_name, step_info in self.evaluation_steps.items()
             if step_info.get('Type') == 'Prompt' and 
             step_info.get('Name') == f"Evaluate {eval_type.lower()}"),
            ""
        )

        prompt = (
            f"RESUME:\n{self.resume_text}\n\n"
            f"EVALUATION INSTRUCTION: {eval_instruction}\n\n"
            "EVALUATION RULES:\n"
        )
        
        for name, rule in rules.items():
            prompt += (
                f"- {name}:\n"
                f"  Description: {rule.get('Description', 'No description provided')}\n"
            )
            if rule.get('Specification'):
                prompt += f"  Specification: {rule['Specification']}\n"
            prompt += "\n"
        
        return prompt

    def _process_evaluation_response(self, response: str) -> Dict:
        """Process and validate the evaluation response."""
        try:
            clean_response = response.strip('`').replace('json\n', '').replace('\n', '')
            return json.loads(clean_response)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing evaluation response: {str(e)}")
            raise

    def evaluate_type(self, eval_type: str, stage: int) -> Dict:
        """Evaluate all rules of a specific type."""
        logger.info(f"Starting evaluation for type: {eval_type}")
        
        if not self.resume_text:
            raise ValueError("No resume has been loaded. Please load a resume first.")
        
        prompt = self._prepare_evaluation_prompt(eval_type)
        try:
            response = self.llm.generate_response(prompt)
            results = self._process_evaluation_response(response)
            self.stage_results[stage].update(results)
            return results
        except Exception as e:
            logger.error(f"Error during {eval_type} evaluation: {str(e)}")
            raise

    def evaluate_resume(self) -> Dict:
        """Perform full resume evaluation following the evaluation steps."""
        if not self.resume_text:
            raise ValueError("No resume has been loaded. Please load a resume first.")

        sorted_steps = sorted(
            self.evaluation_steps.items(),
            key=lambda x: x[1].get('Order', 999)
        )

        for step_name, step_info in sorted_steps:
            if step_info['Type'] == 'Prompt':
                logger.info(f"Executing evaluation step: {step_name}")
                eval_type = step_info.get('Name').replace('Evaluate ', '')
                stage = step_info.get('Stage', 1)
                try:
                    self.evaluate_type(eval_type, stage)
                except Exception as e:
                    logger.error(f"Error in step {step_name}: {str(e)}")
                    raise

        return self.get_combined_evaluation()

    def get_overall_score(self) -> float:
        """Calculate the overall score based on weighted Core type evaluations."""
        core_results = self.stage_results[1]
        if not core_results:
            raise ValueError("No evaluation results available")

        core_rules = {
            name: rule for name, rule in self.evaluation_rules.items()
            if rule.get('Type') == 'Core' and rule.get('is_contribute_rating_overall') == 'True'
        }

        total_weight = 0
        weighted_sum = 0

        for name, rule in core_rules.items():
            if name in core_results:
                weight = float(rule.get('Weight', 0))
                value = float(core_results[name].get('value', 0))
                weighted_sum += weight * value
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0

    def get_combined_evaluation(self) -> Dict:
        """Combine all stage results into a single evaluation result."""
        overall_score = self.get_overall_score()
        
        # Determine overall rating based on score
        rating = None
        if overall_score >= 9:
            rating = "exceptional"
        elif overall_score >= 8:
            rating = "very high"
        elif overall_score >= 7:
            rating = "high"
        elif overall_score >= 6:
            rating = "average"
        else:
            rating = "poor"

        combined_results = {
            "metadata": {
                "evaluation_date": datetime.now().isoformat(),
                "evaluation_version": "1.0",
                "resume_file": str(self.current_resume_path)
            },
            "overall_evaluation": {
                "score": round(overall_score, 2),
                "rating": rating
            },
            "stage_1": self.stage_results[1],
            "stage_2": self.stage_results[2],
            "stage_3": self.stage_results[3],
            "summary": {
                "evaluated_fields": len(self.stage_results[1]) + 
                                  len(self.stage_results[2]) + 
                                  len(self.stage_results[3]),
                "unable_to_evaluate": self.stage_results[1].get('_meta_cant_be_evaluated_df', [])
            }
        }

        return combined_results

    def export_results(self, output_path: str) -> None:
        """Export the combined evaluation results to a JSON file."""
        try:
            combined_results = self.get_combined_evaluation()
            with open(output_path, 'w') as f:
                json.dump(combined_results, f, indent=2)
            logger.info(f"Results exported to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            raise

