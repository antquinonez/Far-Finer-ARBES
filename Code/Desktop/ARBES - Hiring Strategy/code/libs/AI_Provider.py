# ai_provider.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import backoff
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)

class AIResponse:
    """Class to standardize AI provider responses"""
    def __init__(self, text: str, model: str, tokens_used: int, completion_time: float):
        self.text = text
        self.model = model
        self.tokens_used = tokens_used
        self.completion_time = completion_time
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "completion_time": self.completion_time,
            "timestamp": self.timestamp.isoformat()
        }

class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass

class RateLimitError(AIProviderError):
    """Raised when rate limits are hit"""
    pass

class AuthenticationError(AIProviderError):
    """Raised for authentication/authorization failures"""
    pass

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.system_instructions = config.get('system_instructions')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 4000)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup provider-specific logging"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    def generate_response(self, prompt: str, model: str) -> AIResponse:
        """Generate a response from the AI provider"""
        pass

    @abstractmethod
    def clear_conversation(self) -> None:
        """Clear the conversation history"""
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Get the token count for a piece of text"""
        pass

class AzureAIProvider(AIProvider):
    """Azure OpenAI provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Import Azure specific clients
        from lib.AI.FFAIAzure import FFAIAzure
        from lib.AI.FFAzureOpenAI import FFAzureOpenAI
        
        try:
            self.client = FFAzureOpenAI(config)
            self.ai = FFAIAzure(self.client)
            self.logger.info("Azure AI provider initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure AI provider: {str(e)}")
            raise AIProviderError(f"Azure initialization failed: {str(e)}")

    @backoff.on_exception(
        backoff.expo,
        (RateLimitError, ConnectionError),
        max_tries=3,
        max_time=30
    )
    def generate_response(self, prompt: str, model: str) -> AIResponse:
        start_time = datetime.utcnow()
        
        try:
            response = self.ai.generate_response(prompt, model=model)
            
            completion_time = (datetime.utcnow() - start_time).total_seconds()
            tokens_used = self.get_token_count(prompt + response)
            
            return AIResponse(
                text=response,
                model=model,
                tokens_used=tokens_used,
                completion_time=completion_time
            )
            
        except Exception as e:
            if "rate limits exceeded" in str(e).lower():
                raise RateLimitError(f"Azure rate limit exceeded: {str(e)}")
            raise AIProviderError(f"Azure generation failed: {str(e)}")

    def clear_conversation(self) -> None:
        try:
            self.ai.clear_conversation()
            self.logger.debug("Conversation history cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear conversation: {str(e)}")
            raise AIProviderError(f"Failed to clear Azure conversation: {str(e)}")

    def get_token_count(self, text: str) -> int:
        # Implement Azure-specific token counting
        # This is a simplified example - replace with actual implementation
        return len(text.split()) * 1.3  # rough estimate

class AnthropicProvider(AIProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Import Anthropic specific client
        from lib.AI.FFAnthropicCached import FFAnthropicCached
        
        try:
            self.ai = FFAnthropicCached(config)
            self.logger.info("Anthropic provider initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Anthropic provider: {str(e)}")
            raise AIProviderError(f"Anthropic initialization failed: {str(e)}")

    @backoff.on_exception(
        backoff.expo,
        (RateLimitError, ConnectionError),
        max_tries=3,
        max_time=30
    )
    def generate_response(self, prompt: str, model: str) -> AIResponse:
        start_time = datetime.utcnow()
        
        try:
            response = self.ai.generate_response(prompt, model=model)
            
            completion_time = (datetime.utcnow() - start_time).total_seconds()
            tokens_used = self.get_token_count(prompt + response)
            
            return AIResponse(
                text=response,
                model=model,
                tokens_used=tokens_used,
                completion_time=completion_time
            )
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                raise RateLimitError(f"Anthropic rate limit exceeded: {str(e)}")
            raise AIProviderError(f"Anthropic generation failed: {str(e)}")

    def clear_conversation(self) -> None:
        try:
            self.ai.clear_conversation()
            self.logger.debug("Conversation history cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear conversation: {str(e)}")
            raise AIProviderError(f"Failed to clear Anthropic conversation: {str(e)}")

    def get_token_count(self, text: str) -> int:
        # Implement Anthropic-specific token counting
        # This is a simplified example - replace with actual implementation
        return len(text.split()) * 1.3  # rough estimate

class AIProviderFactory:
    """Factory class for creating AI providers"""
    
    _providers = {
        "azure": AzureAIProvider,
        "anthropic": AnthropicProvider
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """Register a new provider class"""
        if not issubclass(provider_class, AIProvider):
            raise ValueError(f"Provider class must inherit from AIProvider")
        cls._providers[name] = provider_class
        logger.info(f"Registered new provider: {name}")

    @classmethod
    def create_provider(cls, 
                       provider_type: str, 
                       config: Dict[str, Any],
                       fallback_provider: Optional[str] = None) -> AIProvider:
        """
        Create and return an AI provider instance
        
        Args:
            provider_type: Type of provider to create
            config: Configuration for the provider
            fallback_provider: Optional fallback provider if primary fails
            
        Returns:
            AIProvider instance
            
        Raises:
            AIProviderError: If provider creation fails and no fallback exists
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
            
        try:
            provider_class = cls._providers[provider_type]
            return provider_class(config)
            
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {str(e)}")
            
            if fallback_provider:
                logger.info(f"Attempting fallback to {fallback_provider}")
                return cls.create_provider(fallback_provider, config)
                
            raise AIProviderError(f"Failed to create provider and no fallback specified: {str(e)}")

# Example usage and configuration
if __name__ == "__main__":
    # Example configuration
    azure_config = {
        "system_instructions": "You are a helpful AI assistant",
        "temperature": 0.5,
        "max_tokens": 4000,
        # Add Azure-specific configuration
        "api_key": "your_azure_api_key",
        "endpoint": "your_azure_endpoint"
    }

    anthropic_config = {
        "system_instructions": "You are a helpful AI assistant",
        "temperature": 0.7,
        "max_tokens": 4000,
        # Add Anthropic-specific configuration
        "api_key": "your_anthropic_api_key"
    }

    try:
        # Create Azure provider with Anthropic fallback
        provider = AIProviderFactory.create_provider(
            "azure", 
            azure_config,
            fallback_provider="anthropic"
        )

        # Generate a response
        response = provider.generate_response(
            "What is the capital of France?",
            model="gpt-4"
        )

        print(json.dumps(response.to_dict(), indent=2))

    except AIProviderError as e:
        print(f"Error using AI provider: {str(e)}")