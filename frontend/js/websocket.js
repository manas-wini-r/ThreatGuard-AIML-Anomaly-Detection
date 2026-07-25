// ============================================================
// WEBSOCKET - Real-time Updates
// ============================================================

const WS_URL = 'ws://localhost:8000/ws';
let ws = null;
let reconnectTimer = null;

function connectWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = function() {
            console.log('✅ WebSocket connected');
            updateConnectionStatus(true);
        };
        
        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                if (data.status === 'anomaly' || data.type === 'alert') {
                    const alert = data.data || data;
                    addAlertToFeed(alert);
                    updateStats(alert);
                }
            } catch (e) {
                console.error('WebSocket parse error:', e);
            }
        };
        
        ws.onclose = function() {
            console.log('❌ WebSocket disconnected');
            updateConnectionStatus(false);
            clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connectWebSocket, 3000);
        };
        
        ws.onerror = function() {
            console.log('⚠️ WebSocket error');
        };
    } catch (e) {
        console.error('WebSocket error:', e);
        setTimeout(connectWebSocket, 3000);
    }
}

function updateConnectionStatus(connected) {
    const badge = document.querySelector('.live-badge');
    if (!badge) return;
    if (connected) {
        badge.style.color = '#10b981';
        badge.textContent = '● LIVE';
    } else {
        badge.style.color = '#ef4444';
        badge.textContent = '● OFFLINE';
    }
}

function addAlertToFeed(alert) {
    const container = document.getElementById('liveFeed');
    if (!container) return;
    
    // Remove empty state
    if (container.querySelector('.empty-state')) container.innerHTML = '';
    
    const div = document.createElement('div');
    div.className = `feed-item ${alert.severity || 'low'}`;
    div.innerHTML = `
        <span class="time">${formatTime(alert.timestamp)}</span>
        <span class="msg">${alert.explanation || 'Anomaly detected!'}</span>
        <span class="tag">${formatType(alert.threat_type)}</span>
    `;
    container.insertBefore(div, container.firstChild);
    
    // Keep only last 20 items
    while (container.children.length > 20) {
        container.removeChild(container.lastChild);
    }
}

function updateStats(alert) {
    const anomalies = document.getElementById('anomalies');
    const alerts = document.getElementById('activeAlerts');
    const count = document.getElementById('alertCount');
    
    if (anomalies) {
        const val = parseInt(anomalies.textContent.replace(/,/g, '')) || 0;
        anomalies.textContent = val + 1;
    }
    if (alerts) {
        const val = parseInt(alerts.textContent.replace(/,/g, '')) || 0;
        alerts.textContent = val + 1;
    }
    if (count) {
        const val = parseInt(count.textContent) || 0;
        count.textContent = val + 1;
    }
}

// ===== START =====
connectWebSocket();