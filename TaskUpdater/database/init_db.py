import sqlite3
from pathlib import Path

def init_db():
    """Initialize the TaskUpdater database"""
    db_dir = Path(__file__).parent
    db_dir.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_dir / 'tasks.db', isolation_level=None)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS task_updates (
            timestamp TEXT,
            user_id TEXT,
            original_message TEXT,
            task_status TEXT
        )
    ''')
    conn.close()

def get_db():
    """Get database connection"""
    db_path = Path(__file__).parent / 'tasks.db'
    return sqlite3.connect(db_path, isolation_level=None)

if __name__ == "__main__":
    init_db() 