"""
Configuration for the Flask server.
"""
import datetime
from flask import Flask
from flask_socketio import SocketIO

# Initialize Flask application
app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.config['SECRET_KEY'] = 'your-s!e43gmt-key'

# Initialize SocketIO with the Flask app
socketio = SocketIO(app)

# Get local timezone for consistent timestamp generation
LOCAL_TIMEZONE = datetime.datetime.now().astimezone().tzinfo
