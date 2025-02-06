import sqlite3

def check_database():
    with sqlite3.connect('data/chat.db') as conn:
        cursor = conn.cursor()
        
        # Check messages table
        print("\nMessages in database:")
        cursor.execute('SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT 5')
        for role, content in cursor.fetchall():
            print(f"{role}: {content}")
            
        # Check extracted information
        print("\nExtracted information:")
        cursor.execute('SELECT timestamp, category, item FROM extracted_information ORDER BY timestamp DESC LIMIT 10')
        for timestamp, category, item in cursor.fetchall():
            print(f"{timestamp} - {category}: {item}")

if __name__ == "__main__":
    check_database() 