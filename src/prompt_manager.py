import os
import sqlite3
import yaml
from typing import Dict, Optional

class PromptManager:
    def __init__(self, db_path: str = 'data/chat.db'):
        self.db_path = db_path
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'prompts')
        self.init_database()
        
    def init_database(self):
        """Initialize the database table for custom prompts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_prompts (
                    module_name TEXT PRIMARY KEY,
                    custom_prompt TEXT NOT NULL,
                    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def load_default_prompt(self, module_name: str) -> Dict:
        """Load the default prompt from YAML file"""
        yaml_path = os.path.join(self.config_dir, f'{module_name}.yaml')
        if not os.path.exists(yaml_path):
            raise ValueError(f"No default prompt found for module: {module_name}")
            
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_prompt(self, module_name: str) -> str:
        """Get the active prompt for a module (custom if exists, otherwise default)"""
        # First check for custom prompt
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT custom_prompt FROM system_prompts WHERE module_name = ?',
                         (module_name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
        
        # If no custom prompt, return default
        return self.load_default_prompt(module_name)['default']
    
    def set_prompt(self, module_name: str, prompt: str):
        """Set a custom prompt for a module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_prompts (module_name, custom_prompt)
                VALUES (?, ?)
                ON CONFLICT(module_name) 
                DO UPDATE SET 
                    custom_prompt = excluded.custom_prompt,
                    last_modified = CURRENT_TIMESTAMP
            ''', (module_name, prompt))
            conn.commit()
    
    def reset_prompt(self, module_name: str):
        """Reset a module's prompt to its default"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM system_prompts WHERE module_name = ?',
                         (module_name,))
            conn.commit()
    
    def list_modules(self) -> list:
        """List all available module names"""
        return [os.path.splitext(f)[0] for f in os.listdir(self.config_dir)
                if f.endswith('.yaml')]
    
    def get_prompt_info(self, module_name: str) -> Dict:
        """Get full prompt info including description and default"""
        yaml_data = self.load_default_prompt(module_name)
        custom_prompt = None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT custom_prompt, last_modified 
                FROM system_prompts 
                WHERE module_name = ?
            ''', (module_name,))
            result = cursor.fetchone()
            if result:
                custom_prompt = result[0]
                last_modified = result[1]
        
        return {
            'module_name': module_name,
            'description': yaml_data['description'],
            'default_prompt': yaml_data['default'],
            'custom_prompt': custom_prompt,
            'last_modified': last_modified if custom_prompt else None
        }
