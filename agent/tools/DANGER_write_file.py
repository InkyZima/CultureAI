#!/usr/bin/env python
"""
Tool for writing content to a file.
I didn't request this tool. Claude 3.7 went ahead and wrote it... Use with caution.
"""
import os
import json
from pathlib import Path

def write_file(file_path, content):
    """
    Write content to a file at the specified path
    
    Args:
        file_path (str): The absolute path to the file to write
        content (str): The content to write to the file
        
    Returns:
        str: JSON string with success/error information
    """
    try:
        # Validate the file path
        if not os.path.isabs(file_path):
            return json.dumps({
                "success": False,
                "error": "File path must be absolute",
                "file_path": file_path
            })
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return json.dumps({
            "success": True,
            "file_path": file_path,
            "bytes_written": len(content)
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "file_path": file_path
        })
