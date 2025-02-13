"""
This code pre-processes chat messages from the user before they are sent to the chat llm to generate a response. This code injects additional instructions into that user chat message.
"""

import datetime
import sqlite3
import os


def inject_system_message(user_message):
    """Inject system instructions into user messages.

    Pre-processes user messages received by the API server from the frontend/user, and injects system instructions (by appending them to the end of the user message like so: ... \n[System instruction: Ask the user what they ate for breakfast today.]
    """
    # fetch the last entry from the database conversation_history.db table injections and append them to the user_message
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'conversation_history.db'))
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='injections'")
    if not c.fetchone():
        c.execute("CREATE TABLE injections (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, timestamp REAL NOT NULL)")
    c.execute("SELECT message FROM injections ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    if row is not None:
        if row[0] and row[0].strip() != "":
            user_message = user_message + "\n[System instruction: " + row[0] + "]"
    conn.close()

    return user_message


def inject_datetime(user_message):
    """Inject datetime
    
    The LLM needs to know the time of day when the user is writing them, so that they can use this context to know how to answer. E.g. the LLm shouldn't ask for lunch plans if it's past lunch time.
    """ 
    return "User on " + datetime.datetime.now().strftime("%H:%M") + ": " + user_message