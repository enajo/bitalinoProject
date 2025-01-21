// Define a flag to check the connection status
let isConnected = false;

// Grab the button element for connection
const connectButton = document.getElementById('connect-btn');
const statusText = document.getElementById('status-text'); // For displaying connection status

// Add event listener for the button click
connectButton.addEventListener('click', function() {
    if (!isConnected) {
        connectToBITalino();
        isConnected = true;
        connectButton.textContent = 'Disconnect from BITalino'; // Update button text
    } else {
        disconnectFromBITalino();
        isConnected = false;
        connectButton.textContent = 'Connect to BITalino'; // Reset button text
    }
});

// Function to handle connection to BITalino
function connectToBITalino() {
    console.log('Attempting to connect to BITalino sensor...');
    updateStatusText('Connecting to BITalino...');
    
    // Emit event to start the connection to the sensor
    socket.emit('connect_to_sensor', { macAddress: '98:D3:71:FD:62:0B' });
    
    // Listen for successful connection response
    socket.on('connection_success', function(data) {
        console.log('Successfully connected to BITalino: ', data);
        updateStatusText('Connected to BITalino');
        
        // Start the data acquisition after connection
        startAcquisition();
    });

    // Listen for connection error response
    socket.on('connection_error', function(error) {
        console.error('Failed to connect to BITalino:', error);
        updateStatusText('Failed to connect to BITalino. Please try again.');
    });
}

// Function to handle disconnection from BITalino
function disconnectFromBITalino() {
    console.log('Disconnecting from BITalino...');
    updateStatusText('Disconnecting from BITalino...');
    
    // Emit event to stop the connection to the sensor
    socket.emit('disconnect_from_sensor');
    
    // Listen for disconnection confirmation
    socket.on('disconnected', function() {
        console.log('Disconnected from BITalino.');
        updateStatusText('Disconnected from BITalino');
        
        // Stop data acquisition when disconnected
        stopAcquisition();
    });
}

// Function to start acquisition of data from BITalino
function startAcquisition() {
    console.log('Starting data acquisition...');
    updateStatusText('Starting data acquisition...');
    
    // Add logic to begin real-time data acquisition from BITalino
    // Example: Start reading data from the sensor and updating the graph
    // Use WebSocket, HTTP requests, or any other mechanism to get real-time data
    
    // Placeholder for actual acquisition logic:
    // setInterval(updateGraph, 1000); // Example to update graph every second (adjust as needed)
}

// Function to stop the data acquisition
function stopAcquisition() {
    console.log('Stopping data acquisition...');
    updateStatusText('Stopping data acquisition...');
    
    // Add logic to stop reading data from BITalino
    // For example, you could stop the interval or halt WebSocket communication
}

// Function to update the status text on the UI
function updateStatusText(message) {
    statusText.textContent = message;
}

// Placeholder function to simulate graph updates (example)
function updateGraph() {
    // Example: Update the graph with real-time data
    // You would integrate this with your actual graph plotting logic (e.g., Plotly, Chart.js)
    console.log("Updating graph with new data...");
}
