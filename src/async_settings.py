"""Manages async feature settings for the Cultural AI Companion."""

import sqlite3
from dataclasses import dataclass
from typing import Dict, List
import os

@dataclass
class AsyncFeature:
    """Represents an async feature that can be enabled/disabled."""
    name: str
    description: str
    enabled: bool = True
    default: bool = True

class AsyncSettings:
    """Manages settings for async features."""
    
    def __init__(self, db_path: str = 'data/chat.db'):
        """Initialize AsyncSettings.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Define available features
        self.features = {
            'information_extraction': AsyncFeature(
                name='Information Extraction',
                description='Extract and store relevant information from conversations for context.',
                enabled=True
            ),
            'conversation_analysis': AsyncFeature(
                name='Conversation Analysis',
                description='Analyze conversation quality and patterns to improve interactions.',
                enabled=True
            ),
            'instruction_generation': AsyncFeature(
                name='Instruction Generation',
                description='Generate contextual instructions to guide the conversation.',
                enabled=True
            ),
            'time_awareness': AsyncFeature(
                name='Time Awareness',
                description='Adjust responses based on time of day and provide time-appropriate suggestions.',
                enabled=True
            )
        }
        
        self._init_database()
        self._load_settings()
    
    def _init_database(self):
        """Initialize SQLite database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS async_features (
                    feature_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT 1
                )
            ''')
            
            # Insert default features if table is empty
            cursor.execute('SELECT COUNT(*) FROM async_features')
            if cursor.fetchone()[0] == 0:
                for feature_id, feature in self.features.items():
                    cursor.execute(
                        'INSERT INTO async_features (feature_id, name, description, enabled) VALUES (?, ?, ?, ?)',
                        (feature_id, feature.name, feature.description, feature.enabled)
                    )
            conn.commit()
    
    def _load_settings(self):
        """Load settings from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT feature_id, enabled FROM async_features')
            for feature_id, enabled in cursor.fetchall():
                if feature_id in self.features:
                    self.features[feature_id].enabled = bool(enabled)
    
    def get_features(self) -> List[AsyncFeature]:
        """Get list of all features with their current status."""
        return list(self.features.values())
    
    def update_feature(self, feature_id: str, enabled: bool) -> bool:
        """Update feature status.
        
        Args:
            feature_id: ID of the feature to update
            enabled: New enabled status
            
        Returns:
            bool: True if update was successful
        """
        if feature_id not in self.features:
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE async_features SET enabled = ? WHERE feature_id = ?',
                    (enabled, feature_id)
                )
                conn.commit()
                
            self.features[feature_id].enabled = enabled
            return True
        except Exception:
            return False
    
    def is_feature_enabled(self, feature_id: str) -> bool:
        """Check if a feature is enabled.
        
        Args:
            feature_id: ID of the feature to check
            
        Returns:
            bool: True if feature is enabled
        """
        return self.features.get(feature_id, AsyncFeature('', '', False)).enabled
    
    def reset_to_defaults(self) -> bool:
        """Reset all features to their default values.
        
        Returns:
            bool: True if reset was successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for feature_id, feature in self.features.items():
                    cursor.execute(
                        'UPDATE async_features SET enabled = ? WHERE feature_id = ?',
                        (feature.default, feature_id)
                    )
                    feature.enabled = feature.default
                conn.commit()
            return True
        except Exception:
            return False
