"""
Placeholder handler module for agent prompt templates.

This module defines placeholder handling functions for all known placeholders
used in agent prompt templates. It provides functions to detect placeholders
in templates and replace them with appropriate values.
"""

import datetime
import re
from typing import Dict, Any, List, Callable, Optional

# Import database for accessing message and injection history
try:
    from database import MessageDatabase
    db = MessageDatabase()
except ImportError:
    # When running from a test script in a different directory
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import MessageDatabase
    db = MessageDatabase()


class PlaceholderHandler:
    """
    Handles the detection and replacement of placeholders in prompt templates.
    
    This class stores all known placeholders and their corresponding handler functions,
    and provides methods to detect and replace placeholders in any template.
    """
    
    def __init__(self):
        """Initialize the placeholder registry with all known placeholder handlers."""
        # Registry of placeholder handlers: maps placeholder name to handler function
        self.handlers: Dict[str, Callable[[], str]] = {
            "timestamp": self._handle_timestamp,
            "chat_history": self._handle_chat_history,
            "unconsumed_injections": self._handle_unconsumed_injections
        }
    
    def process_template(self, template: str) -> str:
        """
        Process a template string and replace all known placeholders.
        
        Args:
            template (str): The template string with placeholders
            
        Returns:
            str: The processed template with placeholders replaced
        """
        # Find all placeholders in the template using regex
        placeholders = self._find_placeholders(template)
        
        # Replace each placeholder with its value
        processed_template = template
        for placeholder in placeholders:
            if placeholder in self.handlers:
                replacement = self.handlers[placeholder]()
                processed_template = processed_template.replace(f"{{{placeholder}}}", replacement)
            else:
                # Log unknown placeholders
                print(f"Warning: Unknown placeholder '{placeholder}' found in template")
        
        return processed_template
    
    def _find_placeholders(self, template: str) -> List[str]:
        """
        Find all placeholders in a template string.
        
        Args:
            template (str): The template string to search
            
        Returns:
            List[str]: List of placeholder names without the curly braces
        """
        # Use regex to find all {placeholder} patterns
        placeholders = re.findall(r'{([^{}]+)}', template)
        return placeholders
    
    def register_placeholder(self, name: str, handler: Callable[[], str]) -> None:
        """
        Register a new placeholder handler.
        
        Args:
            name (str): The placeholder name (without curly braces)
            handler (Callable[[], str]): Function that returns the replacement string
        """
        self.handlers[name] = handler
    
    def get_all_placeholders(self) -> List[str]:
        """
        Get a list of all registered placeholder names.
        
        Returns:
            List[str]: List of all registered placeholder names
        """
        return list(self.handlers.keys())
    
    # Handler functions for standard placeholders
    
    def _handle_timestamp(self) -> str:
        """Return the current timestamp in ISO format."""
        return datetime.datetime.now().isoformat()
    
    def _handle_chat_history(self) -> str:
        """Format the recent chat history."""
        # Get chat history from database and format it
        messages = db.get_messages(limit=20)  # Get last 20 messages
        messages.reverse()  # Display in chronological order
        
        chat_history_str = ""
        for msg in messages:
            role = msg.get('role', '')
            text = msg.get('message', '')
            timestamp = msg.get('timestamp', '')
            # Format with timestamp if available
            if timestamp:
                chat_history_str += f"[{timestamp}] {role}: {text}\n\n"
            else:
                chat_history_str += f"{role}: {text}\n\n"
        
        # Default message if no history available
        if not chat_history_str:
            chat_history_str = "No chat history available yet."
            
        return chat_history_str
    
    def _handle_unconsumed_injections(self) -> str:
        """Format the unconsumed injections."""
        # Get unconsumed injections from database and format them
        injections = db.get_injections(consumed=False)
        unconsumed_injections_str = ""
        for injection in injections:
            instruction = injection.get('injection', '')
            timestamp = injection.get('timestamp', '')
            if timestamp and instruction:
                unconsumed_injections_str += f"[{timestamp}] {instruction}\n"
        
        # Default message if no unconsumed injections
        if not unconsumed_injections_str:
            unconsumed_injections_str = "No pending instructions."
            
        return unconsumed_injections_str


# Create a singleton instance for use throughout the application
placeholder_handler = PlaceholderHandler()


def process_template(template: str) -> str:
    """
    Process a template string and replace all known placeholders.
    
    Args:
        template (str): The template string with placeholders
        
    Returns:
        str: The processed template with placeholders replaced
    """
    return placeholder_handler.process_template(template)


def register_custom_placeholder(name: str, handler: Callable[[], str]) -> None:
    """
    Register a custom placeholder handler.
    
    Args:
        name (str): The placeholder name (without curly braces)
        handler (Callable[[], str]): Function that returns the replacement string
    """
    placeholder_handler.register_placeholder(name, handler)


def get_available_placeholders() -> List[str]:
    """
    Get a list of all available placeholder names.
    
    Returns:
        List[str]: List of all registered placeholder names
    """
    return placeholder_handler.get_all_placeholders()
