# Chart.js Templates for Outside Brand

Complete Chart.js configuration templates using Outside brand styling.

## Color Array

```javascript
const outsideColors = {
    primary: '#FFD100',
    primaryDark: '#E6BC00',
    black: '#000000',
    darkGray: '#333333',
    mediumGray: '#666666',
    lightGray: '#999999',
    lighterGray: '#CCCCCC',
};

const chartPalette = [
    '#FFD100', '#000000', '#333333', '#666666',
    '#999999', '#CCCCCC', '#E6BC00', '#B8960A'
];
```

## Line Chart (Activity Over Time)

```javascript
new Chart(ctx, {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [{
            label: 'Activity',
            data: monthlyData,
            borderColor: '#FFD100',
            backgroundColor: 'rgba(255, 209, 0, 0.15)',
            pointBackgroundColor: '#000000',
            pointBorderColor: '#FFD100',
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7,
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: '#000000',
                titleColor: '#FFD100',
                bodyColor: '#FFFFFF',
                borderColor: '#FFD100',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    color: '#666666'
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    color: '#666666'
                }
            }
        }
    }
});
```

## Bar Chart (Horizontal - Rankings)

```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: categoryLabels,
        datasets: [{
            label: 'Count',
            data: categoryData,
            backgroundColor: '#FFD100',
            borderColor: '#E6BC00',
            borderWidth: 1,
            borderRadius: 4
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: '#000000',
                titleColor: '#FFD100',
                bodyColor: '#FFFFFF'
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    color: '#666666'
                }
            },
            y: {
                grid: {
                    display: false
                },
                ticks: {
                    color: '#333333',
                    font: {
                        weight: 500
                    }
                }
            }
        }
    }
});
```

## Bar Chart (Vertical - Time Series)

```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: hourLabels,
        datasets: [{
            label: 'Events',
            data: hourlyData,
            backgroundColor: function(context) {
                // Highlight peak hour
                const index = context.dataIndex;
                return index === peakHourIndex ? '#000000' : '#FFD100';
            },
            borderColor: '#E6BC00',
            borderWidth: 1,
            borderRadius: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    color: '#666666'
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        }
    }
});
```

## Doughnut Chart (Distribution)

```javascript
new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: sourceLabels,
        datasets: [{
            data: sourceData,
            backgroundColor: chartPalette,
            borderColor: '#FFFFFF',
            borderWidth: 2,
            hoverOffset: 10
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    padding: 15,
                    usePointStyle: true,
                    pointStyle: 'circle',
                    color: '#333333',
                    font: {
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: '#000000',
                titleColor: '#FFD100',
                bodyColor: '#FFFFFF'
            }
        }
    }
});
```

## Stacked Area Chart (Trends)

```javascript
new Chart(ctx, {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [
            {
                label: 'Category 1',
                data: cat1Data,
                borderColor: '#FFD100',
                backgroundColor: 'rgba(255, 209, 0, 0.6)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Category 2',
                data: cat2Data,
                borderColor: '#000000',
                backgroundColor: 'rgba(0, 0, 0, 0.4)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Category 3',
                data: cat3Data,
                borderColor: '#666666',
                backgroundColor: 'rgba(102, 102, 102, 0.3)',
                fill: true,
                tension: 0.4
            }
        ]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 20,
                    usePointStyle: true
                }
            }
        },
        scales: {
            x: {
                grid: { display: false }
            },
            y: {
                stacked: true,
                beginAtZero: true
            }
        }
    }
});
```

## Radar Chart (Multi-dimension)

```javascript
new Chart(ctx, {
    type: 'radar',
    data: {
        labels: dimensionLabels,
        datasets: [{
            label: 'Score',
            data: dimensionData,
            backgroundColor: 'rgba(255, 209, 0, 0.3)',
            borderColor: '#FFD100',
            borderWidth: 2,
            pointBackgroundColor: '#000000',
            pointBorderColor: '#FFD100',
            pointRadius: 4
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false }
        },
        scales: {
            r: {
                beginAtZero: true,
                angleLines: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                pointLabels: {
                    color: '#333333',
                    font: {
                        size: 12,
                        weight: 500
                    }
                }
            }
        }
    }
});
```

## Chart Container CSS

```css
.chart-container {
    position: relative;
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.chart-container h3 {
    color: #000000;
    font-size: 1.1rem;
    margin-bottom: 15px;
    border-bottom: 3px solid #FFD100;
    padding-bottom: 8px;
}

.chart-wrapper {
    height: 300px;
}

@media (max-width: 768px) {
    .chart-wrapper {
        height: 250px;
    }
}
```
