"""
This code pre-processes chat messages from the user before they are sent to the chat llm to generate a response. This code injects additional instructions into that user chat message.
"""

import datetime

def inject_system_message(user_message):
    """Inject system instructions into user messages.

    Pre-processes user messages received by the API server from the frontend/user, and injects system instructions (by appending them to the end of the user message like so: ... \n[System instruction: Ask the user what they ate for breakfast today.]
    """
    # dummy implementation - do nothing for now
    return user_message


def inject_datetime(user_message):
    """Inject datetime
    
    The LLM needs to know the time of day when the user is writing them, so that they can use this context to know how to answer. E.g. the LLm shouldn't ask for lunch plans if it's past lunch time.
    """

    return "User on " + datetime.datetime.now().strftime("%H:%M") + ": " + user_message