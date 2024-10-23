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
    

from typing import Union, List
import textwrap
import re

def wrap_multiline(
        text: str,
        width: int = 80,
        preserve_paragraphs: bool = True,
        remove_indentation: bool = True,
        initial_indent: str = "",
        subsequent_indent: str = "",
    ) -> str:
    """
    Wrap multiline text blocks while preserving original line breaks and structure.
    
    Args:
        text (str): The multiline text to wrap
        width (int): Maximum line width (default: 80)
        preserve_paragraphs (bool): Keep paragraph breaks (default: True)
        remove_indentation (bool): Remove common leading whitespace (default: True)
        initial_indent (str): String to prefix first line of each paragraph
        subsequent_indent (str): String to prefix subsequent lines of each paragraph
    
    Returns:
        str: The wrapped text with preserved structure
    
    Example:
        >>> text = '''This is a paragraph
        ...   that spans multiple lines.
        ...
        ...   This is another paragraph
        ...   with multiple lines.'''
        >>> print(wrap_multiline(text, width=40))
        This is a paragraph
          that spans multiple lines.

          This is another paragraph
          with multiple lines.
    """
    if not text:
        return ""

    # Handle indentation
    if remove_indentation:
        text = textwrap.dedent(text)
    
    def wrap_paragraph(para: str) -> str:
        """Wrap a single paragraph while preserving existing line breaks."""
        # Split into lines and preserve empty lines
        lines = para.split('\n')
        wrapped_lines = []
        
        for line in lines:
            # Preserve empty lines
            if not line.strip():
                wrapped_lines.append(line)
                continue
            
            # Get the leading whitespace
            leading_space = re.match(r'^\s*', line).group(0)
            
            # Wrap the content of the line
            content = line.strip()
            if len(content) > 0:
                # Calculate remaining width after indentation
                effective_width = max(width - len(leading_space), 20)
                
                # Wrap the line content
                wrapped = textwrap.fill(
                    content,
                    width=effective_width,
                    initial_indent="",
                    subsequent_indent=subsequent_indent
                )
                
                # Reapply the original indentation
                wrapped_lines.extend(
                    leading_space + wline
                    for wline in wrapped.split('\n')
                )
            else:
                wrapped_lines.append(line)
        
        return '\n'.join(wrapped_lines)

    if preserve_paragraphs:
        # Split into paragraphs (preserve multiple newlines)
        paragraphs = re.split(r'(\n\s*\n)', text)
        wrapped_parts = []
        
        for i, part in enumerate(paragraphs):
            # If it's a separator (newlines), preserve it exactly
            if i % 2 == 1:
                wrapped_parts.append(part)
            # If it's a paragraph, wrap it
            elif part.strip():
                wrapped_parts.append(wrap_paragraph(part))
        
        return ''.join(wrapped_parts)
    else:
        # Treat entire text as single paragraph
        return wrap_paragraph(text)
