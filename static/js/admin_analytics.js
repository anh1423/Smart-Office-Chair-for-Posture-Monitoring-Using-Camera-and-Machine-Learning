/**
 * Advanced Analytics Dashboard JavaScript
 * Admin-only analytics with historical data, charts, and export
 */

const API_BASE_URL = window.location.origin;

// Global state
let currentPeriod = 'day';
let currentStartDate = null;
let currentEndDate = null;
let charts = {};
let autoRefreshInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    setupEventListeners();
    loadData('day');
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Time period buttons
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            const period = this.dataset.period;

            if (period === 'custom') {
                document.getElementById('customRange').style.display = 'flex';
            } else {
                document.getElementById('customRange').style.display = 'none';
                loadData(period);
            }
        });
    });

    // Custom range apply
    document.getElementById('applyCustom').addEventListener('click', applyCustomRange);

    // Export button
    document.getElementById('exportBtn').addEventListener('click', openExportModal);
    document.getElementById('closeExportModal').addEventListener('click', closeExportModal);
    document.getElementById('cancelExport').addEventListener('click', closeExportModal);
    document.getElementById('confirmExport').addEventListener('click', confirmExport);
}

/**
 * Load data for specified period
 */
async function loadData(period) {
    currentPeriod = period;

    try {
        // Load statistics
        const statsResponse = await fetch(`${API_BASE_URL}/api/admin/stats/${period}`);
        const statsData = await statsResponse.json();

        if (statsData.success) {
            updateStatistics(statsData.stats);
            currentStartDate = statsData.start_date;
            currentEndDate = statsData.end_date;
        }

        // Load trend data
        const trendResponse = await fetch(`${API_BASE_URL}/api/admin/trend/${period}`);
        const trendData = await trendResponse.json();

        if (trendData.success) {
            updateDailyTrendChart(trendData.trend);
        }

        // Load warning frequency
        const warningsResponse = await fetch(`${API_BASE_URL}/api/admin/warnings/${period}`);
        const warningsData = await warningsResponse.json();

        if (warningsData.success) {
            updateWarningFreqChart(warningsData.frequency);
        }

        // Load sensor history
        await loadSensorHistory(period);

    } catch (error) {
        console.error('Error loading data:', error);
        alert('Failed to load analytics data');
    }

    // Setup auto-refresh for 'day' period only
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }

    if (period === 'day') {
        autoRefreshInterval = setInterval(() => {
            loadData('day');
        }, 10000); // Refresh every 10 seconds
    }
}

/**
 * Apply custom date range
 */
