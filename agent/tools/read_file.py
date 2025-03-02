import os
import json

def read_file(file_path):
    """
    Read a file and return its contents as a string.
    
    Args:
        file_path (str): Absolute path to the file to be read
    
    Returns:
        str: File contents as a string if successful, error message if not
    """
    try:
        if not os.path.isabs(file_path):
            return json.dumps({
                "error": f"File path '{file_path}' is not absolute"
            })
        
        if not os.path.exists(file_path):
            return json.dumps({
                "error": f"File not found: '{file_path}'"
            })
            
        if not os.path.isfile(file_path):
            return json.dumps({
                "error": f"Path is not a file: '{file_path}'"
            })
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        return json.dumps({
            "content": content,
            "file_path": file_path
        })
        
    except Exception as e:
        return json.dumps({
            "error": f"Error reading file: {str(e)}"
        })

# Define the tool specification for Google Generative AI 0.8.4
TOOL_SPEC = {
    "function_declarations": [
        {
            "name": "read_file",
            "description": "Read the contents of a file given its absolute path",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "file_path": {
                        "type": "STRING",
                        "description": "Absolute path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    ]
}