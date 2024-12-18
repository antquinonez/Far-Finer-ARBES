import re
import unicodedata
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OutputTextCleaner:
    """Utility class for comprehensive text cleaning."""
    
    # Characters to preserve
    ALLOWED_PUNCTUATION = '.,-_():;?!/[]{}@#$%&*+=<>'
    ALLOWED_QUOTES = '"\'""''\u201C\u201D\u2018\u2019'  # Various quote types
    
    # Mapping for character replacements
    CHAR_REPLACEMENTS = {
        # Smart quotes and apostrophes
        # '“': '"',     # U+201C LEFT DOUBLE QUOTATION MARK
        # '”': '"',     # U+201D RIGHT DOUBLE QUOTATION MARK
        # '‘': "'",     # U+2018 LEFT SINGLE QUOTATION MARK
        # '’': "'",     # U+2019 RIGHT SINGLE QUOTATION MARK
        # '‚': "'",     # U+201A SINGLE LOW-9 QUOTATION MARK
        # '„': '"',     # U+201E DOUBLE LOW-9 QUOTATION MARK
        
        # Dashes and hyphens
        '—': '-',     # U+2014 EM DASH
        '–': '-',     # U+2013 EN DASH
        '‐': '-',     # U+2010 HYPHEN
        '‑': '-',     # U+2011 NON-BREAKING HYPHEN
        '−': '-',     # U+2212 MINUS SIGN
        
        # Spaces and zero-width characters
        '\xa0': ' ',  # NO-BREAK SPACE
        '\u200b': '', # ZERO WIDTH SPACE
        '\u200c': '', # ZERO WIDTH NON-JOINER
        '\u200d': '', # ZERO WIDTH JOINER
        '\u2060': '', # WORD JOINER
        '\ufeff': '', # ZERO WIDTH NO-BREAK SPACE
        
        # Other special characters
        '…': '...',   # U+2026 HORIZONTAL ELLIPSIS
        '•': '*',     # U+2022 BULLET
        '·': '*',     # U+00B7 MIDDLE DOT
        '○': '*',     # U+25CB WHITE CIRCLE
        '●': '*',     # U+25CF BLACK CIRCLE
        '▪': '*',     # U+25AA BLACK SMALL SQUARE
        '■': '*',     # U+25A0 BLACK SQUARE
        '□': '*',     # U+25A1 WHITE SQUARE
        '★': '*',     # U+2605 BLACK STAR
        '☆': '*',     # U+2606 WHITE STAR
        '➢': '>',     # U+27A2 THREE-D TOP-LIGHTED RIGHTWARDS ARROWHEAD
        '➣': '>',     # U+27A3 THREE-D BOTTOM-LIGHTED RIGHTWARDS ARROWHEAD
        '➤': '>',     # U+27A4 BLACK RIGHTWARDS ARROWHEAD
        '⇒': '=>',    # U+21D2 RIGHTWARDS DOUBLE ARROW
        '⇨': '=>',    # U+21E8 RIGHTWARDS WHITE ARROW
        
        # Common HTML entities
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
    }

    @classmethod
    def clean_text(cls, text: str, aggressive: bool = False) -> str:
        """
        Clean text by removing or replacing problematic characters.
        
        Args:
            text: Input text to clean
            aggressive: If True, removes all characters not explicitly allowed
        
        Returns:
            Cleaned text string
        """
        if not isinstance(text, str):
            return str(text)

        # Step 1: Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Step 2: Apply character replacements
        for old, new in cls.CHAR_REPLACEMENTS.items():
            text = text.replace(old, new)
        
        # Step 3: Handle whitespace
        text = re.sub(r'\s+', ' ', text)  # Collapse multiple whitespace
        text = re.sub(r'\s*\n\s*', '\n', text)  # Clean up newlines
        
        if aggressive:
            # Step 4: Remove all characters except allowed ones
            allowed_chars = (
                set(cls.ALLOWED_PUNCTUATION) |
                set(cls.ALLOWED_QUOTES) |
                {'\n', ' '} |
                set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            )
            text = ''.join(c for c in text if c in allowed_chars)
        
        # Step 5: Clean up edge cases
        text = re.sub(r'"\s+}', '"}', text)  # Remove spaces before closing braces
        text = re.sub(r'"\s+,', '",', text)  # Remove spaces before commas
        text = re.sub(r'\s+:', ':', text)    # Remove spaces before colons
        text = re.sub(r':\s+', ': ', text)   # Normalize spaces after colons
        
        return text.strip()

    @classmethod
    def clean_dict_values(cls, data: Dict[str, Any], aggressive: bool = False) -> Dict[str, Any]:
        """
        Recursively clean all string values in a dictionary.
        
        Args:
            data: Dictionary to clean
            aggressive: If True, removes all characters not explicitly allowed
            
        Returns:
            Dictionary with cleaned string values
        """
        if not isinstance(data, dict):
            return data
            
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = cls.clean_text(value, aggressive)
            elif isinstance(value, dict):
                cleaned[key] = cls.clean_dict_values(value, aggressive)
            elif isinstance(value, list):
                cleaned[key] = [
                    cls.clean_dict_values(item, aggressive) if isinstance(item, dict)
                    else cls.clean_text(item, aggressive) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                cleaned[key] = value
        return cleaned