async function applyCustomRange() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    if (!startDate || !endDate) {
        alert('Please select both start and end dates');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/stats/custom`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_date: startDate, end_date: endDate })
        });

        const data = await response.json();

        if (data.success) {
            updateStatistics(data.stats);
            currentStartDate = data.start_date;
            currentEndDate = data.end_date;
            currentPeriod = 'custom';
        }
    } catch (error) {
        console.error('Error loading custom range:', error);
        alert('Failed to load data for custom range');
    }
}

/**
 * Update statistics cards
 */
function updateStatistics(stats) {
    document.getElementById('totalDetections').textContent = stats.total_detections || 0;
    document.getElementById('correctRate').textContent = `${stats.correct_percentage || 0}%`;
    document.getElementById('totalWarnings').textContent = stats.total_warnings || 0;
    document.getElementById('badPostures').textContent = stats.bad_posture_count || 0;

    // Update posture distribution chart
    updatePostureDistChart(stats.posture_distribution || {});

    // Update mode distribution chart
    updateModeDistChart(stats.mode_distribution || {});
}

/**
 * Update posture distribution chart
 */
function updatePostureDistChart(distribution) {
    const ctx = document.getElementById('postureDistChart');

    if (charts.postureDist) {
        charts.postureDist.destroy();
    }

    const labels = Object.keys(distribution).map(formatPostureLabel);
    const data = Object.values(distribution);

    charts.postureDist = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#10b981', '#ef4444', '#f59e0b', '#8b5cf6',
                    '#ec4899', '#06b6d4', '#3b82f6', '#f97316'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#cbd5e1' } }
            }
        }
    });
}

/**
 * Update daily trend chart
 */
function updateDailyTrendChart(trend) {
    const ctx = document.getElementById('dailyTrendChart');

    if (charts.dailyTrend) {
        charts.dailyTrend.destroy();
    }

    const labels = trend.map(d => d.date);
    const correctData = trend.map(d => d.correct);
    const badData = trend.map(d => d.bad);

    charts.dailyTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Correct Posture',
                    data: correctData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Bad Posture',
                    data: badData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#cbd5e1' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' } },
                y: { ticks: { color: '#94a3b8' } }
            }
        }
    });
}

/**
 * Update warning frequency chart
 */
function updateWarningFreqChart(frequency) {
    const ctx = document.getElementById('warningFreqChart');

    if (charts.warningFreq) {
        charts.warningFreq.destroy();
    }

    const labels = Object.keys(frequency);
    const data = Object.values(frequency);

    charts.warningFreq = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Warnings',
                data: data,
                backgroundColor: '#f59e0b'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#cbd5e1' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' } },
                y: { ticks: { color: '#94a3b8' } }
            }
        }
    });
}

/**
 * Update mode distribution chart
 */
function updateModeDistChart(distribution) {
    const ctx = document.getElementById('modeDistChart');

    if (charts.modeDist) {
        charts.modeDist.destroy();
    }

    const labels = Object.keys(distribution);
    const data = Object.values(distribution);

    charts.modeDist = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1' } } }
        }
    });
}

/**
 * Open export modal
 */
function openExportModal() {
    const start = new Date(currentStartDate).toLocaleDateString();
    const end = new Date(currentEndDate).toLocaleDateString();
    document.getElementById('exportRange').textContent = `${start} - ${end}`;
    document.getElementById('exportModal').classList.add('show');
}

/**
 * Close export modal
 */
function closeExportModal() {
    document.getElementById('exportModal').classList.remove('show');
}

/**
 * Confirm export
 */
async function confirmExport() {
    const format = document.getElementById('exportFormat').value;

    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                format: format,
                start_date: currentStartDate.split('T')[0],
                end_date: currentEndDate.split('T')[0]
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `posture_data.${format === 'excel' ? 'xlsx' : 'csv'}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            closeExportModal();
            alert('✅ Data exported successfully!');
        } else {
            alert('❌ Failed to export data');
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('❌ Export failed');
    }
}

/**
 * Format posture label
 */
function formatPostureLabel(label) {
    return label.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}


// ==================== AI Model Performance Functions ====================

/**
 * Load AI performance data
 */
async function loadAIPerformance(period) {
    try {
        // Load camera activation stats
        const activationResponse = await fetch(`${API_BASE_URL}/api/admin/ai-performance/camera-activation/${period}`);
        const activationData = await activationResponse.json();

        if (activationData.success) {
            updateCameraActivationStats(activationData.stats);
        }

        // Load confidence comparison
        const confidenceResponse = await fetch(`${API_BASE_URL}/api/admin/ai-performance/confidence-comparison/${period}`);
        const confidenceData = await confidenceResponse.json();

        if (confidenceData.success) {
            updateConfidenceComparison(confidenceData.comparison);
        }

        // Load fusion conflicts
        const conflictsResponse = await fetch(`${API_BASE_URL}/api/admin/ai-performance/fusion-conflicts/${period}`);
        const conflictsData = await conflictsResponse.json();

        if (conflictsData.success) {
            updateFusionLog(conflictsData.conflicts);
        }

    } catch (error) {
        console.error('Error loading AI performance data:', error);
    }
}

/**
 * Update camera activation statistics
 */
function updateCameraActivationStats(stats) {
    document.getElementById('sensorOnlyCount').textContent = stats.sensor_only || 0;
    document.getElementById('sensorOnlyPercent').textContent = `${stats.sensor_percentage || 0}%`;
    document.getElementById('cameraActivatedCount').textContent = stats.camera_activated || 0;
    document.getElementById('cameraActivatedPercent').textContent = `${stats.camera_percentage || 0}%`;

    // Update chart
    const ctx = document.getElementById('cameraActivationChart');

    if (charts.cameraActivation) {
        charts.cameraActivation.destroy();
    }

    charts.cameraActivation = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Sensor Only', 'Camera Activated'],
            datasets: [{
                label: 'Detections',
                data: [stats.sensor_only, stats.camera_activated],
                backgroundColor: ['#10b981', '#f59e0b']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#94a3b8' } },
                y: { ticks: { color: '#94a3b8' } }
            }
        }
    });
}

/**
 * Update confidence comparison
 */
