import bitalino

class SensorManager:
    def __init__(self, mac_address, channel):
        self.mac_address = mac_address
        self.channel = channel
        self.device = None

    def connect(self):
        try:
            self.device = bitalino.BITalino(self.mac_address)
            return "Connected"
        except Exception as e:
            return f"Connection failed: {e}"

    def disconnect(self):
        if self.device:
            self.device.close()

    def start_acquisition(self, sampling_rate=1000, nframes=100):
        try:
            self.device.start(sampling_rate, [self.channel])
            return "Data acquisition started"
        except Exception as e:
            return f"Failed to start acquisition: {e}"

    def stop_acquisition(self):
        try:
            self.device.stop()
            return "Data acquisition stopped"
        except Exception as e:
            return f"Failed to stop acquisition: {e}"

    def read_data(self, nframes=100):
        try:
            data = self.device.read(nframes)
            emg_signal = data[:, self.channel]
            envelope = abs(emg_signal).mean()
            return {"raw": emg_signal.tolist(), "envelope": envelope}
        except Exception as e:
            return f"Error reading data: {e}"
