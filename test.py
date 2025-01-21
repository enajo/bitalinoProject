import time
from bitalino import BITalino
import numpy as np

# BITalino sensor MAC address
MAC_ADDRESS = '98:D3:71:FD:62:0B'

# Sample rate and the A1 channel index
SAMPLE_RATE = 1000  # Samples per second
CHANNEL_INDEX = 0  # A1 channel index in the BITalino data

# Apply a simple moving average to smooth the EMG signal
def smooth_signal(emg_data, window_size=5):
    return np.convolve(emg_data, np.ones(window_size) / window_size, mode='valid')

def connect_to_bitalino():
    try:
        # Initialize the BITalino sensor with the provided MAC address
        sensor = BITalino(MAC_ADDRESS)
        sensor.start()  # Start the sensor (enable it for data acquisition)
        print(f"Connected to BITalino sensor with MAC address {MAC_ADDRESS}")
        return sensor
    except Exception as e:
        print(f"Error connecting to BITalino sensor: {e}")
        return None

def read_bitalino_data(sensor, num_samples=10):
    try:
        # Read multiple samples from the sensor at once
        data = sensor.read(num_samples)
        emg_data_list = []

        # Process each sample and extract the A1 channel data
        for sample in data:
            emg_data = sample[CHANNEL_INDEX]  # A1 data is in the 0th index of each sample
            emg_data_list.append(emg_data)
            print(f"Raw Data (A1 Channel): {emg_data}")

        # Apply smoothing to the data
        smoothed_data = smooth_signal(emg_data_list)

        # Print smoothed EMG data
        for smoothed in smoothed_data:
            print(f"Smoothed Real-time EMG Data (A1 Channel): {smoothed}")

    except Exception as e:
        print(f"Error reading data from BITalino sensor: {e}")

def main():
    print("Testing BITalino connection...")
    sensor = connect_to_bitalino()  # Connect to BITalino sensor

    if sensor:
        print("Starting data acquisition...")
        try:
            while True:
                read_bitalino_data(sensor)  # Read and process data from A1 channel
                time.sleep(1 / SAMPLE_RATE)  # Delay based on the sample rate (e.g., 1 ms for 1000 Hz sampling rate)
        except KeyboardInterrupt:
            print("Data acquisition stopped.")
            sensor.stop()  # Stop the sensor when done
    else:
        print("Failed to connect to BITalino sensor.")

if __name__ == "__main__":
    main()
