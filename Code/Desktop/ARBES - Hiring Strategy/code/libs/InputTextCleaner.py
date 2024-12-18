import re
import unicodedata

class InputTextCleaner:
    """Utility class for cleaning text before sending to LLMs."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing problematic characters and normalizing whitespace.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text string
        """
        if not text:
            return text
            
        
        # Step 1: Normalize unicode characters
        normalized = unicodedata.normalize('NFKD', text)
        
        # Step 2: Remove control characters except newlines and tabs
        control_char_pattern = r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]'
        text_no_control = re.sub(control_char_pattern, '', normalized)
        
        # Step 3: Replace unicode dingbats and special symbols
        # This covers ranges for dingbats, miscellaneous symbols, etc.
        dingbats_pattern = r'[\u2700-\u27BF\u2600-\u26FF\u2800-\u28FF]'
        text_no_dingbats = re.sub(dingbats_pattern, '', text_no_control)
        
        # Step 4: Replace multiple spaces with single space
        text_normalized_spaces = re.sub(r' +', ' ', text_no_dingbats)
        
        # Step 5: Replace multiple newlines with double newline
        text_normalized_newlines = re.sub(r'\n{3,}', '\n\n', text_normalized_spaces)
        
        # Step 6: Strip whitespace from start and end
        text_stripped = text_normalized_newlines.strip()
        
        return text_stripped
    
    @staticmethod
    def clean_dict_values(d: dict) -> dict:
        """
        Recursively clean all string values in a dictionary.
        
        Args:
            d: Input dictionary
            
        Returns:
            Dictionary with cleaned string values
        """
        cleaned = {}
        for k, v in d.items():
            if isinstance(v, str):
                cleaned[k] = InputTextCleaner.clean_text(v)
            elif isinstance(v, dict):
                cleaned[k] = InputTextCleaner.clean_dict_values(v)
            elif isinstance(v, list):
                cleaned[k] = [
                    InputTextCleaner.clean_text(x) if isinstance(x, str)
                    else InputTextCleaner.clean_dict_values(x) if isinstance(x, dict)
                    else x
                    for x in v
                ]
            else:
                cleaned[k] = v
        return cleaned