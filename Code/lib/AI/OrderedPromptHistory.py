from typing import Optional, List, Dict, Any
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
import time
from datetime import datetime
import re

import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Interaction:
    """Represents a single prompt-response interaction"""
    sequence_number: int
    model: str
    timestamp: float
    prompt_name: Optional[str]
    prompt: str
    response: str
    history: Optional[List[str]] = None  # Added history field
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence_number": self.sequence_number,
            "model": self.model,
            "timestamp": self.timestamp,
            "prompt_name": self.prompt_name,
            "prompt": self.prompt,
            "response": self.response,
            "history": self.history,  # Include history in dict representation
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat()
        }

class OrderedPromptHistory:
    def __init__(self):
        self.prompt_dict: OrderedDict[str, List[Interaction]] = OrderedDict()
        self._current_sequence = 0
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing RAG tags, PROMPT sections, and extra whitespace"""
        # Remove RAG sections
        cleaned = re.sub(r'<RAG>[\s\S]*?</RAG>', '', text)
        # Remove PROMPT sections
        cleaned = re.sub(r'========\s*PROMPT\s*========[\s\S]*', '', cleaned)
        
        # Clean whitespace line by line
        cleaned_lines = []
        for line in cleaned.splitlines():
            cleaned_line = ' '.join(line.split())
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines).strip()

    def get_effective_prompt_name(self, prompt_name:Any)->str:
        logger.debug(f"Running: get_effective_prompt_name()")
        logger.debug(f"prompt_name: {prompt_name} | type: {type(prompt_name)}")

        if type(prompt_name) == str:
            # Clean prompt_name
            cleaned_prompt = self._clean_text(prompt_name)

            logger.debug(f"returning effective_prompt: {cleaned_prompt} | type: str")
            return cleaned_prompt
        elif type(prompt_name) == tuple:
            values = []
    
            # Iterate through the tuple
            for item in prompt_name:
                # Each item is a tuple of (name, dictionary)
                name, _ = item
                
                # Add the name (first element of each inner tuple)
                values.append(name)
            
            # if single element tuple, return value as a str
            if len(tuple(values)) == 1:
                simple_value = tuple(values)[0]

                logger.debug(f"returning effective_prompt: {simple_value} | type: {type(simple_value)}")
                return tuple(values)[0]
            # return multiple item tuple
            else:
                logger.debug(f"returning effective_prompt: {tuple(values)} | type: tuple")
                return tuple(values)


    def add_interaction(self, model: str, prompt: str, response: str, 
                       prompt_name: Optional[str] = None, 
                       history: Optional[List[str]] = None) -> Interaction:
        """
        Add a new interaction to the history, storing cleaned versions of prompt and response
        
        Args:
            model: The model used for the interaction
            prompt: The prompt text
            response: The response text
            prompt_name: Optional name/key for the prompt. If None, uses prompt text as key
            history: Optional list of prompt names that form the history chain for this interaction
        
        Returns:
            The created Interaction object
        """
        logger.debug("***************************************************************")
        logger.debug(f"Running: add_interaction()")
        logger.debug("***************************************************************")
        logger.debug(f"prompt: {prompt} | type: {type(prompt)}")
        logger.debug(f"prompt_name: {prompt_name} | type: {type(prompt_name)}")
        logger.debug(f"history: {history} | type: {type(history)}")
        logger.debug(f"model: {model} | type: {type(model)}")
        logger.debug("***************************************************************")

        logger.debug(f"response: {response} | type: {type(response)}")

        self._current_sequence += 1

        
        # Clean prompt and response before storing
        cleaned_prompt = self._clean_text(prompt)
        cleaned_response = self._clean_text(response)
        logger.debug(f"cleaned_response: {cleaned_response}")

        # GET PROMPT NAME
        effective_prompt_name = self.get_effective_prompt_name(prompt_name) or cleaned_prompt
        logger.debug(f"effective_prompt_name: {effective_prompt_name}")



        interaction = Interaction(
            sequence_number=self._current_sequence,
            model=model,
            timestamp=time.time(),
            prompt_name=effective_prompt_name,
            prompt=cleaned_prompt,
            response=cleaned_response,
            history=history  # Store the history chain
        )
        

        if effective_prompt_name not in self.prompt_dict:
            self.prompt_dict[effective_prompt_name] = []

        self.prompt_dict[effective_prompt_name].append(interaction)
        return interaction

    def get_interactions_by_prompt_name(self, prompt_name: str) -> List[Interaction]:
        """Get all interactions for a specific prompt name"""
        logger.debug(f"Getting interactions for prompt_name: {prompt_name}")

        return deepcopy(self.prompt_dict.get(prompt_name, []))
    
    def get_latest_interaction_by_prompt_name(self, prompt_name: str) -> Optional[Interaction]:
        """Get the most recent interaction for a specific prompt name"""
        logger.debug(f"Getting latest interaction for prompt_name: {prompt_name}")
        
        interactions = self.prompt_dict.get(prompt_name, [])
        return deepcopy(interactions[-1]) if interactions else None
    
    def get_all_prompt_names(self) -> List[str]:
        """Get a list of all prompt names in order of first appearance"""
        if hasattr(self, 'prompt_dict'):
            all_prompt_names = self.prompt_dict.keys()
            logger.debug(f"Returning all prompt names: {all_prompt_names}")
            return list(all_prompt_names)
        else:
            logger.warning("prompt_dict is not initialized")
            return []  # or handle the error case differently

    
    def get_all_interactions(self) -> List[Interaction]:
        """Get all interactions in sequence order"""
        logger.debug("Getting all interactions")
        logger.debug(f"Object Prompt dict: {self.prompt_dict}")

        all_interactions = []

        for interactions in self.prompt_dict.values():
            all_interactions.extend(interactions)
        return sorted(deepcopy(all_interactions), key=lambda x: x.sequence_number)
    
    def get_prompt_name_usage_stats(self) -> Dict[str, int]:
        """Get statistics on prompt name usage"""
        return {name: len(interactions) for name, interactions in self.prompt_dict.items()}
    
    def get_interactions_by_model_and_prompt_name(self, model: str, prompt_name: str) -> List[Interaction]:
        """Get all interactions for a specific model and prompt name combination"""
        interactions = self.prompt_dict.get(prompt_name, [])
        return deepcopy([i for i in interactions if i.model == model])
    
    def merge_histories(self, other: 'OrderedPromptHistory') -> None:
        """
        Merge another OrderedPromptHistory into this one
        
        Args:
            other: Another OrderedPromptHistory instance to merge
        """
        for prompt_name, interactions in other.prompt_dict.items():
            if prompt_name not in self.prompt_dict:
                self.prompt_dict[prompt_name] = []
            self.prompt_dict[prompt_name].extend(deepcopy(interactions))
            
        # Resequence all interactions to maintain order
        all_interactions = self.get_all_interactions()
        self._current_sequence = 0
        self.prompt_dict.clear()
        
        for interaction in all_interactions:
            self.add_interaction(
                model=interaction.model,
                prompt=interaction.prompt,
                response=interaction.response,
                prompt_name=interaction.prompt_name,
                history=interaction.history  # Preserve history when resequencing
            )
    
    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert the entire history to a dictionary organized by prompt names"""
        return {
            prompt_name: [i.to_dict() for i in interactions]
            for prompt_name, interactions in self.prompt_dict.items()
        }
    
    def get_interaction_by_prompt(self, prompt: str) -> Optional[Interaction]:
        """
        Get an interaction by its exact prompt text
        Useful when prompt was used as the prompt_name
        """
        return self.get_latest_interaction_by_prompt_name(prompt)

    def get_latest_responses_by_prompt_names(self, prompt_names: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Get the latest prompt and response for each specified prompt name.
        
        Args:
            prompt_names: List of prompt names to retrieve
            
        Returns:
            Dictionary with prompt names as keys and dictionaries containing 
            'prompt' and 'response' as values
        """
        result = {}
        for prompt_name in prompt_names:
            latest = self.get_latest_interaction_by_prompt_name(prompt_name)
            if latest and latest.prompt and latest.response:
                result[prompt_name] = {
                    'prompt': latest.prompt,
                    'response': latest.response
                }
        return result
    
    def get_formatted_responses(self, prompt_names: List[str]) -> str:
        """
        Format the latest prompts and responses in the specified format,
        including recursive history chains.
        
        Args:
            prompt_names: List of prompt names to include in the formatted output
            
        Returns:
            Formatted string containing all prompts and responses
        """
        formatted_outputs = []
        processed_prompts = set()  # To prevent infinite loops
        
        def process_prompt_chain(prompt_name: str):
            if prompt_name in processed_prompts:
                return
            
            processed_prompts.add(prompt_name)
            latest = self.get_latest_interaction_by_prompt_name(prompt_name)
            
            if latest:
                # First process this prompt's history if it exists
                if latest.history:
                    for history_prompt in latest.history:
                        process_prompt_chain(history_prompt)
                
                # Then add this prompt's formatted output
                if latest.prompt and latest.response:
                    # Use the cleaned prompt text for the tag, not the prompt_name
                    formatted_output = f"<prompt:{latest.prompt}>{latest.response}</prompt:{latest.prompt}>"
                    formatted_outputs.append(formatted_output)
        
        # Process all prompt chains
        for prompt_name in prompt_names:
            process_prompt_chain(prompt_name)
        
        return '\n'.join(formatted_outputs)