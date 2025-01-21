from flask import Flask, render_template, jsonify
from app.collect_data import SensorManager

app = Flask(__name__)
sensor_manager = SensorManager()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/connection-status")
def connection_status():
    return jsonify({
        "connected": sensor_manager.is_connected,
        "battery": sensor_manager.battery_level
    })

@app.route("/live-data")
def live_data():
    return jsonify(sensor_manager.get_live_data())