function updateConfidenceComparison(comparison) {
    document.getElementById('sensorAvgConf').textContent = `${comparison.sensor_avg || 0}%`;
    document.getElementById('cameraAvgConf').textContent = `${comparison.camera_avg || 0}%`;

    // Prepare data for chart
    const postures = Object.keys(comparison.by_posture || {});
    const sensorData = postures.map(p => comparison.by_posture[p].sensor_avg);
    const cameraData = postures.map(p => comparison.by_posture[p].camera_avg);
    const labels = postures.map(formatPostureLabel);

    const ctx = document.getElementById('confidenceCompChart');

    if (charts.confidenceComp) {
        charts.confidenceComp.destroy();
    }

    charts.confidenceComp = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Sensor',
                    data: sensorData,
                    backgroundColor: '#3b82f6'
                },
                {
                    label: 'Camera',
                    data: cameraData,
                    backgroundColor: '#8b5cf6'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#cbd5e1' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' } },
                y: {
                    ticks: { color: '#94a3b8' },
                    max: 100,
                    title: { display: true, text: 'Confidence (%)', color: '#cbd5e1' }
                }
            }
        }
    });
}

/**
 * Update fusion decision log table
 */
function updateFusionLog(conflicts) {
    const tbody = document.getElementById('fusionLogBody');

    if (!conflicts || conflicts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">No fusion decisions recorded</td></tr>';
        return;
    }

    tbody.innerHTML = conflicts.map(log => {
        const date = new Date(log.timestamp);
        // Convert UTC to UTC+7 (Vietnam time)
        date.setHours(date.getHours() + 7);
        const time = date.toLocaleTimeString('vi-VN');
        const sensorConf = log.sensor_confidence ? `${(log.sensor_confidence * 100).toFixed(1)}%` : '-';
        const cameraConf = log.camera_confidence ? `${(log.camera_confidence * 100).toFixed(1)}%` : '-';

        return `
            <tr>
                <td>${time}</td>
                <td class="conf-cell sensor">${sensorConf}</td>
                <td class="conf-cell camera">${cameraConf}</td>
                <td>${formatPostureLabel(log.posture)}</td>
                <td class="reason-cell">${log.fusion_reason || '-'}</td>
            </tr>
        `;
    }).join('');
}

// Update loadData function to also load AI performance
const originalLoadData = loadData;
loadData = async function (period) {
    await originalLoadData(period);
    await loadAIPerformance(period);
};

// ==================== PHASE 3: SENSOR VISUALIZATION ====================

let sensorUpdateInterval = null;

/**
 * Start real-time sensor updates
 */
function startSensorUpdates() {
    // Initial load
    updateSensorVisualization();

    // Update every 2 seconds
    if (sensorUpdateInterval) {
        clearInterval(sensorUpdateInterval);
    }

    sensorUpdateInterval = setInterval(() => {
        updateSensorVisualization();
    }, 2000);
}

/**
 * Stop sensor updates
 */
function stopSensorUpdates() {
    if (sensorUpdateInterval) {
        clearInterval(sensorUpdateInterval);
        sensorUpdateInterval = null;
    }
}

/**
 * Update all sensor visualizations
 */
