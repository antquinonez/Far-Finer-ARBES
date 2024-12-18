from json import JSONEncoder
import json
from typing import Any, Dict, Union
import unicodedata

class SafeJSONEncoder(JSONEncoder):
    """Custom JSON encoder that ensures safe encoding for LLM processing"""
    
    def default(self, obj: Any) -> Any:
        """Handle special object types"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return super().default(obj)
    
    def encode(self, obj: Any) -> str:
        """Custom encode method with additional safety measures"""
        def clean_string(s: str) -> str:
            # Normalize to ASCII-compatible form
            normalized = unicodedata.normalize('NFKD', s)
            # Replace problematic characters
            cleaned = ''.join(c for c in normalized if unicodedata.category(c)[0] != 'C')
            # Handle additional special characters
            replacements = {
                # Smart quotes and apostrophes
                '“': '"',     # U+201C LEFT DOUBLE QUOTATION MARK
                '”': '"',     # U+201D RIGHT DOUBLE QUOTATION MARK
                '‘': "'",     # U+2018 LEFT SINGLE QUOTATION MARK
                '’': "'",     # U+2019 RIGHT SINGLE QUOTATION MARK
                '‚': "'",     # U+201A SINGLE LOW-9 QUOTATION MARK
                '„': '"',     # U+201E DOUBLE LOW-9 QUOTATION MARK
                
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
                '…': '...',    # U+2026 HORIZONTAL ELLIPSIS
                '•': '*',      # U+2022 BULLET
                '·': '*',      # U+00B7 MIDDLE DOT
                '○': '*',      # U+25CB WHITE CIRCLE
                '●': '*',      # U+25CF BLACK CIRCLE
                '▪': '*',      # U+25AA BLACK SMALL SQUARE
                '■': '*',      # U+25A0 BLACK SQUARE
                '□': '*',      # U+25A1 WHITE SQUARE
                '★': '*',     # U+2605 BLACK STAR
                '☆': '*',     # U+2606 WHITE STAR
                '➢': '>',     # U+27A2 THREE-D TOP-LIGHTED RIGHTWARDS ARROWHEAD
                '➣': '>',     # U+27A3 THREE-D BOTTOM-LIGHTED RIGHTWARDS ARROWHEAD
                '➤': '>',     # U+27A4 BLACK RIGHTWARDS ARROWHEAD
                '⇒': '=>',   # U+21D2 RIGHTWARDS DOUBLE ARROW
                '⇨': '=>'     # U+21E8 RIGHTWARDS WHITE ARROW
            }
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            return cleaned

        def clean_value(v: Any) -> Any:
            if isinstance(v, str):
                return clean_string(v)
            elif isinstance(v, dict):
                return {k: clean_value(v) for k, v in v.items()}
            elif isinstance(v, list):
                return [clean_value(item) for item in v]
            return v

        # Clean the entire object structure
        cleaned_obj = clean_value(obj)
        # Encode using parent class
        return super().encode(cleaned_obj)

def safe_json_loads(json_str: str) -> Union[Dict, list]:
    """Safely load JSON string with encoding handling"""
    if isinstance(json_str, bytes):
        # Try common encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        for encoding in encodings:
            try:
                json_str = json_str.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
    
    return json.loads(json_str)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely dump object to JSON string"""
    return json.dumps(obj, cls=SafeJSONEncoder, ensure_ascii=True, **kwargs)