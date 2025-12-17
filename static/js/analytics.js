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
    console.log('Analytics initializing...');

    // Initialize components (NO camera on analytics page)
    loadConfig();
    updateStats();
    updateCurrentStatus();  // Add current status update

    // Setup event listeners
    setupEventListeners();

    // Start periodic updates
    statsTimer = setInterval(updateStats, STATS_UPDATE_INTERVAL);
    updateTimer = setInterval(updateCurrentStatus, UPDATE_INTERVAL);  // Update current status every 5s

    console.log('Analytics initialized successfully');
});



/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Save config button (only exists for admin)
    const saveBtn = document.getElementById('saveConfigBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveConfig);
    }

    // Mode selection change (only exists for admin)
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    if (modeRadios.length > 0) {
        modeRadios.forEach(radio => {
            radio.addEventListener('change', function () {
                console.log('Mode changed to:', this.value);
            });
        });
    }
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

        // Set mode radio button (only for admin)
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
    if (!saveBtn) return; // Not admin, no save button

    const originalText = saveBtn.textContent;

    try {
        // Get selected mode
        const selectedModeElement = document.querySelector('input[name="mode"]:checked');
        if (!selectedModeElement) return; // No mode selected

        const selectedMode = selectedModeElement.value;

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

        // Update stat values (match analytics.html element IDs)
        document.getElementById('totalDetections').textContent = stats.total_detections || 0;
        document.getElementById('correctRate').textContent = `${stats.correct_percentage || 0}%`;
        document.getElementById('totalWarnings').textContent = stats.total_warnings || 0;
        document.getElementById('badPostures').textContent = stats.bad_posture_count || 0;

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