async function updateSensorVisualization() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/sensor/realtime`);
        const data = await response.json();

        if (data.success && data.sensor_values) {
            updateRadarChart(data.sensor_values);
            updateHeatmap(data.sensor_values);
            updateSensorHistory(data);
        }
    } catch (error) {
        console.error('Error updating sensor visualization:', error);
    }
}

/**
 * Update radar chart
 */
function updateRadarChart(sensorValues) {
    const ctx = document.getElementById('sensorRadarChart');
    if (!ctx) return;

    if (charts.sensorRadar) {
        charts.sensorRadar.destroy();
    }

    // Extract sensor values (sensor1-sensor7)
    const values = [
        sensorValues.sensor1 || 0,
        sensorValues.sensor2 || 0,
        sensorValues.sensor3 || 0,
        sensorValues.sensor4 || 0,
        sensorValues.sensor5 || 0,
        sensorValues.sensor6 || 0,
        sensorValues.sensor7 || 0
    ];

    charts.sensorRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['S1 (Rear L)', 'S2 (Rear R)', 'S3 (Front L)', 'S4 (Front R)', 'S5 (Back)', 'S6 (Shoulder R)', 'S7 (Shoulder L)'],
            datasets: [{
                label: 'Pressure',
                data: values,
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                borderColor: '#8b5cf6',
                borderWidth: 2,
                pointBackgroundColor: '#8b5cf6',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#8b5cf6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 4200,
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' },
                    pointLabels: { color: '#cbd5e1', font: { size: 11 } }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

/**
 * Update seat heatmap
 */
function updateHeatmap(sensorValues) {
    const sensors = ['sensor1', 'sensor2', 'sensor3', 'sensor4', 'sensor5', 'sensor6', 'sensor7'];

    sensors.forEach((sensor, index) => {
        const value = sensorValues[sensor] || 0;
        const circle = document.getElementById(sensor);

        if (circle) {
            // Color mapping based on pressure (0-4095 scale)
            let color;
            if (value < 1000) {
                color = '#3b82f6'; // Blue - Low
            } else if (value < 2000) {
                color = '#10b981'; // Green - Medium
            } else if (value < 3000) {
                color = '#f59e0b'; // Orange - High
            } else {
                color = '#ef4444'; // Red - Very High
            }

            circle.setAttribute('fill', color);

            // Opacity based on value (0.3 to 1.0)
            const opacity = Math.min(1.0, 0.3 + (value / 4200) * 0.7);
            circle.setAttribute('opacity', opacity);
        }
    });
}

/**
 * Update sensor history graph
 */

window.addEventListener('beforeunload', function () {
    stopSensorUpdates();
});
// Add debug at the end of admin_analytics.js
console.log('🔍 Phase 3 Sensor Visualization code loaded!');
console.log('📊 Charts object:', charts);
console.log('🎯 Starting sensor updates in 1 second...');

// Better initialization - check if elements exist
function initSensorVisualization() {
    const radarCanvas = document.getElementById('sensorRadarChart');
    const historyCanvas = document.getElementById('sensorHistoryChart');
    const heatmap = document.getElementById('seatHeatmap');

    console.log('🔍 Checking sensor elements...');
    console.log('Radar canvas:', radarCanvas);
    console.log('History canvas:', historyCanvas);
    console.log('Heatmap SVG:', heatmap);

    if (radarCanvas && historyCanvas && heatmap) {
        console.log('✅ All sensor elements found! Starting updates...');
        startSensorUpdates();
    } else {
        console.warn('⚠️ Some sensor elements not found. Retrying in 1s...');
        setTimeout(initSensorVisualization, 1000);
    }
}

// Call init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSensorVisualization);
} else {
    // DOM already loaded
    initSensorVisualization();
}
/**
 * Load sensor history for selected period
 */
async function loadSensorHistory(period) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/sensor/history?period=${period}`);
        const data = await response.json();

        if (data.success && data.history) {
            renderSensorHistoryChart(data.history);
        }
    } catch (error) {
        console.error('Error loading sensor history:', error);
    }
}

/**
 * Render sensor history chart with historical data
 */
function renderSensorHistoryChart(history) {
    const ctx = document.getElementById('sensorHistoryChart');
    if (!ctx) return;

    if (charts.sensorHistory) {
        charts.sensorHistory.destroy();
    }

    if (!history || history.length === 0) {
        return;
    }

    const labels = history.map(h => {
        const date = new Date(h.timestamp);
        // Convert UTC to UTC+7 (Vietnam time)
        date.setHours(date.getHours() + 7);
        return date.toLocaleString('vi-VN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    });

    const colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4'];
    const datasets = [];

    for (let i = 1; i <= 7; i++) {
        const sensorKey = `sensor${i}`;
        datasets.push({
            label: `S${i}`,
            data: history.map(h => h.sensors[sensorKey] || 0),
            borderColor: colors[i - 1],
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: history.length > 50 ? 0 : 2
        });
    }

    charts.sensorHistory = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#cbd5e1', boxWidth: 12, padding: 10 }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#94a3b8', maxRotation: 45, maxTicksLimit: 20 },
                    grid: { color: '#334155' }
                },
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' },
                    beginAtZero: true,
                    max: 4200
                }
            }
        }
    });
}

// ==================== PHASE 4: SYSTEM HEALTH MONITORING ====================

let healthUpdateInterval = null;

/**
 * Start system health monitoring
 */
function startHealthMonitoring() {
    // Initial load
    updateSystemHealth();

    // Update every 5 seconds
    if (healthUpdateInterval) {
        clearInterval(healthUpdateInterval);
    }

    healthUpdateInterval = setInterval(() => {
        updateSystemHealth();
    }, 5000);
}

/**
 * Stop health monitoring
 */
function stopHealthMonitoring() {
    if (healthUpdateInterval) {
        clearInterval(healthUpdateInterval);
        healthUpdateInterval = null;
    }
}

/**
 * Update system health metrics
 */
