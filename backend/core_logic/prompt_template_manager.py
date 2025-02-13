"""
This file is a utility module for managing prompt templates used in the backend of the LLM chat application.
It provides functionalities to load prompt templates from text files stored in a designated directory,
and to retrieve specific templates by their names. This allows for easy organization and reuse of different prompt strategies
within the application's LLM invocation logic.
"""

import os
from langchain.prompts import PromptTemplate

PROMPT_TEMPLATE_DIR = "backend/prompt_templates"  # Directory to store prompt template files

def load_templates():
    """Loads prompt templates from files in the prompt_templates directory."""
    templates = {}
    if not os.path.exists(PROMPT_TEMPLATE_DIR):
        os.makedirs(PROMPT_TEMPLATE_DIR)  # Create directory if it doesn't exist

    for template_name in os.listdir(PROMPT_TEMPLATE_DIR):
        template_dir = os.path.join(PROMPT_TEMPLATE_DIR, template_name)
        if os.path.isdir(template_dir):  # Check if it's a directory (template folder)
            template_file = os.path.join(template_dir, f"{template_name}.txt") # Construct expected filename
            if os.path.exists(template_file):
                try:
                    with open(template_file, "r") as f:
                        template_content = f.read()
                        templates[template_name] = PromptTemplate.from_template(template_content)  # Load as Langchain PromptTemplate
                except Exception as e: # Handle potential errors (e.g., file reading, invalid template)
                    print(f"Error loading template {template_name}: {e}")
            else:
                print(f"Warning: Template file {template_name}.txt not found in directory {template_dir}")

    return templates

def get_template_names(templates):
    """Returns a list of available prompt template names."""
    return list(templates.keys())

def get_template_by_name(templates, template_name):
    """Retrieves a prompt template by its name."""
    return templates.get(template_name)

# Load templates when the module is initialized
prompt_templates = load_templates()