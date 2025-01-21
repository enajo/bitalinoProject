from bitalino import BITalino
import time

class BitalinoHandler:
    """Handles BITalino device operations."""

    def __init__(self):
        self.device = None
        self.connected = False
        self.acquiring = False

    def connect(self):
        """Connect to the BITalino device."""
        try:
            mac_address = "98:D3:71:FD:62:0B"  # Replace with your BITalino MAC address
            print(f"Connecting to BITalino at MAC address: {mac_address}")
            self.device = BITalino(mac_address)
            self.connected = True
            print("Connection successful!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from the BITalino device."""
        if self.device:
            print("Disconnecting BITalino...")
            self.device.close()
        self.connected = False
        self.acquiring = False
        print("Disconnected successfully.")

    def start_acquisition(self, socketio):
        """Start data acquisition from the BITalino device."""
        if not self.connected:
            raise Exception("BITalino device is not connected.")

        self.acquiring = True
        try:
            sampling_rate = 100  # Sampling rate in Hz
            channels = [0]  # Channel to acquire data from
            print(f"Starting acquisition at {sampling_rate} Hz on channels {channels}")
            self.device.start(sampling_rate, channels)

            # Read data continuously in a separate thread
            while self.acquiring:
                data = self.device.read(10)  # Read 10 samples
                print(f"Data acquired: {data.tolist()}")
                socketio.emit("data", {"data": data.tolist()})
                time.sleep(0.01)
        except Exception as e:
            print(f"Error during acquisition: {e}")
        finally:
            self.stop_acquisition()

    def stop_acquisition(self):
        """Stop data acquisition from the BITalino device."""
        if self.device and self.acquiring:
            print("Stopping acquisition...")
            self.device.stop()
        self.acquiring = False
        print("Acquisition stopped.")
