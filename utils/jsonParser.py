# deprecated
import json
from typing import Any, Dict
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

def parse_and_display(json_str: str, title: str = "JSON Output") -> Dict[str, Any]:
    """
    Parse JSON string and display it in a formatted way
    
    Args:
        json_str: JSON string to parse
        title: Optional title for the display panel
    
    Returns:
        Parsed JSON as a Python dictionary
    """
    console = Console()
    
    try:
        # Clean the input string if it contains escaped newlines
        cleaned_str = json_str.replace('\\n', '\n')
        
        # Parse JSON
        data = json.loads(cleaned_str)
        
        # Create formatted display
        syntax = Syntax(
            json.dumps(data, indent=2),
            "json",
            theme="monokai",
            word_wrap=True
        )
        
        # Display in panel
        console.print(Panel(
            syntax,
            title=title,
            border_style="blue"
        ))
        
        return data
        
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing JSON: {str(e)}[/red]")
        return {}

# Example usage
if __name__ == "__main__":
    example_json = '''
    {
        "name": "Test Project",
        "description": "A simple test",
        "tasks": ["task1", "task2"]
    }
    '''
    parsed_data = parse_and_display(example_json)
