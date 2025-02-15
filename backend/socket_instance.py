from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = '$%#^hgf*&(&)'
socketio = SocketIO(app, cors_allowed_origins="*")

def get_socketio_instance():
    return socketio

def get_app_instance():
    return app