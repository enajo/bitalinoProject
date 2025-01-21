// graph.js
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById("fileInput");
    const chartDiv = document.getElementById("chart");
    let data = [];

    // Read the file and parse the data
    fileInput.addEventListener("change", handleFileUpload);

    function handleFileUpload(event) {
        const file = event.target.files[0];
        const reader = new FileReader();

        reader.onload = function(e) {
            const fileContent = e.target.result;
            parseFileData(fileContent);
        };

        reader.readAsText(file);
    }

    // Parse the content of the uploaded .txt file
    function parseFileData(fileContent) {
        const lines = fileContent.split("\n");
        data = [];

        lines.forEach(line => {
            const values = line.split("\t");
            if (values.length > 1) {
                data.push({
                    time: parseFloat(values[0]),
                    emg: parseFloat(values[1])
                });
            }
        });

        drawGraph(data);
    }

    // Draw graph using D3.js
    function drawGraph(data) {
        const margin = { top: 20, right: 30, bottom: 40, left: 40 };
        const width = 800 - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        // Clear previous chart
        chartDiv.innerHTML = "";

        // Set up the SVG canvas
        const svg = d3.select(chartDiv)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Set the scales
        const x = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.time)])
            .range([0, width]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.emg)])
            .range([height, 0]);

        // Add the X axis
        svg.append("g")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(x));

        // Add the Y axis
        svg.append("g")
            .call(d3.axisLeft(y));

        // Draw the line
        svg.append("path")
            .data([data])
            .attr("fill", "none")
            .attr("stroke", "#2575fc")
            .attr("stroke-width", 2)
            .attr("d", d3.line()
                .x(d => x(d.time))
                .y(d => y(d.emg))
            );
    }

    // Optional: Dynamically update the chart at regular intervals if needed
    function updateGraph() {
        // This can be used to fetch new data and redraw the graph
        // e.g., if you're polling for new sensor data.
    }
});
