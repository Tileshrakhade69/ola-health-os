/**
 * OLA Health OS - Chart.js Rendering Utilities
 */

const HealthcareCharts = {
    // Theme colors
    colors: {
        primary: '#0284c7',
        primaryAlpha: 'rgba(2, 132, 199, 0.15)',
        teal: '#0d9488',
        tealAlpha: 'rgba(13, 148, 136, 0.2)',
        amber: '#d97706',
        red: '#dc2626',
        green: '#16a34a',
        palette: [
            '#0284c7', '#0d9488', '#8b5cf6', '#f59e0b',
            '#ec4899', '#10b981', '#6366f1', '#64748b'
        ]
    },

    // 1. Line / Area Trend Chart
    createTrendChart(ctxId, labels, data, label = 'Metric', color = '#0284c7') {
        const ctx = document.getElementById(ctxId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    borderColor: color,
                    backgroundColor: 'rgba(2, 132, 199, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { size: 11 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 }, maxRotation: 45 }
                    }
                }
            }
        });
    },

    // 2. Bar Chart
    createBarChart(ctxId, labels, data, label = 'Volume', color = '#0284c7') {
        const ctx = document.getElementById(ctxId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: color,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { size: 11 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    }
                }
            }
        });
    },

    // 3. Doughnut / Pie Chart
    createDoughnutChart(ctxId, labels, data) {
        const ctx = document.getElementById(ctxId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: this.colors.palette,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { boxWidth: 12, font: { size: 11 } }
                    }
                },
                cutout: '65%'
            }
        });
    }
};
