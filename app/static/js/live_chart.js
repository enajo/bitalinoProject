const canvas = document.getElementById("emg-graph");
const ctx = canvas.getContext("2d");

let data = [];
let connectionStatus = document.getElementById("connection-status");

function updateGraph() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    data.forEach((value, index) => {
        const x = (index / data.length) * canvas.width;
        const y = canvas.height - (value / 1023) * canvas.height;
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
}

function fetchData() {
    fetch("/live-data")
        .then(response => response.json())
        .then(json => {
            data = json.data;
            updateGraph();
        });
}

function fetchStatus() {
    fetch("/connection-status")
        .then(response => response.json())
        .then(json => {
            connectionStatus.textContent = json.connected
                ? `Connected (Battery: ${json.battery_level}%)`
                : "Disconnected";
        });
}

setInterval(fetchData, 100);
setInterval(fetchStatus, 5000);
