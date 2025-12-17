const API_BASE_URL = "";

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

    // Also update battery status
    await updateBatteryStatus();
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

console.log('Adding battery monitoring...');

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
            const bar = document.getElementById('batteryLevel');
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

console.log('✓ Battery monitoring functions defined');
