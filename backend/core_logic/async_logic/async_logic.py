import threading
from flask import jsonify
import time

def hello_world_task():
    time.sleep(5)
    print("Hello world from do_async_stuff.")

def do_async_stuff():
    """Does all the other async stuff concurrently to the main chat flow.
    
    
    Creates system instructions to be injected into user messages, based on: 
        Current time + 
        Analysis of current chat conversation + 
        static chat objectives list.  
    """
    thread = threading.Thread(target=hello_world_task) # Create a thread
    thread.start() # Start the thread

