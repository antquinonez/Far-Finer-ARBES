from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import textwrap

@dataclass
class FieldFormatter:
    """Handles consistent field formatting with configurable parameters."""
    field_width: int = 35
    content_width: int = 160
    indent_size: int = 4

    def format_field(self, name: str, value: Any, indent_level: int = 0) -> str:
        """Format a field with proper name alignment and content wrapping."""
        if value is None or value == '':
            return ''
            
        result = []
        field_name = f"{name}:".ljust(self.field_width)
        base_indent = ' ' * (self.field_width + (indent_level * self.indent_size))
        
        # Convert value to string and handle multi-line content
        if isinstance(value, (list, tuple)):
            result.append(field_name)
            result.append(self._format_list(value, base_indent))
        elif isinstance(value, dict):
            result.append(field_name)
            result.append(self._format_dict(value, base_indent))
        else:
            str_value = str(value).replace('\\', '')  # Remove backslashes
            if '\n' in str_value or len(str_value) > (self.content_width - self.field_width):
                result.append(field_name)
                result.append(self._wrap_text(str_value, base_indent))
            else:
                result.append(f"{field_name}{str_value}")
                
        return '\n'.join(result)

    def _wrap_text(self, text: str, indent: str) -> str:
        """Wrap text with proper indentation."""
        wrapped_lines = []
        # Remove backslashes before processing
        text = text.replace('\\', '')
        for line in text.split('\n'):
            if line.strip():
                wrapped = textwrap.fill(
                    line,
                    width=self.content_width - len(indent),
                    initial_indent=indent,
                    subsequent_indent=indent
                )
                wrapped_lines.append(wrapped)
        return '\n'.join(wrapped_lines)

    def _format_list(self, items: Union[List, Tuple], indent: str) -> str:
        """Format list items with proper indentation."""
        result = []
        for item in items:
            if isinstance(item, str):
                # Remove backslashes from list items
                item = item.replace('\\', '')
                prefix = '- ' if not item.startswith('-') else ''
                wrapped = self._wrap_text(f"{prefix}{item}", indent)
                result.append(wrapped)
            elif isinstance(item, dict):
                result.append(self._format_dict(item, indent))
            elif isinstance(item, (list, tuple)):
                result.append(self._format_list(item, indent + ' ' * self.indent_size))
        return '\n'.join(result)

    def _format_dict(self, d: Dict, indent: str) -> str:
        """Format dictionary with proper indentation."""
        result = []
        for key, value in d.items():
            # Remove backslashes from both key and value
            key = str(key).replace('\\', '')
            if isinstance(value, str):
                value = value.replace('\\', '')
            key_str = f"{key}:"
            if isinstance(value, dict):
                result.append(f"{indent}{key_str}")
                result.append(self._format_dict(value, indent + ' ' * self.indent_size))
            elif isinstance(value, (list, tuple)):
                result.append(f"{indent}{key_str}")
                result.append(self._format_list(value, indent + ' ' * self.indent_size))
            else:
                result.append(f"{indent}{key_str} {value}")
        return '\n'.join(result)