async function updateSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/system/health`);
        const data = await response.json();

        if (data.success && data.metrics) {
            updateCPUMetrics(data.metrics.cpu);
            updateMemoryMetrics(data.metrics.memory);
            updateTemperatureMetrics(data.metrics.temperature);
            updateDiskMetrics(data.metrics.disk);
        }
    } catch (error) {
        console.error('Error updating system health:', error);
    }
}

/**
 * Update CPU metrics
 */
function updateCPUMetrics(cpu) {
    if (!cpu.available) return;

    const usage = cpu.usage;
    document.getElementById('cpuUsage').textContent = `${usage}%`;
    document.getElementById('cpuCores').textContent = `${cpu.cores} cores`;

    const bar = document.getElementById('cpuBar');
    bar.style.width = `${usage}%`;

    // Color based on usage
    if (usage < 50) {
        bar.style.background = '#10b981'; // Green
    } else if (usage < 80) {
        bar.style.background = '#f59e0b'; // Orange
    } else {
        bar.style.background = '#ef4444'; // Red
    }
}

/**
 * Update memory metrics
 */
function updateMemoryMetrics(memory) {
    if (!memory.available) return;

    const percent = memory.percent;
    document.getElementById('ramUsage').textContent = `${percent}%`;
    document.getElementById('ramInfo').textContent = `${memory.used_gb} GB / ${memory.total_gb} GB`;

    const bar = document.getElementById('ramBar');
    bar.style.width = `${percent}%`;

    // Color based on usage
    if (percent < 70) {
        bar.style.background = '#10b981'; // Green
    } else if (percent < 85) {
        bar.style.background = '#f59e0b'; // Orange
    } else {
        bar.style.background = '#ef4444'; // Red
    }
}

/**
 * Update temperature metrics
 */
function updateTemperatureMetrics(temp) {
    if (!temp.available) return;

    const temperature = temp.temp;
    document.getElementById('cpuTemp').textContent = `${temperature}°C`;

    const bar = document.getElementById('tempBar');
    const maxTemp = temp.critical || 100;
    const percent = Math.min((temperature / maxTemp) * 100, 100);
    bar.style.width = `${percent}%`;

    // Status and color
    let status, color;
    if (temperature < 60) {
        status = 'Normal';
        color = '#10b981'; // Green
    } else if (temperature < 70) {
        status = 'Warm';
        color = '#f59e0b'; // Orange
    } else if (temperature < 80) {
        status = 'Hot';
        color = '#ef4444'; // Red
    } else {
        status = 'Critical!';
        color = '#dc2626'; // Dark Red
    }

    document.getElementById('tempInfo').textContent = status;
    bar.style.background = color;
}

/**
 * Update disk metrics
 */
function updateDiskMetrics(disk) {
    if (!disk.available) return;

    const percent = disk.percent;
    document.getElementById('diskUsage').textContent = `${percent}%`;
    document.getElementById('diskInfo').textContent = `${disk.used_gb} GB / ${disk.total_gb} GB`;

    const bar = document.getElementById('diskBar');
    bar.style.width = `${percent}%`;

    // Color based on usage
    if (percent < 70) {
        bar.style.background = '#8b5cf6'; // Purple
    } else if (percent < 85) {
        bar.style.background = '#f59e0b'; // Orange
    } else {
        bar.style.background = '#ef4444'; // Red
    }
}

// Start health monitoring when page loads
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(() => {
        startHealthMonitoring();
    }, 2000);
});

// Stop monitoring when leaving page
window.addEventListener('beforeunload', function () {
    stopHealthMonitoring();
});

// ==================== PHASE 5: DATA MANAGEMENT ====================

let currentCleanupAction = null;

/**
 * Load database statistics
 */
async function loadDatabaseStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/database/stats`);
        const data = await response.json();

        if (data.success && data.stats) {
            updateDatabaseStats(data.stats);
            displayCleanupSuggestions(data.suggestions || []);
        }
    } catch (error) {
        console.error('Error loading database stats:', error);
    }
}

/**
 * Update database statistics display
 */
function updateDatabaseStats(stats) {
    document.getElementById('dbTotalLogs').textContent = stats.total_logs || 0;
    document.getElementById('dbOldLogs').textContent = stats.old_logs_30d || 0;
    document.getElementById('dbDaysOfData').textContent = stats.days_of_data || 0;
}

/**
 * Display cleanup suggestions
 */
