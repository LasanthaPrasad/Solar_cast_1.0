document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('locationComparisonChart').getContext('2d');
    let chart;

    function createChart(data) {
        const datasets = Object.keys(data).map((location, index) => {
            const color = `hsl(${index * 90}, 70%, 50%)`;
            return {
                label: location,
                data: data[location].map(point => ({ x: new Date(point.timestamp), y: point.ghi })),
                borderColor: color,
                backgroundColor: color,
                fill: false,
                tension: 0.4
            };
        });

        chart = new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'hour',
                            displayFormats: {
                                hour: 'MMM D, HH:mm'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'GHI (W/m²)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'GHI Forecast Comparison for 4 Locations'
                    }
                }
            }
        });
    }

    function updateChart() {
        fetch('/api/multi_location_forecast')
            .then(response => response.json())
            .then(data => {
                if (chart) {
                    chart.destroy();
                }
                createChart(data);
            })
            .catch(error => console.error('Error fetching forecast data:', error));
    }

    updateChart();
    // Update the chart every 5 minutes
    setInterval(updateChart, 5 * 60 * 1000);
});