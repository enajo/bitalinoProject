document.addEventListener('DOMContentLoaded', () => {
    // Handle file upload
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const formData = new FormData(uploadForm);
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();
                if (result.success) {
                    initializeRealTimeChart();
                } else {
                    console.error('Upload failed:', result.error);
                }
            } catch (error) {
                console.error('Upload error:', error);
            }
        });
    }

    // Initialize real-time chart
    function initializeRealTimeChart() {
        const ctx = document.getElementById('realTimeChart').getContext('2d');
        const realTimeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Real-Time EMG Data',
                    data: [],
                    borderColor: 'blue',
                    borderWidth: 2,
                    fill: false,
                }],
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time',
                        },
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Signal Value',
                        },
                    },
                },
            },
        });

        // Simulate real-time updates
        const socket = io.connect();
        socket.on('update_chart', (data) => {
            const time = new Date().toLocaleTimeString();
            realTimeChart.data.labels.push(time);
            realTimeChart.data.datasets[0].data.push(data.value);

            // Keep the chart to the last 20 data points
            if (realTimeChart.data.labels.length > 20) {
                realTimeChart.data.labels.shift();
                realTimeChart.data.datasets[0].data.shift();
            }

            realTimeChart.update();
        });
    }
});
