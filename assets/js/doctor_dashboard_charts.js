document.addEventListener('DOMContentLoaded', function () {

    function getJsonData(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return null;
        return JSON.parse(element.textContent);
    }

    // ===== Monthly Bookings Bar Chart =====
    const monthlyCanvas = document.getElementById('monthlyBookingsChart');
    const monthlyData = getJsonData('monthly-bookings-data');

    if (monthlyCanvas && monthlyData) {
        const monthlyCtx = monthlyCanvas.getContext('2d');
        new Chart(monthlyCtx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Bookings per Month',
                    data: monthlyData,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // ===== Appointment Status Pie Chart =====
    const statusCanvas = document.getElementById('statusPieChart');
    const pieLabels = getJsonData('pie-chart-labels');
    const pieData = getJsonData('pie-chart-data');
    const pieColors = getJsonData('pie-chart-colors');

    if (statusCanvas && pieLabels && pieData && pieColors) {
        const statusCtx = statusCanvas.getContext('2d');
        new Chart(statusCtx, {
            type: 'pie',
            data: {
                labels: pieLabels,
                datasets: [{
                    label: 'Appointment Statuses',
                    data: pieData,
                    backgroundColor: pieColors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
});