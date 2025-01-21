import bitalino
import numpy as np

class SensorManager:
    def __init__(self, mac_address, channel):
        self.mac_address = mac_address
        self.channel = channel
        self.device = None
        self.is_acquiring = False

    def connect(self):
        self.device = bitalino.BITalino(self.mac_address)

    def start_acquisition(self):
        if self.device:
            self.device.start(1000, [self.channel])
            self.is_acquiring = True

    def read_data(self):
        if self.device and self.is_acquiring:
            return self.device.read(100)
        return np.array([])

    def stop_acquisition(self):
        if self.device:
            self.device.stop()
            self.device.close()
            self.is_acquiring = False
