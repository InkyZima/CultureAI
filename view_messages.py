import sqlite3
import json
from datetime import datetime

def format_timestamp(timestamp):
    """Format ISO timestamp to a readable format."""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def view_messages(limit=20):
    """View the most recent messages from the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect('messages.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query the messages
        cursor.execute(
            "SELECT * FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        
        # Print header
        print("\n=== Recent Messages ===")
        print(f"{'ID':<5} {'Role':<10} {'Timestamp':<20} {'Message':<50}")
        print("="*85)
        
        # Print each message
        for row in rows:
            # Format the timestamp
            formatted_time = format_timestamp(row['timestamp'])
            
            # Format and print the message
            print(f"{row['id']:<5} {row['role']:<10} {formatted_time:<20} {row['message'][:50]}")
        
        print(f"\nTotal messages: {len(rows)}")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        print(f"Error viewing messages: {e}")

if __name__ == "__main__":
    view_messages()
