import time
import threading
import numpy as np
from flask_socketio import emit, SocketIO
from .sensor_manager import SensorManager

socketio = SocketIO()

# Global sensor manager instance
sensor_manager = SensorManager("98:D3:71:FD:62:0B", 1)

def register_socket_events():
    @socketio.on('connect')
    def handle_connect():
        emit('status', {'message': 'Connected to WebSocket'})

    @socketio.on('disconnect')
    def handle_disconnect():
        sensor_manager.stop_acquisition()
        emit('status', {'message': 'Disconnected from WebSocket'})

    @socketio.on('connect_device')
    def connect_device():
        try:
            sensor_manager.connect()
            emit('status', {'message': 'BITalino connected!'})
        except Exception as e:
            emit('status', {'message': f'Error connecting: {str(e)}'})

    @socketio.on('start_acquisition')
    def start_acquisition():
        def stream_data():
            try:
                sensor_manager.start_acquisition()
                while sensor_manager.is_acquiring:
                    data = sensor_manager.read_data()
                    raw = data[:, -1].tolist()
                    envelope = np.mean(np.abs(np.diff(raw)))
                    socketio.emit('data', {'raw': raw, 'envelope': envelope})
                    time.sleep(0.1)
            except Exception as e:
                emit('status', {'message': f'Error during acquisition: {str(e)}'})

        thread = threading.Thread(target=stream_data)
        thread.start()

    @socketio.on('stop_acquisition')
    def stop_acquisition():
        sensor_manager.stop_acquisition()
        emit('status', {'message': 'Acquisition stopped'})
