"""
This code contains the implementation of sqlite initialization and sqlite writing/retrival functions.
"""
import sqlite3
import logging
from langchain.schema import HumanMessage, AIMessage
import os
import datetime

# Define absolute path to the database file
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
history_db_file = os.path.join(base_dir, 'data', 'conversation_history.db')

# Ensure the data directory exists
os.makedirs(os.path.dirname(history_db_file), exist_ok=True)

# injections table creation is currently in message_injector.py
def create_tables():
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS injections (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, timestamp TEXT NOT NULL)")
    conn.commit()
    conn.close()

def load_history():
    history = []
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT type, content, timestamp FROM chat_history ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    for row in rows:
        message_type, content, timestamp = row
        if message_type == "human":
            history.append(HumanMessage(content=content, timestamp=timestamp))
        elif message_type == "ai":
            history.append(AIMessage(content=content, timestamp=timestamp))
    conn.close()
    return history

def load_history_today():
    history = []
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, content, timestamp FROM chat_history WHERE substr(timestamp, 1, 10) = ? ORDER BY timestamp ASC",
        (datetime.datetime.now().date().isoformat(),)
    )
    rows = cursor.fetchall()
    for row in rows:
        message_type, content, timestamp = row
        if message_type == "human":
            history.append(HumanMessage(content=content, timestamp=timestamp))
        elif message_type == "ai":
            history.append(AIMessage(content=content, timestamp=timestamp))
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
                       (msg_type, message.content, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logging.debug("history saved to database")

def save_injection_message(message):
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO injections (message, timestamp) VALUES (?,?)", (message.replace("\n", ""), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def clear_history():
    conn = sqlite3.connect(history_db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    cursor.execute("DELETE FROM injections")
    conn.commit()
    conn.close()

