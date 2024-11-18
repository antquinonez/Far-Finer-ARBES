# Copyright (c) 2024 Antonio Quinonez
# Licensed under the MIT License. See LICENSE in the project root for license information.

import os
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime

load_dotenv()

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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence_number": self.sequence_number,
            "model": self.model,
            "timestamp": self.timestamp,
            "prompt_name": self.prompt_name,
            "prompt": self.prompt,
            "response": self.response,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat()
        }

class OrderedHistory:
    def __init__(self):
        self.interactions: List[Interaction] = []
        self._current_sequence = 0
    
    def add_interaction(self, model: str, prompt: str, response: str, prompt_name: Optional[str] = None) -> Interaction:
        """Add a new interaction to the history"""
        self._current_sequence += 1
        interaction = Interaction(
            sequence_number=self._current_sequence,
            model=model,
            timestamp=time.time(),
            prompt_name=prompt_name,
            prompt=prompt,
            response=response
        )
        self.interactions.append(interaction)
        return interaction

    def get_all_interactions(self) -> List[Interaction]:
        """Get all interactions"""
        return deepcopy(self.interactions)
    
    def get_last_n_interactions(self, n: int) -> List[Interaction]:
        """Get the last n interactions"""
        return deepcopy(self.interactions[-n:])
    
    def get_interaction_by_sequence(self, sequence_number: int) -> Optional[Interaction]:
        """Get a specific interaction by its sequence number"""
        for interaction in self.interactions:
            if interaction.sequence_number == sequence_number:
                return deepcopy(interaction)
        return None
    
    def get_interactions_by_model(self, model: str) -> List[Interaction]:
        """Get all interactions for a specific model"""
        return deepcopy([i for i in self.interactions if i.model == model])
    
    def get_interactions_in_timeframe(self, start_time: float, end_time: Optional[float] = None) -> List[Interaction]:
        """Get interactions within a specified timeframe"""
        end_time = end_time or time.time()
        return deepcopy([i for i in self.interactions if start_time <= i.timestamp <= end_time])
    
    def get_latest_interaction(self) -> Optional[Interaction]:
        """Get the most recent interaction"""
        return deepcopy(self.interactions[-1]) if self.interactions else None
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all interactions to a list of dictionaries"""
        return [i.to_dict() for i in self.interactions]
    
    def get_prompt_history(self) -> List[str]:
        """Get a list of all prompts in order"""
        return [i.prompt for i in self.interactions]
    
    def get_response_history(self) -> List[str]:
        """Get a list of all responses in order"""
        return [i.response for i in self.interactions]
    
    def get_model_usage_stats(self) -> Dict[str, int]:
        """Get statistics on model usage"""
        stats = {}
        for interaction in self.interactions:
            stats[interaction.model] = stats.get(interaction.model, 0) + 1
        return stats