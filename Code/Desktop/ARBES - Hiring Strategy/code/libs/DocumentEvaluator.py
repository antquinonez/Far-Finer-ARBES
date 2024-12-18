from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, date
from abc import ABC, abstractmethod
import sys
import os
import json
import logging
import shutil
import time
import backoff
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import groupby
from typing import List, Tuple, Dict
import textwrap
import re

from llama_index.core import VectorStoreIndex
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import Document

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..', '..')))

# Import AI providers
from lib.AI.FFAI_AzureOpenAI import FFAI_AzureOpenAI as AI
from lib.AI.FFAzureOpenAI import FFAzureOpenAI

from libs.FieldFormatter import FieldFormatter
from libs.OutputTextCleaner import OutputTextCleaner
from libs.InputTextCleaner import InputTextCleaner
from libs.SafeJSONEncoder import SafeJSONEncoder, safe_json_loads, safe_json_dumps


# Configure logging
logger = logging.getLogger(__name__)

class EvaluationStrategy(ABC):
    """Base strategy for evaluation rule processing"""
    
    def __init__(self, evaluator: 'DocumentEvaluator'):
        self.evaluator = evaluator
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def process_rules(self, rules: List[Tuple[str, Dict]], stage: int) -> Dict[str, Any]:
        """Process a set of rules for a given stage"""
        pass

class BatchEvaluationStrategy(EvaluationStrategy):
    """Strategy for batch processing of rules"""
    
    def process_rules(self, rules: List[Tuple[str, Dict]], stage: int) -> Dict[str, Any]:
        batches = self.evaluator._group_rules_for_batching(rules)
        results = {}
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            
            for batch_idx, batch in enumerate(batches):
                if not batch:
                    continue
                    
                model = batch[0][1].get('Model', [self.evaluator.DEFAULT_MODEL])[0]
                logger.debug(f"Submitting batch {batch_idx + 1}/{len(batches)} "
                              f"with {len(batch)} rules using model {model}")
                
                futures.append(
                    executor.submit(
                        self.evaluator._evaluate_batch,
                        batch,
                        model
                    )
                )
                time.sleep(2)
            
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.update(batch_results)
                except Exception as e:
                    logger.error(f"Batch evaluation failed: {str(e)}", exc_info=True)
                    
        return results

class IndividualEvaluationStrategy(EvaluationStrategy):
    """Strategy for individual processing of rules"""
    
    def process_rules(self, rules: List[Tuple[str, Dict]], stage: int) -> Dict[str, Any]:
        results = {}
        
        for rule_name, rule in rules:
            try:
                rule_result = self.evaluator._evaluate_single_rule(rule_name, rule)
                results.update(rule_result)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error evaluating {rule_name}: {str(e)}", exc_info=True)
                self.evaluator._add_to_cannot_evaluate(
                    rule_name,
                    rule,
                    f"Individual evaluation failed: {str(e)}"
                )
                
        return results

