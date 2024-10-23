from typing import Optional
import json

def fix_json_from_codeblock(input_str, output_type:Optional[str] = None):
    """
    Takes a problematic JSON string and attempts to:
    1. Remove markdown code block syntax
    2. Fix escape characters
    3. Clean up any formatting issues
    4. Return a properly formatted JSON string
    """
    # Remove markdown code block syntax if present
    input_str = input_str.replace('```json', '').replace('```', '').strip()
    
    # First, let's properly escape the quotes within strings
    # Remove existing escape characters and re-escape properly
    cleaned = input_str.replace('\\"', '"')  # Remove any existing escaped quotes
    
    # Parse the string to a Python dictionary
    try:
        data = json.loads(cleaned)
        
        if output_type == 'json':
            # Format it back to a properly indented JSON string
            formatted_json = json.dumps(data, indent=2)
            return formatted_json
        else:
            return data

    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"
