/**
 * Dashboard JavaScript for Posture Monitoring System
 * Handles real-time updates, API calls, and chart rendering
 */

// Configuration
const API_BASE_URL = window.location.origin;
const UPDATE_INTERVAL = 5000; // 5 seconds
const STATS_UPDATE_INTERVAL = 5000; // 5 seconds (sync with current status)

// Global variables
let postureChart = null;
let updateTimer = null;
let statsTimer = null;

// Posture label formatting (convert snake_case to Title Case)
function formatPostureLabel(label) {
    return label
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function () {
    console.log('Dashboard initializing...');

    // Initialize components
    initVideoStream();
    loadConfig();
    updateStats();
    updateCurrentStatus();  // Add current status update
    checkSystemHealth();

    // Setup event listeners
    setupEventListeners();

    // Start periodic updates
    statsTimer = setInterval(updateStats, STATS_UPDATE_INTERVAL);
    updateTimer = setInterval(updateCurrentStatus, UPDATE_INTERVAL);  // Update current status every 5s

    console.log('Dashboard initialized successfully');
});

/**
 * Initialize video stream
 */
function initVideoStream() {
    const videoElement = document.getElementById('videoStream');
    const videoOverlay = document.getElementById('videoOverlay');

    // Check camera status first
    fetch(`${API_BASE_URL}/api/camera/status`)
        .then(response => response.json())
        .then(status => {
            if (!status.is_available) {
                videoOverlay.innerHTML = '<p>📷 Camera Not Available<br><small>Sensor Only Mode Active</small></p>';
                updateCameraStatus(false);
                return;
            }

            // Camera available - hide overlay after short delay
            // (MJPEG stream doesn't trigger onload event)
            setTimeout(() => {
                videoOverlay.style.display = 'none';
                updateCameraStatus(true);
            }, 2000);

            // Also set error handler
            videoElement.onerror = function () {
                videoOverlay.innerHTML = '<p>❌ Cannot Connect Camera<br><small>Sensor Only Mode Active</small></p>';
                videoOverlay.style.display = 'flex';
                updateCameraStatus(false);
            };
        })
        .catch(error => {
            console.error('Failed to check camera status:', error);
            videoOverlay.innerHTML = '<p>⚠️ Cannot Check Camera<br><small>Sensor Only Mode Active</small></p>';
            updateCameraStatus(false);
        });
}

/**
 * Update camera status indicator
 */
function updateCameraStatus(isOnline) {
    const statusElement = document.getElementById('cameraStatus');
    if (isOnline) {
        statusElement.innerHTML = '<span style="color: #10b981;">Online</span>';
    } else {
        statusElement.innerHTML = '<span style="color: #ef4444;">Offline</span>';
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Save config button
    document.getElementById('saveConfigBtn').addEventListener('click', saveConfig);

    // Mode selection change
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', function () {
            console.log('Mode changed to:', this.value);
        });
    });
}

/**
 * Load configuration from server
 */
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/config`);

        if (!response.ok) {
            throw new Error('Failed to load config');
        }

        const config = await response.json();
        console.log('Config loaded:', config);

        // Set mode radio button
        const modeRadio = document.querySelector(`input[name="mode"][value="${config.mode}"]`);
        if (modeRadio) {
            modeRadio.checked = true;
        }

    } catch (error) {
        console.error('Error loading config:', error);
        showNotification('Cannot load configuration', 'error');
    }
}

/**
 * Save configuration to server
 */
async function saveConfig() {
    const saveBtn = document.getElementById('saveConfigBtn');
    const originalText = saveBtn.textContent;

    try {
        // Get selected mode
        const selectedMode = document.querySelector('input[name="mode"]:checked').value;

        // Show loading state
        saveBtn.textContent = '⏳ Saving...';
        saveBtn.disabled = true;

        const response = await fetch(`${API_BASE_URL}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode: selectedMode,
                auto_threshold: 0.70,
                fusion_weights: {
                    sensor: 0.4,
                    camera: 0.6
                }
            })
        });

        if (!response.ok) {
            throw new Error('Failed to save config');
        }

        const result = await response.json();
        console.log('Config saved:', result);

        showNotification('✅ Configuration Saved', 'success');

    } catch (error) {
        console.error('Error saving config:', error);
        showNotification('❌ Cannot Save Configuration', 'error');
    } finally {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
    }
}

/**
 * Update current status from latest posture log
 */
async function updateCurrentStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/latest`);

        if (!response.ok) {
            return;  // No data yet
        }

        const latest = await response.json();

        // Update posture label
        const postureElement = document.getElementById('currentPosture');
        postureElement.textContent = formatPostureLabel(latest.posture);

        // Update confidence
        const confidenceElement = document.getElementById('currentConfidence');
        confidenceElement.textContent = `${Math.round(latest.confidence * 100)}%`;

        // Update last update time
        const lastUpdateElement = document.getElementById('lastUpdate');
        // Add 'Z' to mark as UTC if not present, then convert to local time
        const timestampStr = latest.timestamp.endsWith('Z') ? latest.timestamp : latest.timestamp + 'Z';
        const timestamp = new Date(timestampStr);
        lastUpdateElement.textContent = timestamp.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });

        // Show/hide warning
        const alertSection = document.getElementById('alertsSection');
        if (latest.warning) {
            alertSection.style.display = 'block';
        } else {
            alertSection.style.display = 'none';
        }

    } catch (error) {
        console.error('Error updating current status:', error);
    }
}

/**
 * Update statistics from server
 */
async function updateStats() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/api/stats?date=${today}`);

        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }

        const stats = await response.json();
        console.log('Stats updated:', stats);

        // Update stat values
        document.getElementById('totalDetections').textContent = stats.total_detections || 0;
        document.getElementById('correctPercentage').textContent = `${stats.correct_percentage || 0}%`;
        document.getElementById('totalWarnings').textContent = stats.total_warnings || 0;
        document.getElementById('badPostureCount').textContent = stats.bad_posture_count || 0;

        // Update chart
        updatePostureChart(stats.posture_distribution || {});

    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

