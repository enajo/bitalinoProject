from flask import Blueprint, render_template, jsonify
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.bitalino_handler import BitalinoHandler

# Create a blueprint for routes
bp = Blueprint("routes", __name__)

# Create a BitalinoHandler instance
bitalino_handler = BitalinoHandler()

# Route for the home page
@bp.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")

# SocketIO events

@socketio.on("connect_bitalino")
def connect_bitalino():
    """Handle the connection to BITalino."""
    try:
        if bitalino_handler.connect():
            emit("status", {"status": "connected"})
        else:
            emit("status", {"status": "connection_failed"})
    except Exception as e:
        emit("status", {"status": f"error: {str(e)}"})

@socketio.on("disconnect_bitalino")
def disconnect_bitalino():
    """Handle the disconnection from BITalino."""
    try:
        bitalino_handler.disconnect()
        emit("status", {"status": "disconnected"})
    except Exception as e:
        emit("status", {"status": f"error: {str(e)}"})

@socketio.on("start_acquisition")
def start_acquisition():
    """Start data acquisition from BITalino."""
    try:
        bitalino_handler.start_acquisition(socketio)
        emit("status", {"status": "acquisition_started"})
    except Exception as e:
        emit("status", {"status": f"error: {str(e)}"})

@socketio.on("stop_acquisition")
def stop_acquisition():
    """Stop data acquisition from BITalino."""
    try:
        bitalino_handler.stop_acquisition()
        emit("status", {"status": "acquisition_stopped"})
    except Exception as e:
        emit("status", {"status": f"error: {str(e)}"})

@socketio.on("join")
def on_join(data):
    """Handle a user joining a room."""
    room = data["room"]
    join_room(room)
    emit("message", {"msg": f"User joined room {room}"}, to=room)

@socketio.on("leave")
def on_leave(data):
    """Handle a user leaving a room."""
    room = data["room"]
    leave_room(room)
    emit("message", {"msg": f"User left room {room}"}, to=room)
