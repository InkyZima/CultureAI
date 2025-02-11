"""
This code contains the implementation of sqlite initialization and sqlite writing/retrival functions.
"""
import sqlite3
import time
import logging
from langchain.schema import HumanMessage, AIMessage
import os

# Define absolute path to the database file
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
history_db_file = os.path.join(base_dir, 'data', 'conversation_history.db')

# Ensure the data directory exists
os.makedirs(os.path.dirname(history_db_file), exist_ok=True)


def create_table():
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def load_history():
    history = []
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT type, content FROM chat_history ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    for row in rows:
        message_type, content = row
        if message_type == "human":
            history.append(HumanMessage(content=content))
        elif message_type == "ai":
            history.append(AIMessage(content=content))
    conn.close()
    return history

def save_history(history):
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history") # Clear old history for simplicity
    for message in history:
        if isinstance(message, HumanMessage):
            msg_type = "human"
        elif isinstance(message, AIMessage):
            msg_type = "ai"
        else:
            logging.warning(f"Unknown message type: {type(message)}, skipping save for this message.")
            continue # Skip messages that are not HumanMessage or AIMessage

        cursor.execute("INSERT INTO chat_history (type, content, timestamp) VALUES (?, ?, ?)",
                       (msg_type, message.content, time.time()))
    conn.commit()
    conn.close()
    logging.debug("history saved to database")


def clear_history():
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()