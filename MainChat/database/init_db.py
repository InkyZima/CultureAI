import sqlite3
from pathlib import Path

def init_db():
    """Initialize the MainChat database"""
    # Create database directory if it doesn't exist
    db_dir = Path(__file__).parent
    db_dir.mkdir(exist_ok=True)
    
    # Connect to database and create tables
    conn = sqlite3.connect(db_dir / 'mainchat.db', isolation_level=None)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            timestamp TEXT,
            user_id TEXT,
            party TEXT,  -- 'user' or 'ai'
            content TEXT,
            system_prompt TEXT
        )
    ''')
    conn.close()

def get_db():
    """Get database connection"""
    db_path = Path(__file__).parent / 'mainchat.db'
    return sqlite3.connect(db_path, isolation_level=None)

if __name__ == "__main__":
    init_db()
