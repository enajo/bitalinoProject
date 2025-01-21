from flask import Flask, render_template, jsonify
import random
import threading
import time

app = Flask(__name__)

# Global variable to store the EMG data
emg_data = []

# Flag to control data collection
collecting_data = False

# Function to simulate collecting data from the BITalino sensor
def collect_emg_data():
    global emg_data, collecting_data
    while collecting_data:
        # Simulate random EMG data (10 channels)
        emg_data.append([random.randint(0, 1023) for _ in range(10)])
        time.sleep(1)  # Collect data every second

# Start data collection in a separate thread
def start_data_collection():
    global collecting_data
    collecting_data = True
    threading.Thread(target=collect_emg_data, daemon=True).start()

# Stop data collection
def stop_data_collection():
    global collecting_data
    collecting_data = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start():
    start_data_collection()
    return jsonify({"status": "started"})

@app.route('/stop')
def stop():
    stop_data_collection()
    return jsonify({"status": "stopped"})

@app.route('/data')
def get_data():
    return jsonify({"data": emg_data})

if __name__ == '__main__':
    app.run(debug=True)