function displayCleanupSuggestions(suggestions) {
    const container = document.getElementById('cleanupSuggestions');

    if (!suggestions || suggestions.length === 0) {
        container.innerHTML = '';
        return;
    }

    const html = suggestions.map(s => `
        <div class="suggestion-card ${s.type}">
            <div class="suggestion-icon">${s.type === 'danger' ? '⚠️' : 'ℹ️'}</div>
            <div class="suggestion-content">
                <div class="suggestion-message">${s.message}</div>
                <button class="btn-sm" onclick="confirmCleanup('${s.action}', ${s.days})">Clean Up Now</button>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

/**
 * Show cleanup confirmation modal
 */
function confirmCleanup(action, days) {
    currentCleanupAction = { action, days: days || parseInt(document.getElementById('daysToKeep').value) };

    const messages = {
        'clear_all': 'Are you sure you want to delete ALL posture logs? This will permanently remove all historical data.',
        'clear_old': `Are you sure you want to delete logs older than ${currentCleanupAction.days} days?`,
        'clear_stats': 'Are you sure you want to delete all daily statistics? Charts will be empty until new data is collected.'
    };

    document.getElementById('cleanupMessage').textContent = messages[action] || 'Are you sure?';
    document.getElementById('confirmCleanup').checked = false;
    document.getElementById('confirmCleanupBtn').disabled = true;
    document.getElementById('cleanupModal').style.display = 'flex';
}

/**
 * Close cleanup modal
 */
function closeCleanupModal() {
    document.getElementById('cleanupModal').style.display = 'none';
    currentCleanupAction = null;
}

/**
 * Enable/disable confirm button based on checkbox
 */
document.addEventListener('DOMContentLoaded', function () {
    const checkbox = document.getElementById('confirmCleanup');
    const confirmBtn = document.getElementById('confirmCleanupBtn');

    if (checkbox && confirmBtn) {
        checkbox.addEventListener('change', function () {
            confirmBtn.disabled = !this.checked;
        });
    }

    // Load database stats on page load
    setTimeout(() => {
        loadDatabaseStats();
    }, 2000);
});

/**
 * Execute cleanup action
 */
async function executeCleanup() {
    if (!currentCleanupAction) return;

    const confirmBtn = document.getElementById('confirmCleanupBtn');
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Deleting...';

    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                confirm: true,
                action: currentCleanupAction.action,
                days: currentCleanupAction.days
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Success! Deleted ${data.deleted} records.`);
            closeCleanupModal();
            loadDatabaseStats();
            loadData(currentPeriod); // Reload analytics data
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Error executing cleanup:', error);
        alert('Failed to execute cleanup');
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirm Delete';
    }
}

// ==================== BATTERY MONITORING ====================

/**
 * Update battery metrics
 */
async function updateBatteryStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/battery/latest`);
        const result = await response.json();

        if (result.success && result.data) {
            const battery = result.data;

            // Update display
            document.getElementById('batteryPercentage').textContent = `${Math.round(battery.percentage)}%`;
            document.getElementById('batteryVoltage').textContent = `${battery.voltage}V`;

            // Update level badge
            const levelBadge = document.getElementById('batteryLevelBadge');
            if (levelBadge) {
                levelBadge.textContent = battery.level.charAt(0).toUpperCase() + battery.level.slice(1);
                levelBadge.className = 'badge badge-' + battery.level;
            }

            // Update progress bar
            const bar = document.getElementById('batteryBar');
            if (bar) {
                const pct = parseFloat(battery.percentage);
                bar.style.width = `${pct}%`;

                // Color based on percentage
                if (pct > 75) {
                    bar.style.background = '#10b981'; // Green
                } else if (pct > 50) {
                    bar.style.background = '#3b82f6'; // Blue
                } else if (pct > 25) {
                    bar.style.background = '#f59e0b'; // Orange
                } else {
                    bar.style.background = '#ef4444'; // Red
                }
            }

            // Update last update time
            const updateTime = new Date(battery.timestamp).toLocaleTimeString('vi-VN');
            const lastUpdateEl = document.getElementById('batteryLastUpdate');
            if (lastUpdateEl) {
                lastUpdateEl.textContent = updateTime;
            }
        }
    } catch (error) {
        console.error('Error updating battery status:', error);
    }
}

// Add battery update to system health monitoring
const originalUpdateSystemHealth = updateSystemHealth;
updateSystemHealth = async function () {
    await originalUpdateSystemHealth();
    await updateBatteryStatus();
};

// Auto-load "Today" period on page load
document.addEventListener('DOMContentLoaded', function () {
    // Wait a bit for page to fully load
    setTimeout(() => {
        // Auto-select "Today" and load data
        loadData('day');
    }, 1000);
});
