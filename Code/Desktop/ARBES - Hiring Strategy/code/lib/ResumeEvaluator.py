from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import sys
import os
import json
import logging
import shutil
from operator import itemgetter
from dotenv import load_dotenv
import time
from itertools import groupby
import backoff
from concurrent.futures import ThreadPoolExecutor, as_completed

from llama_index.core import VectorStoreIndex
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import Document

from .ResumeSkillsTransformer import ResumeSkillsTransformer

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
    BATCH_SIZE = 4
    
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
        self.llm = None
        
    def _load_json(self, file_path: str) -> Dict:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            raise

    def _init_stage_results(self) -> Dict[int, Dict]:
        """Initialize empty stage results structure with integer keys."""
        return {
            1: {},  # Stage 1 results
            2: {},  # Stage 2 results
            3: {}   # Stage 3 results
        }

    def _get_base_instructions(self) -> str:
        """Get base system instructions with resume content."""
        base_instruction = next(
            (step_info.get('Instruction', '') 
             for step_name, step_info in self.evaluation_steps.items()
             if step_info.get('Type') == 'System Instruction' and 
             step_info.get('Stage') == 0),
            ""
        )
        
        if not base_instruction:
            raise ValueError("System instructions not found in evaluation steps")
        
        system_instructions = (
            "=============================\n"
            "BASE SYSTEM INSTRUCTIONS\n"
            "=============================\n"
            f"{base_instruction}\n"
            "=============================\n"
        )

        if self.resume_text:
            system_instructions = (
                f"{system_instructions}\n"
                "==================================================\n"
                "RESUME TEXT\n"
                "==================================================\n"
                f"{self.resume_text}\n"
            )
        else:
            raise ValueError("Resume text must be loaded before getting system instructions")
            
        return system_instructions

    def _sort_rules_by_stage_and_order(self) -> List[Tuple[str, Dict]]:
        """Sort evaluation rules by stage and order, handling string-to-int conversion."""
        rules_with_metadata = [
            (name, rule) for name, rule in self.evaluation_rules.items()
            if not name.startswith('_')  # Skip meta fields
        ]
        
        return sorted(
            rules_with_metadata,
            key=lambda x: (
                int(x[1].get('Stage', '1')),  # Convert string stage to int
                int(x[1].get('Order', '1'))    # Convert string order to int
            )
        )

    def _get_model_for_rule(self, rule: Dict[str, Any]) -> str:
        """Get the appropriate model for a given rule."""
        models = rule.get('Model', ['claude-3-5-haiku-latest'])
        return models[0] if models else 'claude-3-5-haiku-latest'

    def _should_clear_history(self, rule: Dict[str, Any]) -> bool:
        """Check if conversation history should be cleared for this rule."""
        hist_handling = rule.get('Hist Handling', [])
        return 'pre_clear' in hist_handling

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if the file is a supported resume format."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=300
    )
    def load_resume(self, resume_path: str) -> bool:
        """Load and index a resume document."""
        try:
            documents = SimpleDirectoryReader(input_files=[resume_path]).load_data()
            self.document_index = VectorStoreIndex.from_documents(documents)
            self.resume_text = "\n".join([doc.text for doc in documents])
            self.current_resume_path = resume_path
            
            # Initialize LLM if needed
            self._init_llm()
            
            logger.info(f"Successfully loaded and indexed resume from {resume_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading resume {resume_path}: {str(e)}")
            return False

    def _init_llm(self) -> None:
        """Initialize the LLM client if not already initialized."""
        if not self.resume_text:
            raise ValueError("Resume text must be loaded before initializing LLM")
            
        if self.llm is None:
            system_instructions = self._get_base_instructions()
            self.llm = FFAnthropicCached(config={
                "system_instructions": system_instructions,
                "temperature": 0.5,
                "max_tokens": 4000
            })

    def _get_rule_stage(self, rule: Dict) -> int:
        """Helper method to consistently get stage as integer."""
        try:
            return int(rule.get('Stage', '1'))
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid stage value in rule, defaulting to 1: {str(e)}")
            return 1

    def _group_rules_for_batching(self, rules: List[Tuple[str, Dict]]) -> List[List[Tuple[str, Dict]]]:
        """Group rules by model that can be batched together."""
        # First, filter for rules that can be batched (have pre_clear history handling)
        batchable_rules = [
            (name, rule) for name, rule in rules
            if "pre_clear" in rule.get('Hist Handling', [])
        ]
        
        # Group by model and stage
        def get_group_key(rule_tuple):
            return (
                rule_tuple[1].get('Model', ['default'])[0],
                self._get_rule_stage(rule_tuple[1])
            )
        
        sorted_rules = sorted(batchable_rules, key=get_group_key)
        batches = []
        
        # Group by both model and stage
        for (model, stage), group in groupby(sorted_rules, key=get_group_key):
            group_list = list(group)
            
            # Split into batches of BATCH_SIZE
            for i in range(0, len(group_list), self.BATCH_SIZE):
                batch = group_list[i:i + self.BATCH_SIZE]
                batches.append(batch)
        
        logger.debug(f"Created {len(batches)} batches from {len(rules)} rules")
        return batches

    def _evaluate_batch(self, batch: List[Tuple[str, Dict]], model: str) -> Dict[str, Any]:
        """Evaluate a batch of rules together."""
        try:
            # Clear conversation history before batch
            self.llm.clear_conversation()
            
            combined_prompt = self._prepare_batch_prompt(batch)
            
            @backoff.on_exception(
                backoff.expo,
                Exception,
                max_tries=3,
                max_time=300,
                giveup=lambda e: not isinstance(e, Exception) or not str(e).startswith('429')
            )
            def execute_batch():
                return self.llm.generate_response(
                    prompt=combined_prompt,
                    model=model
                )
            
            response = execute_batch()
            results = self._process_evaluation_response(response)
            
            # Validate results structure
            for rule_name, rule in batch:
                if rule_name in results:
                    result = results[rule_name]
                    if not isinstance(result, dict) or 'type' not in result:
                        logger.warning(f"Result for {rule_name} missing standard structure")
                        results[rule_name] = {
                            "type": rule.get('Type', 'Core'),
                            "sub_type": rule.get('Sub_Type', 'None'),
                            "value": result,
                            "eval": f"Evaluated from {rule_name}",
                            "source": ["resume"],
                            "source_detail": ["Document content"]
                        }
            
            # Update stage results
            for rule_name, rule in batch:
                stage = self._get_rule_stage(rule)
                logger.debug(f"Processing rule {rule_name} for stage {stage}")
                
                if rule_name in results:
                    if stage not in self.stage_results:
                        logger.error(f"Invalid stage {stage} for rule {rule_name}")
                        self._add_to_cannot_evaluate(
                            rule_name,
                            rule,
                            f"Invalid stage: {stage}"
                        )
                        continue
                        
                    self.stage_results[stage][rule_name] = results[rule_name]
                    logger.debug(f"Added result for {rule_name} to stage {stage}")
                else:
                    logger.warning(f"No result found for {rule_name} in batch response")
                    self._add_to_cannot_evaluate(
                        rule_name, 
                        rule,
                        "No result in batch response"
                    )
            
            # Add sleep between batches to avoid rate limits        
            time.sleep(5)
                
            return results
        
        except Exception as e:
            logger.error(f"Error evaluating batch: {str(e)}", exc_info=True)
            for rule_name, rule in batch:
                self._add_to_cannot_evaluate(
                    rule_name,
                    rule,
                    f"Batch evaluation failed: {str(e)}"
                )
            raise

    def _prepare_batch_prompt(self, batch: List[Tuple[str, Dict]]) -> str:
        """Prepare a combined prompt for batch evaluation."""
        prompt = "Please evaluate the following attributes together:\n\n"
        
        for rule_name, rule in batch:
            prompt += (
                f"Attribute Name: {rule_name}\n"
                f"Description: {rule.get('Description', '')}\n"
            )
            if rule.get('Specification'):
                prompt += f"Specification: {rule['Specification']}\n"
            prompt += "\n"
            
        prompt += "\nPlease provide your evaluation in JSON format with results for each attribute."
        
        return prompt

    def _prepare_single_rule_prompt(self, rule_name: str, rule: Dict[str, Any]) -> str:
        """Prepare evaluation prompt for a single rule."""
        prompt = (
            f"Please evaluate the following attribute:\n\n"
            f"Attribute Name: {rule_name}\n"
            f"Description: {rule.get('Description', '')}\n"
        )
        
        if rule.get('Specification'):
            prompt += f"Specification: {rule['Specification']}\n"
            
        prompt += "\nPlease provide your evaluation in JSON format."
        
        return prompt

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
        max_time=300
    )
    def _evaluate_single_rule(self, rule_name: str, rule: Dict[str, Any], use_steps: bool = True) -> Dict:
        """Evaluate a single rule with backoff retry logic."""
        if self.llm is None:
            self._init_llm()
            
        if self._should_clear_history(rule):
            self.llm.clear_conversation()
        
        model = self._get_model_for_rule(rule)
        
        if use_steps:
            matching_step = next(
                (step for step in self.evaluation_steps.values()
                 if step.get('Type') == 'Prompt' and 
                 step.get('Stage') == rule.get('Stage', 1) and
                 step.get('Type') == rule.get('Type')),
                None
            )
            
            prompt = matching_step.get('Instruction', '') if matching_step else self._prepare_single_rule_prompt(rule_name, rule)
        else:
            prompt = self._prepare_single_rule_prompt(rule_name, rule)
            
        try:
            response = self.llm.generate_response(prompt, model=model)
            results = self._process_evaluation_response(response)
            
            stage = rule.get('Stage', 1)
            self.stage_results[stage][rule_name] = results.get(rule_name, {})
            
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule_name}: {str(e)}")
            self._add_to_cannot_evaluate(rule_name, rule, str(e))
            raise

    def _process_evaluation_response(self, response: str) -> Dict:
        """Process and validate the evaluation response."""
        try:
            json_text = response[response.find('{'):response.rfind('}')+1]
            logger.debug(f"Processing evaluation response. Raw text length: {len(response)}")
            logger.debug(f"Extracted JSON text: {json_text}")
            
            results = json.loads(json_text)
            
            # Add standard structure to any results that are missing it
            for field_name, field_value in results.items():
                rule = self.evaluation_rules.get(field_name, {})
                
                # If the result is just a value without the standard structure
                if not isinstance(field_value, dict) or not all(key in field_value for key in ['type', 'value']):
                    structured_value = {
                        "type": rule.get('Type', 'Core'),
                        "sub_type": rule.get('Sub_Type', 'None'),
                        "value": field_value,
                        "eval": f"Evaluated from {field_name}",
                        "source": ["resume"],
                        "source_detail": ["Document content"]
                    }
                    
                    # Add weight if it exists in rules
                    if 'Weight' in rule and rule['Weight'] != 'Not Applicable':
                        try:
                            structured_value["weight"] = float(rule['Weight'])
                        except (ValueError, TypeError):
                            pass
                            
                    results[field_name] = structured_value
            
            logger.debug(f"Parsed evaluation results: {json.dumps(results, indent=2)}")
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing evaluation response: {str(e)}")
            logger.error(f"Problematic text: {json_text}")
            raise

    def _add_to_cannot_evaluate(self, rule_name: str, rule: Dict, reason: str) -> None:
        """Add a rule to the list of items that couldn't be evaluated."""
        cannot_evaluate_item = {
            "field_name": rule_name,
            "Type": rule.get('Type', 'Unknown'),
            "SubType": rule.get('Sub_Type', 'Unknown'),
            "reason": reason
        }
        
        stage = self._get_rule_stage(rule)
        if '_meta_cant_be_evaluated_df' not in self.stage_results[stage]:
            self.stage_results[stage]['_meta_cant_be_evaluated_df'] = []
            
        self.stage_results[stage]['_meta_cant_be_evaluated_df'].append(cannot_evaluate_item)
        logger.debug(f"Added {rule_name} to cannot_evaluate list with reason: {reason}")

    def _get_preferred_name(self) -> str:
        """Extract preferred name from evaluation results or generate a fallback name."""
        preferred_name = self.stage_results[1].get('preferred_name', {}).get('value')
        
        if not preferred_name:
            preferred_name = Path(self.current_resume_path).stem
            
        safe_name = "".join(c for c in preferred_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        return safe_name

    def evaluate_resume(self, use_steps: bool = True) -> Dict:
        """Perform full resume evaluation with batching."""
        logger.info(f"Starting resume evaluation for {self.current_resume_path}")
        
        if not self.resume_text:
            raise ValueError("No resume has been loaded. Please load a resume first.")
            
        # Clear any existing stage results
        self.stage_results = self._init_stage_results()
        logger.debug("Initialized empty stage results")
        
        # Reset LLM conversation history
        if self.llm:
            self.llm.clear_conversation()

        try:
            sorted_rules = self._sort_rules_by_stage_and_order()
            logger.debug(f"Sorted {len(sorted_rules)} rules for evaluation")
            
            # Process rules by stage to maintain evaluation order
            for stage in [1, 2, 3]:
                stage_rules = [
                    (name, rule) for name, rule in sorted_rules
                    if self._get_rule_stage(rule) == stage
                ]
                
                if not stage_rules:
                    logger.debug(f"No rules found for stage {stage}")
                    continue
                    
                logger.debug(f"Processing {len(stage_rules)} rules for stage {stage}")
                
                # Group rules that can be batched for this stage
                batches = self._group_rules_for_batching(stage_rules)
                logger.debug(f"Grouped rules into {len(batches)} batches")
                
                # Track which rules are included in batches
                batched_rules = {
                    rule_name 
                    for batch in batches 
                    for rule_name, _ in batch
                }
                
                # Process batches for this stage
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = []
                    
                    for batch_idx, batch in enumerate(batches):
                        if not batch:
                            continue
                            
                        model = batch[0][1].get('Model', ['claude-3-5-haiku-latest'])[0]
                        logger.debug(f"Submitting batch {batch_idx + 1}/{len(batches)} "
                                f"with {len(batch)} rules using model {model}")
                        
                        futures.append(
                            executor.submit(
                                self._evaluate_batch,
                                batch,
                                model
                            )
                        )
                        
                        # Add delay between submitting batches
                        time.sleep(2)
                    
                    # Wait for all batch evaluations in this stage to complete
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            logger.debug(f"Batch evaluation completed with {len(result)} results")
                            logger.debug(f"Stage {stage} results after batch: "
                                    f"{json.dumps(self.stage_results[stage], indent=2)}")
                        except Exception as e:
                            logger.error(f"Batch evaluation failed: {str(e)}", exc_info=True)
                            continue
                
                # Process remaining rules individually
                remaining_rules = [
                    (name, rule) for name, rule in stage_rules
                    if name not in batched_rules
                ]
                
                for rule_name, rule in remaining_rules:
                    try:
                        self._evaluate_single_rule(rule_name, rule, use_steps)
                        stage = self._get_rule_stage(rule)
                        logger.debug(f"Stage {stage} results after individual evaluation: "
                                f"{json.dumps(self.stage_results[stage], indent=2)}")
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"Error evaluating {rule_name}: {str(e)}", exc_info=True)
                        self._add_to_cannot_evaluate(
                            rule_name,
                            rule,
                            f"Individual evaluation failed: {str(e)}"
                        )
                        
                # Add delay between stages
                time.sleep(3)

            logger.info("Resume evaluation completed, getting combined results")
            return self.get_combined_evaluation()
            
        except Exception as e:
            logger.error(f"Error during resume evaluation: {str(e)}", exc_info=True)
            raise

    def get_overall_score(self) -> float:
        """Calculate the overall score based on weighted Core type evaluations."""
        logger.debug("Starting overall score calculation")
        
        core_results = self.stage_results[1]
        logger.debug(f"Stage 1 results: {json.dumps(core_results, indent=2)}")
        
        if not core_results:
            logger.warning("No stage 1 results available for scoring")
            raise ValueError("No evaluation results available")

        core_rules = {
            name: rule for name, rule in self.evaluation_rules.items()
            if rule.get('Type') == 'Core' 
            and rule.get('is_contribute_rating_overall') == 'True'
            and rule.get('value_type') in ('Integer', 'Decimal')
        }
        
        logger.debug(f"Found {len(core_rules)} core rules that contribute to overall score")
        logger.debug(f"Core rules: {list(core_rules.keys())}")

        total_weight = 0
        weighted_sum = 0

        for name, rule in core_rules.items():
            if name in core_results:
                try:
                    weight = float(rule.get('Weight', 0))
                    value = float(core_results[name].get('value', 0))
                    weighted_sum += weight * value
                    total_weight += weight
                    logger.debug(f"Rule {name}: weight={weight}, value={value}, " 
                            f"weighted_sum={weighted_sum}, total_weight={total_weight}")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Skipping non-numeric value for {name}: {str(e)}")
                    continue
            else:
                logger.debug(f"Core rule {name} not found in results")

        if total_weight <= 0:
            logger.warning("No valid weighted scores found, returning 0")
            return 0.0

        final_score = weighted_sum / total_weight
        logger.debug(f"Calculated overall score: {final_score}")
        
        return final_score

    def get_combined_evaluation(self) -> Dict:
        """Combine all stage results into a single evaluation result."""
        logger.debug("Starting to combine evaluation results")
        logger.debug(f"Stage results before combination: {json.dumps(self.stage_results, indent=2)}")
        
        try:
            overall_score = self.get_overall_score()
        except Exception as e:
            logger.error(f"Error calculating overall score: {str(e)}", exc_info=True)
            overall_score = 0
        
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

        logger.debug(f"Determined rating '{rating}' for score {overall_score}")

        # Initialize content section by collecting all attributes from stages
        content = {}
        
        # Get all unique attribute names from evaluation rules
        attribute_names = {
            name for name, rule in self.evaluation_rules.items()
            if not name.startswith('_')  # Skip meta fields
        }
        
        # Process each attribute from any stage
        for attr_name in attribute_names:
            # Look for the attribute in each stage
            for stage in [1, 2, 3]:
                if attr_name in self.stage_results[stage]:
                    stage_value = self.stage_results[stage][attr_name]
                    
                    # Handle different data structures
                    if isinstance(stage_value, dict) and "value" in stage_value:
                        # Already has value wrapper
                        content[attr_name] = stage_value
                    elif isinstance(stage_value, list):
                        # List needs value wrapper
                        content[attr_name] = {"value": stage_value}
                    else:
                        # Other types just get copied
                        content[attr_name] = stage_value
                    
                    logger.debug(f"Added {attr_name} from stage {stage} to content")
                    break  # Use first occurrence if found in multiple stages

        combined_results = {
            "metadata": {
                "evaluation_date": datetime.now().isoformat(),
                "source_file": str(self.current_resume_path)
            },
            "overall_evaluation": {
                "score": round(overall_score, 2),
                "rating": rating
            },
            "content": content,
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
        
        logger.debug(f"Initial combined results: {json.dumps(combined_results, indent=2)}")

        # Transform data from stages and merge into integrated structure
        try:
            logger.debug("Starting data transformation")
            transformer = ResumeSkillsTransformer(combined_results)
            integrated_results = transformer.create_integrated_json()
            logger.debug(f"Transformed results: {json.dumps(integrated_results, indent=2)}")
            return integrated_results
        except Exception as e:
            logger.error(f"Error during data transformation: {str(e)}", exc_info=True)
            return combined_results

    def evaluate_directory(self, resume_dir: str) -> List[Dict]:
        """Evaluate all supported resume files in directory."""
        resume_dir_path = Path(resume_dir)
        if not resume_dir_path.is_dir():
            raise NotADirectoryError(f"{resume_dir} is not a directory")

        results = []
        
        # Get list of supported files first
        resume_files = [
            f for f in resume_dir_path.iterdir()
            if self._is_supported_file(f)
        ]
        
        logger.info(f"Found {len(resume_files)} supported resume files to process")
        
        for file_path in resume_files:
            logger.info(f"Processing resume: {file_path}")
            
            try:
                # Reset state for new resume
                self.resume_text = None
                self.current_resume_path = None
                self.stage_results = self._init_stage_results()
                
                if self.llm:
                    self.llm.clear_conversation()
                
                # Load and evaluate resume
                if self.load_resume(str(file_path)):
                    logger.debug("Resume loaded successfully")
                    evaluation_result = self.evaluate_resume()
                    results.append(evaluation_result)
                    
                    # Export results
                    preferred_name = self._get_preferred_name()
                    output_path = self.output_dir / f"{preferred_name}_evaluation.json"
                    self.export_results(str(output_path))
                    logger.debug(f"Results exported to {output_path}")
                    
                    # Add delay between resumes
                    time.sleep(2)
                else:
                    logger.error(f"Failed to load resume: {file_path}")
                    
            except Exception as e:
                logger.error(f"Error processing resume {file_path}: {str(e)}", exc_info=True)
                continue

        logger.info(f"Successfully processed {len(results)} out of {len(resume_files)} resumes")
        return results

    def export_results(self, output_path: str) -> None:
        """Export the combined evaluation results and move processed resume."""
        try:
            # Export the evaluation results
            combined_results = self.get_combined_evaluation()
            logger.debug(f"Exporting combined results: {json.dumps(combined_results, indent=2)}")
            
            with open(output_path, 'w') as f:
                json.dump(combined_results, f, indent=2)
            logger.info(f"Results exported to {output_path}")
            
            # Move the processed resume to the 'processed' folder
            if self.current_resume_path:
                resume_path = Path(self.current_resume_path)
                processed_dir = resume_path.parent / 'processed'
                
                # Create processed directory if it doesn't exist
                processed_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate destination path
                dest_path = processed_dir / resume_path.name
                
                # Handle case where file with same name exists in processed folder
                counter = 1
                while dest_path.exists():
                    new_name = f"{resume_path.stem}_{counter}{resume_path.suffix}"
                    dest_path = processed_dir / new_name
                    counter += 1
                
                # Move the file
                shutil.move(str(resume_path), str(dest_path))
                logger.info(f"Moved processed resume to {dest_path}")
                
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}", exc_info=True)
            raise

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

    def evaluate_type(self, eval_type: str, stage: int) -> Dict:
        """Evaluate all rules of a specific type."""
        logger.info(f"Starting evaluation for type: {eval_type}")
        
        if not self.resume_text:
            raise ValueError("No resume has been loaded. Please load a resume first.")

        # Get all rules of the specified type and stage
        type_rules = {
            name: rule for name, rule in self.evaluation_rules.items()
            if rule.get('Type') == eval_type and 
            rule.get('Stage', 1) == stage
        }
        
        # Sort rules by order
        sorted_rules = sorted(
            type_rules.items(),
            key=lambda x: int(x[1].get('Order', 1))
        )
        
        results = {}
        for rule_name, rule in sorted_rules:
            try:
                rule_result = self._evaluate_single_rule(rule_name, rule)
                results.update(rule_result)
            except Exception as e:
                logger.error(f"Error during {eval_type} evaluation for {rule_name}: {str(e)}")
                self._add_to_cannot_evaluate(rule_name, rule, str(e))

        return results

# def main():
#     """Main function to run the resume evaluation."""
#     # Configure logging
#     logging.basicConfig(level=logging.INFO)
    
#     # Initialize evaluator
#     evaluator = ResumeEvaluator(
#         evaluation_rules_path="candidate_evaluation_rules.json",
#         evaluation_steps_path="candidate_evaluation_steps.json",
#         output_dir="evaluation_results"
#     )
    
#     # Process resumes
#     results = evaluator.evaluate_directory("resumes")
    
#     print(f"Processed {len(results)} resumes")
#     return results

# if __name__ == "__main__":
#     results = main()