class DocumentEvaluator:
    """Enhanced document evaluator with strategy pattern"""
    
    SUPPORTED_EXTENSIONS: Set[str] = {'.pdf', '.doc', '.docx', '.txt', '.py'}
    BATCH_SIZE = 4
    DEFAULT_MODEL = 'gpt-4'
    
    def __init__(self, evaluation_rules_path: str, evaluation_steps_path: str, output_dir: str):
        """Initialize the document evaluator"""
        self.evaluation_rules = self._load_json(evaluation_rules_path)
        self.evaluation_steps = self._load_json(evaluation_steps_path)

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.document_index = None
        self.document_text = None
        self.current_document_path = None
        self.stage_results = self._init_stage_results()
        self.llm = None
        
        # Initialize evaluation strategies
        self.batch_strategy = BatchEvaluationStrategy(self)
        self.individual_strategy = IndividualEvaluationStrategy(self)

    def _get_evaluation_rules(self):
        try:
            # Check if evaluation_rules exists and is a dictionary
            if not hasattr(self, 'evaluation_rules') or not isinstance(self.evaluation_rules, dict):
                raise AttributeError("evaluation_rules not properly initialized")
            
            return self.evaluation_rules

        except Exception as e:
            raise Exception(f"Error getting data dependency: {str(e)}")

    def _get_all_data_dependencies(self):
        try:
            # Check if evaluation_rules exists and is a dictionary
            if not hasattr(self, 'evaluation_rules') or not isinstance(self.evaluation_rules, dict):
                raise AttributeError("evaluation_rules not properly initialized")
            
            # Create a new dictionary containing only Data Dependencies where they exist
            data_dependencies = {}
            for attr_name, rules in self.evaluation_rules.items():
                if 'Data Dependency' in rules:
                    data_dependencies[attr_name] = rules['Data Dependency']
            
            return data_dependencies
            
        except Exception as e:
            raise Exception(f"Error getting data dependency: {str(e)}")

    def get_data_dependency(self, attr_name):
        try:
            # Check if evaluation_rules exists and is a dictionary
            if not hasattr(self, 'evaluation_rules') or not isinstance(self.evaluation_rules, dict):
                raise AttributeError("evaluation_rules not properly initialized")
                
            # Check if attr_name exists in evaluation_rules
            if attr_name not in self.evaluation_rules:
                raise KeyError(f"Attribute '{attr_name}' not found in evaluation rules")
                
            # Check if 'Data Dependency' key exists
            if 'Data Dependency' not in self.evaluation_rules[attr_name]:
                raise KeyError(f"'Data Dependency' not found for attribute '{attr_name}'")
                
            return self.evaluation_rules[attr_name]['Data Dependency']
            
        except Exception as e:
            raise Exception(f"Error getting data dependency: {str(e)}")


    def _load_json(self, file_path: str) -> Dict:
        """Load and parse a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return safe_json_loads(f.read())
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            raise

    def _init_stage_results(self) -> Dict[int, Dict]:
        """Initialize empty stage results structure"""
        return {1: {}, 2: {}, 3: {}}

    def _get_base_instructions(self) -> str:
        """Get base system instructions with document to be evaluated content"""
        base_instruction = next(
            (step_info.get('Instruction', '') 
             for step_name, step_info in self.evaluation_steps.items()
             if step_info.get('Type') == 'System Instruction' and 
             step_info.get('Stage') == 0),
            ""
        )
        
        if not base_instruction:
            raise ValueError("System instructions not found in evaluation steps")
        
        todays_date = date.today().strftime("%Y-%m-%d")
        
        system_instructions = (
            "===================================================================================================\n"
            f"\nTODAY'S DATE: {todays_date}\n"
            "===================================================================================================\n"
            "BASE SYSTEM INSTRUCTIONS\n"
            "===================================================================================================\n"
            f"{base_instruction}\n"
            "===================================================================================================\n"
            f"OUTPUT ENCODING: ISO-8859-1\n"
            "===================================================================================================\n"
        )

        if self.document_text:
            system_instructions = (
                f"{system_instructions}\n"
                "\n===================================================================================================\n"
                "DOCUMENT TO BE EVALUATED TEXT\n"
                "===================================================================================================\n"
                f"{self.document_text}\n"
                "===================================================================================================\n"
                "END OF DOCUMENT TO BE EVALUATED TEXT\n"
                "===================================================================================================\n"
            )
        else:
            raise ValueError("Document to be evaluated text must be loaded before getting system instructions")
            
        return system_instructions

    def _get_ai(self, system_instructions: str = None) -> AI:
        """Initialize the AI client"""
        azure_client = FFAzureOpenAI(config={
            "system_instructions": system_instructions,
            "temperature": 0.5,
            "infer_o1": True,
            "max_tokens": 16384
        })
        return AI(azure_client)

    def _sort_rules_by_stage_and_order(self) -> List[Tuple[str, Dict]]:
        """Sort evaluation rules by stage and order"""
        rules_with_metadata = [
            (name, rule) for name, rule in self.evaluation_rules.items()
            if not name.startswith('_')
        ]
        
        sorted_rules_with_metadata = sorted(
            rules_with_metadata,
            key=lambda x: (
                int(x[1].get('Stage', '1')),
                int(x[1].get('Order', '1'))
            )
        )
        
        logger.debug(f"Sorted rules: {sorted_rules_with_metadata}")
        return sorted_rules_with_metadata

    def _get_rule_stage(self, rule: Dict) -> int:
        """Get rule stage as integer"""
        try:
            return int(rule.get('Stage', '1'))
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid stage value in rule, defaulting to 1: {str(e)}")
            return 1

    def _group_rules_for_batching(self, rules: List[Tuple[str, Dict]]) -> List[List[Tuple[str, Dict]]]:
        """Group rules that can be batched together"""
        logger.debug(f"Grouping rules for batching: {rules}")
        
        batchable_rules = [
            (name, rule) for name, rule in rules
            if "pre_clear" in rule.get('Hist Handling', [])
        ]
        
        def get_group_key(rule_tuple):
            return (
                rule_tuple[1].get('Model', ['default'])[0],
                self._get_rule_stage(rule_tuple[1])
            )
        
        sorted_rules = sorted(batchable_rules, key=get_group_key)
        batches = []
        
        for (model, stage), group in groupby(sorted_rules, key=get_group_key):
            group_list = list(group)
            for i in range(0, len(group_list), self.BATCH_SIZE):
                batch = group_list[i:i + self.BATCH_SIZE]
                batches.append(batch)
        
        logger.debug(f"Batches: {batches}")
        return batches

    def _evaluate_batch(self, batch: List[Tuple[str, Dict]], model: str) -> Dict[str, Any]:
        """Evaluate a batch of rules together"""
        logger.info(f"Evaluating batch with {len(batch)} rules")

        # create a tuple with the rule names -- we'll use this as the prompt_name
        rules = []
        for rule_name in batch:
            rules.append(rule_name)
        rules = tuple(rules)

        try:
            self.llm.clear_conversation()
            combined_prompt, history_items = self._prepare_batch_prompt(batch)
            
            @backoff.on_exception(
                backoff.expo,
                Exception,
                max_tries=3,
                max_time=300,
                giveup=lambda e: not isinstance(e, Exception) or not str(e).startswith('429')
            )
            def execute_batch():
                response = self.llm.generate_response(
                    prompt=combined_prompt,
                    prompt_name=rules,
                    model=model,
                    history=history_items,
                    dependencies=self._get_all_data_dependencies()
                )
                
                # Add validation for empty response
                if not response or response.isspace():
                    logger.error("Received empty response from LLM")
                    raise ValueError("Empty response received from LLM")
                    
                return response
            
            try:
                response = execute_batch()
                results = self._process_evaluation_response(response)
                
                for rule_name, rule in batch:
                    if rule_name in results:
                        stage = self._get_rule_stage(rule)
                        self.stage_results[stage][rule_name] = results[rule_name]
                    else:
                        self._add_to_cannot_evaluate(
                            rule_name, 
                            rule,
                            "No result in batch response"
                        )
                
                time.sleep(5)
                return results
                
            except ValueError as ve:
                # Handle empty response specifically
                logger.error(f"Batch execution failed: {str(ve)}")
                for rule_name, rule in batch:
                    self._add_to_cannot_evaluate(
                        rule_name,
                        rule,
                        f"Failed to get valid response: {str(ve)}"
                    )
                # Try evaluating rules individually as fallback
                return self._evaluate_batch_fallback(batch, model)
                
        except Exception as e:
            logger.error(f"Error evaluating batch: {str(e)}", exc_info=True)
            for rule_name, rule in batch:
                self._add_to_cannot_evaluate(
                    rule_name,
                    rule,
                    f"Batch evaluation failed: {str(e)}"
                )
            # Try fallback to individual evaluation
            return self._evaluate_batch_fallback(batch, model)

    def _evaluate_batch_fallback(self, batch: List[Tuple[str, Dict]], model: str) -> Dict[str, Any]:
        """Fallback method to evaluate batch rules individually"""
        logger.info("Attempting individual evaluation fallback for failed batch")
        results = {}
        
        for rule_name, rule in batch:
            try:
                # Add delay between individual evaluations
                time.sleep(2)
                rule_result = self._evaluate_single_rule(rule_name, rule, use_steps=False)
                results.update(rule_result)
            except Exception as e:
                logger.error(f"Fallback evaluation failed for {rule_name}: {str(e)}")
                self._add_to_cannot_evaluate(
                    rule_name,
                    rule,
                    f"Fallback evaluation failed: {str(e)}"
                )
        
        return results

    def _prepare_batch_prompt(self, batch: List[Tuple[str, Dict]]) -> Tuple[str, List]:
        """
        Prepare a combined prompt for batch evaluation with improved formatting.
        
        Args:
            batch: List of tuples containing (rule_name, rule_dict) pairs
            
        Returns:
            Tuple[str, list]: Formatted prompt string and data dependencies
        """
        formatter = FieldFormatter()
        prompt = ["Please evaluate the following attributes together:\n"]
        data_dependencies = []
        
        for rule_name, rule in batch:
            # Add header with proper spacing
            prompt.append(f"\n=========================== {rule_name} ===========================\n")
            
            # Core fields in consistent order
            core_fields = [
                ("Attribute Name", rule_name),
                ("Type", rule.get('Type')),
                ("Sub_Type", rule.get('Sub_Type')),
                ("Value Type", rule.get('value_type')),
                ("Weight", rule.get('Weight')),
                ("is_contribute_rating_overall", rule.get('is_contribute_rating_overall')),
                ("Description", rule.get('Description'))
            ]
            
            # Format each core field
            for field_name, value in core_fields:
                formatted = formatter.format_field(field_name, value)
                if formatted:
                    prompt.append(formatted)

            prompt.append('')

            # Handle Specification separately
            if 'Specification' in rule:
                spec = rule['Specification']
                formatted = formatter.format_field("Specification", spec)
                if formatted:
                    prompt.append(formatted)
            
            # Handle Data Dependencies
            deps = rule.get('Data Dependency', [])
            if deps:
                formatted = formatter.format_field("Data Dependencies", deps)
                if formatted:
                    prompt.append(formatted)
                data_dependencies.extend(deps)
                
            prompt.append('')  # Add blank line between attributes
        
        prompt.append("\nPlease provide your evaluation in JSON format with results for each attribute.")
        
        return '\n'.join(prompt), data_dependencies

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
        max_time=300
    )
    def _evaluate_single_rule(self, rule_name: str, rule: Dict[str, Any], use_steps: bool = True) -> Dict:
        """Evaluate a single rule"""
        logger.debug(f"Evaluating rule: {rule_name}")
        logger.debug(f"Rule: {rule}")
        logger.debug(f"Use steps: {use_steps}")
        
        if self.llm is None:
            self._init_llm()

        # get Data Dependency (history) for the Rule
        history_items = rule.get('Data Dependency', [])
        logger.debug(f"history_items: {history_items}")
            
        if "pre_clear" in rule.get('Hist Handling', []):
            self.llm.clear_conversation()
        
        model = rule.get('Model', [self.DEFAULT_MODEL])[0]
        
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
            response = self.llm.generate_response(prompt, model=model, prompt_name=rule_name, history=history_items)
            results = self._process_evaluation_response(response)
            
            stage = self._get_rule_stage(rule)
            self.stage_results[stage][rule_name] = results.get(rule_name, {})
            
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule_name}: {str(e)}")
            self._add_to_cannot_evaluate(rule_name, rule, str(e))
            raise

    def _prepare_single_rule_prompt(self, rule_name: str, rule: Dict[str, Any]) -> str:
        """Prepare evaluation prompt for a single rule"""
        cleaned_rule = InputTextCleaner.clean_dict_values(rule)

        prompt = (
            f"Please evaluate the following attribute:\n\n"
            f"Attribute Name: {rule_name}\n"
            f"Description: {cleaned_rule.get('Description', '')}\n"
        )
        
        if cleaned_rule.get('Specification'):
            prompt += f"Specification for Attribute 'value' field : {cleaned_rule['Specification']}\n"
            
        prompt += "\nPlease provide your evaluation in JSON format."
        logger.debug(f"Prepared single rule prompt: {prompt}")
        
        return prompt

    def _process_evaluation_response(self, response: str) -> Dict[str, Any]:
        """
        Process and validate the evaluation response with comprehensive character cleaning.
        """
        try:
            # Log the raw response
            logger.debug("Raw response received:")
            logger.debug("=" * 80)
            logger.debug(repr(response))
            logger.debug("=" * 80)

            # Clean and extract JSON content
            cleaned_text = OutputTextCleaner.clean_text(response)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_start = cleaned_text.find('{')
                json_end = cleaned_text.rfind('}')
                if json_start != -1 and json_end != -1:
                    json_text = cleaned_text[json_start:json_end + 1]
                else:
                    logger.warning("No JSON content found in response")
                    json_text = ''
                    # raise ValueError("No JSON content found in response")

            # Parse JSON using safe loader
            results = safe_json_loads(json_text)
            cleaned_results = OutputTextCleaner.clean_dict_values(results)

            # Process and validate the structure
            processed_results = {}
            for field_name, field_value in cleaned_results.items():
                rule = self.evaluation_rules.get(field_name, {})
                
                if not isinstance(field_value, dict) or 'type' not in field_value:
                    processed_results[field_name] = {
                        "type": rule.get('Type', 'Core'),
                        "sub_type": rule.get('Sub_Type', 'None'),
                        "value": field_value,
                        "eval": f"Evaluated from {field_name}",
                        "source": ["document"],
                        "source_detail": ["Document content"]
                    }
                else:
                    processed_results[field_name] = field_value

            return processed_results

        except Exception as e:
            logger.error(f"Error processing evaluation response: {str(e)}")
            logger.error(f"Raw response that caused error: {repr(response)}")
            raise

    def _add_to_cannot_evaluate(self, rule_name: str, rule: Dict, reason: str) -> None:
        """Add a rule to cannot evaluate list"""
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
        logger.warning(f"Rule {rule_name} cannot be evaluated: {reason}")


    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=300
    )
    def load_document(self, document_path: str) -> bool:
        """Load and index a document document"""
        try:
            documents = SimpleDirectoryReader(input_files=[document_path]).load_data()
            self.document_index = VectorStoreIndex.from_documents(documents)
            self.document_text = "\n".join([doc.text for doc in documents])
            self.current_document_path = document_path
            
            # Initialize LLM if needed
            self._init_llm()
            
            logger.info(f"Successfully loaded and indexed document from {document_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading document {document_path}: {str(e)}")
            return False

    def _init_llm(self) -> None:
        """Initialize the LLM client"""
        if not self.document_text:
            raise ValueError("Document text must be loaded before initializing LLM")
            
        if self.llm is None:
            system_instructions = self._get_base_instructions()
            self.llm = self._get_ai(system_instructions=system_instructions)

    def evaluate_document(self, use_steps: bool = True) -> Dict:
        """Perform full document evaluation using appropriate strategies"""
        logger.info(f"Starting document evaluation for {self.current_document_path}")
        
        if not self.document_text:
            raise ValueError("No document has been loaded. Please load a document to be evaluated first.")
            
        self.stage_results = self._init_stage_results()
        
        if self.llm:
            self.llm.clear_conversation()

        try:
            sorted_rules = self._sort_rules_by_stage_and_order()
            
            for stage in [1, 2, 3]:
                stage_rules = [
                    (name, rule) for name, rule in sorted_rules
                    if self._get_rule_stage(rule) == stage
                ]
                
                if not stage_rules:
                    continue
                    
                # Determine which rules can be batched
                batchable_rules = [
                    (name, rule) for name, rule in stage_rules
                    if "pre_clear" in rule.get('Hist Handling', [])
                ]

                # TODO: Looks like I need to add other Hist Handling values to make more rules batchable.
                
                non_batchable_rules = [
                    (name, rule) for name, rule in stage_rules
                    if (name, rule) not in batchable_rules
                ]
                
                # Process batchable rules
                if batchable_rules:
                    batch_results = self.batch_strategy.process_rules(batchable_rules, stage)
                    self._update_stage_results(batch_results, stage)
                
                # Process non-batchable rules
                if non_batchable_rules:
                    individual_results = self.individual_strategy.process_rules(non_batchable_rules, stage)
                    self._update_stage_results(individual_results, stage)
                
                time.sleep(3)  # Delay between stages
            
            return self.get_combined_evaluation()
            
        except Exception as e:
            logger.error(f"Error during document evaluation: {str(e)}", exc_info=True)
            raise

        #TODO: Publish history for debugging

    def _update_stage_results(self, results: Dict[str, Any], stage: int) -> None:
        """Update stage results with new evaluation results"""
        for rule_name, result in results.items():
            if stage not in self.stage_results:
                logger.error(f"Invalid stage {stage} for rule {rule_name}")
                continue
                
            self.stage_results[stage][rule_name] = result
            logger.debug(f"Added result for {rule_name} to stage {stage}")

    def get_overall_score(self) -> float:
        """Calculate the overall score based on weighted Core type evaluations"""
        logger.debug("Starting overall score calculation")
        
        core_results = self.stage_results[1]
        
        if not core_results:
            logger.warning("No stage 1 results available for scoring")
            raise ValueError("No evaluation results available")

        core_rules = {
            name: rule for name, rule in self.evaluation_rules.items()
            if rule.get('Type') == 'Core' 
            and rule.get('is_contribute_rating_overall') == 'True'
            and rule.get('value_type') in ('Integer', 'Decimal')
        }

        total_weight = 0
        weighted_sum = 0

        for name, rule in core_rules.items():
            if name in core_results:
                try:
                    weight = float(rule.get('Weight', 0))
                    value = float(core_results[name].get('value', 0))
                    weighted_sum += weight * value
                    total_weight += weight
                except (TypeError, ValueError) as e:
                    logger.warning(f"Skipping non-numeric value for {name}: {str(e)}")
                    continue

        if total_weight <= 0:
            logger.warning("No valid weighted scores found, returning 0")
            return 0.0

        final_score = weighted_sum / total_weight
        logger.debug(f"Calculated overall score: {final_score}")
        
        return final_score

    def get_combined_evaluation(self) -> Dict:
        """Combine all stage results into a single evaluation result"""
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

        # Initialize content section
        content = {}
        attribute_names = {
            name for name, rule in self.evaluation_rules.items()
            if not name.startswith('_')
        }
        
        # Process each attribute from any stage
        for attr_name in attribute_names:
            for stage in [1, 2, 3]:
                if attr_name in self.stage_results[stage]:
                    stage_value = self.stage_results[stage][attr_name]
                    
                    if isinstance(stage_value, dict) and "value" in stage_value:
                        content[attr_name] = stage_value
                    elif isinstance(stage_value, list):
                        content[attr_name] = {"value": stage_value}
                    else:
                        content[attr_name] = stage_value
                    break

        combined_results = {
            "metadata": {
                "evaluation_date": datetime.now().isoformat(),
                "source_file": str(self.current_document_path),
                "source_txt": self.document_text
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

        # Transform data using ResumeSkillsTransformer
        try:
            from .ResumeSkillsTransformer import ResumeSkillsTransformer
            transformer = ResumeSkillsTransformer(combined_results)
            return transformer.create_integrated_json()
        except Exception as e:
            logger.error(f"Error during data transformation: {str(e)}", exc_info=True)
            return combined_results

    def _reset_evaluator_state(self):
        """Fully reset all evaluator state between documents"""
        self.document_text = None
        self.document_index = None
        self.current_document_path = None
        self.stage_results = self._init_stage_results()
        
        self.llm = None
        
        # Clear any cached data dependencies
        if hasattr(self, 'evaluation_rules'):
            # Reset any accumulated history in rules
            for rule in self.evaluation_rules.values():
                if 'Data Dependency' in rule:
                    rule['Data Dependency'] = []


    def evaluate_directory(self, document_dir: str) -> List[Dict]:
        """Evaluate all supported document files in directory"""
        document_dir_path = Path(document_dir)
        if not document_dir_path.is_dir():
            raise NotADirectoryError(f"{document_dir} is not a directory")

        results = []
        document_files = [
            f for f in document_dir_path.iterdir()
            if self._is_supported_file(f)
        ]
        
        logger.info(f"Found {len(document_files)} supported document files to process")
        
        for file_path in document_files:
            logger.info(f"Processing document: {file_path}")
            
            try:
                # Reset state for new document
                # Use the new reset method
                self._reset_evaluator_state()
                
                self.stage_results = self._init_stage_results()
                
                if self.llm:
                    self.llm.clear_conversation()
                
                if self.load_document(str(file_path)):
                    evaluation_result = self.evaluate_document()
                    results.append(evaluation_result)

                    preferred_name = self._get_preferred_name()
                    output_path = self.output_dir / f"{preferred_name}_evaluation.json"
                    self.export_results(str(output_path))
                    
                    time.sleep(2)
                else:
                    logger.error(f"Failed to load document: {file_path}")
                    
            except Exception as e:
                logger.error(f"Error processing document {file_path}: {str(e)}", exc_info=True)
                continue

        return results

    def _get_preferred_name(self) -> str:
        """Extract preferred name from evaluation results or generate fallback"""
        preferred_name = self.stage_results[1].get('preferred_name', {}).get('value')
        
        if not preferred_name:
            preferred_name = Path(self.current_document_path).stem
            
        safe_name = "".join(c for c in preferred_name if c.isalnum() or c in (' ', '-', '_')).strip()
        return safe_name.replace(' ', '_')

    def export_results(self, output_path: str) -> None:
        """Export evaluation results and move processed documents"""
        try:
            combined_results = self.get_combined_evaluation()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(safe_json_dumps(combined_results, indent=2))
            logger.info(f"Results exported to {output_path}")
            
            if self.current_document_path:
                document_path = Path(self.current_document_path)
                processed_dir = document_path.parent / 'processed'
                processed_dir.mkdir(parents=True, exist_ok=True)
                
                dest_path = processed_dir / document_path.name
                counter = 1
                while dest_path.exists():
                    new_name = f"{document_path.stem}_{counter}{document_path.suffix}"
                    dest_path = processed_dir / new_name
                    counter += 1
                
                shutil.move(str(document_path), str(dest_path))
                logger.info(f"Moved processed document to {dest_path}")
                
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}", exc_info=True)
            raise

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file is a supported document format"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

# # Example usage
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
    
#     evaluator = ResumeEvaluator(
#         evaluation_rules_path="candidate_evaluation_rules.json",
#         evaluation_steps_path="candidate_evaluation_steps.json",
#         output_dir="evaluation_results"
#     )
    
#     results = evaluator.evaluate_directory("resumes")
#     print(f"Processed {len(results)} resumes")