/**
 * Update posture distribution chart
 */
function updatePostureChart(distribution) {
    const ctx = document.getElementById('postureChart');

    if (!ctx) return;

    // Prepare data - use formatPostureLabel for display
    const labels = Object.keys(distribution).map(key => formatPostureLabel(key));
    const data = Object.values(distribution);

    // Destroy existing chart
    if (postureChart) {
        postureChart.destroy();
    }

    // Create new chart
    postureChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#10b981', // Correct - Green
                    '#ef4444', // Backward - Red
                    '#f59e0b', // Forward - Orange
                    '#8b5cf6', // Left - Purple
                    '#ec4899', // Right - Pink
                    '#06b6d4', // Left leg - Cyan
                    '#3b82f6', // Right leg - Blue
                    '#f97316', // Front edge - Orange
                    '#dc2626'  // Hunched - Dark red
                ],
                borderWidth: 2,
                borderColor: '#1e293b'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#cbd5e1',
                        padding: 15,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true
                }
            }
        }
    });
}

/**
 * Check system health
 */
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);

        if (!response.ok) {
            throw new Error('Health check failed');
        }

        const health = await response.json();
        console.log('System health:', health);

        // Update status indicator
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');

        if (health.status === 'ok') {
            statusDot.style.background = '#10b981';
            statusText.textContent = 'System Online';
        } else if (health.status === 'degraded') {
            statusDot.style.background = '#f59e0b';
            statusText.textContent = 'System Degraded';
        } else {
            statusDot.style.background = '#ef4444';
            statusText.textContent = 'System Error';
        }

    } catch (error) {
        console.error('Health check error:', error);
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        statusDot.style.background = '#ef4444';
        statusText.textContent = 'Cannot Connect';
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Simple notification (can be enhanced with a library)
    const alertSection = document.getElementById('alertsSection');
    const alertMessage = document.getElementById('alertMessage');

    if (type === 'error') {
        alertSection.style.display = 'block';
        alertMessage.textContent = message;
        alertMessage.style.color = '#ef4444';
    } else if (type === 'success') {
        alertSection.style.display = 'block';
        alertMessage.textContent = message;
        alertMessage.style.color = '#10b981';

        // Hide after 3 seconds
        setTimeout(() => {
            alertSection.style.display = 'none';
        }, 3000);
    }
}

/**
 * Format timestamp
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('vi-VN');
}

// Cleanup on page unload
window.addEventListener('beforeunload', function () {
    if (updateTimer) clearInterval(updateTimer);
    if (statsTimer) clearInterval(statsTimer);
    if (postureChart) postureChart.destroy();
});

// ==================== BATTERY MONITORING ====================

let batteryUpdateInterval = null;

function startBatteryMonitoring() {
    updateBatteryStatus();
    batteryUpdateInterval = setInterval(updateBatteryStatus, 5000); // Update every 5s
}

function stopBatteryMonitoring() {
    if (batteryUpdateInterval) {
        clearInterval(batteryUpdateInterval);
        batteryUpdateInterval = null;
    }
}

async function updateBatteryStatus() {
    try {
        const response = await fetch('/api/battery/latest');
        const result = await response.json();

        if (result.success && result.data) {
            const data = result.data;

            // Update voltage
            document.getElementById('batteryVoltage').textContent = data.voltage + 'V';

            // Update percentage
            const percentage = parseFloat(data.percentage);
            document.getElementById('batteryPercentage').textContent = Math.round(percentage) + '%';
            document.getElementById('batteryLevel').style.width = percentage + '%';

            // Update status
            const statusEl = document.getElementById('batteryStatus');
            statusEl.textContent = data.status === 'charging' ? '⚡ Charging' : '🔌 Not Charging';
            statusEl.className = 'value ' + (data.status === 'charging' ? 'charging' : '');

            // Update level badge
            const badgeEl = document.getElementById('batteryLevelBadge');
            badgeEl.textContent = data.level.charAt(0).toUpperCase() + data.level.slice(1);
            badgeEl.className = 'badge badge-' + data.level;

            // Update battery level color
            const levelEl = document.getElementById('batteryLevel');
            if (percentage > 75) {
                levelEl.style.background = '#10b981'; // Green
            } else if (percentage > 50) {
                levelEl.style.background = '#3b82f6'; // Blue
            } else if (percentage > 25) {
                levelEl.style.background = '#f59e0b'; // Orange
            } else {
                levelEl.style.background = '#ef4444'; // Red
            }

            // Update last update time
            const updateTime = new Date(data.timestamp).toLocaleTimeString('vi-VN');
            document.getElementById('batteryLastUpdate').textContent = updateTime;
        }
    } catch (error) {
        console.error('Error updating battery status:', error);
    }
}

// Start monitoring when page loads
document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('batteryIcon')) {
        startBatteryMonitoring();
    }
});

// Stop monitoring when leaving page
window.addEventListener('beforeunload', function () {
    stopBatteryMonitoring();
});
