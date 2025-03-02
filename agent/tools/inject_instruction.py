#!/usr/bin/env python
"""
Tool for injecting instructions into the conversation between Chat-AI and user
"""
import json
import datetime
import sys
import os

# Add the parent directory to the system path so we can import the database module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from database import MessageDatabase

def inject_instruction(instruction):
    """
    Inject an instruction into the conversation between Chat-AI and user.
    The instruction will be considered by the Chat-AI when replying to the user next time.
    
    Args:
        instruction (str): The instruction to inject
        
    Returns:
        str: JSON string with success/error information
    """
    try:
        if not instruction or not isinstance(instruction, str):
            return json.dumps({
                "success": False,
                "error": "Instruction must be a non-empty string"
            })
        
        # Create injection object
        injection = {
            'injection': instruction,
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'Agent',
            'consumed': False
        }
        
        # Save to the database
        db = MessageDatabase()
        success = db.save_injection(injection)
        
        # Try to import the injections array from app.py dynamically
        # This is needed for the live application, but might not work in testing
        try:
            # We import this within the try block to avoid initializing the app during testing
            # Get a reference to the global injections list without importing the whole app
            # This approach prevents the automatic deletion of injections
            import importlib.util
            import sys
            
            # Try to find app.py in the project root
            app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'app.py'))
            
            if os.path.exists(app_path):
                # Load app.py without executing the module initialization code
                spec = importlib.util.spec_from_file_location("app_module", app_path)
                app_module = importlib.util.module_from_spec(spec)
                
                # Get the injections list only if it exists
                if hasattr(app_module, 'injections'):
                    app_module.injections.append(injection)
                    print(f"Added injection to app.injections: {injection}")
                else:
                    print("app.injections list not found, skipping memory injection")
            else:
                print(f"app.py not found at {app_path}, skipping memory injection")
                
        except Exception as import_error:
            # This is expected during testing or if app isn't initialized
            print(f"Note: Could not add to app.injections array: {import_error}")
            # This doesn't affect database storage, so we can continue
        
        return json.dumps({
            "success": success,
            "message": "Instruction injected successfully",
            "instruction": instruction,
            "timestamp": injection['timestamp']
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# Define the tool specification for Google Generative AI 
TOOL_SPEC = {
    "name": "inject_instruction",
    "description": "Inject an instruction into the conversation between Chat-AI and user. The instruction will be considered by the Chat-AI when replying to the user next time.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "instruction": {
                "type": "STRING",
                "description": "The instruction to inject. Examples: 'Ask the user if they meditated this morning.', 'Suggest to the user to do some physical exercise after work.'"
            }
        },
        "required": ["instruction"]
    }
}
