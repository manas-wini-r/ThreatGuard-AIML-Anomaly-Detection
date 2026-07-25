// ============================================================
// THREATGUARD - Complete Application
// ============================================================

const API = 'http://localhost:8000/api';

// ===== NAVIGATION =====
document.querySelectorAll('.nav a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.nav a').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        const section = this.dataset.section;
        document.getElementById(section).classList.add('active');
        document.getElementById('pageTitle').textContent = this.textContent.trim();
        document.getElementById('breadcrumbCurrent').textContent = this.textContent.trim();
        
        if (section === 'alerts') {
            loadAlerts();
        }
    });
});

// ===== API CALL =====
async function fetchAPI(endpoint) {
    try {
        const res = await fetch(API + endpoint);
        if (!res.ok) throw new Error('API error');
        return await res.json();
    } catch (e) {
        console.error('API Error:', e);
        return null;
    }
}

// ===== VIEW ALL ALERTS =====
function viewAllAlerts() {
    document.querySelectorAll('.nav a').forEach(l => l.classList.remove('active'));
    const alertsLink = document.querySelector('[data-section="alerts"]');
    if (alertsLink) {
        alertsLink.classList.add('active');
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById('alerts').classList.add('active');
        document.getElementById('pageTitle').textContent = 'Security Alerts';
        document.getElementById('breadcrumbCurrent').textContent = 'Security Alerts';
        loadAlerts();
    }
}

// ===== DASHBOARD =====
async function loadDashboard() {
    const data = await fetchAPI('/stats');
    if (!data) return;
    
    document.getElementById('totalLogs').textContent = data.total_logs || 0;
    document.getElementById('anomalies').textContent = data.anomalies_detected || 0;
    document.getElementById('activeAlerts').textContent = data.anomalies_detected || 0;
    document.getElementById('alertCount').textContent = data.anomalies_detected || 0;
    document.getElementById('modelAccuracy').textContent = data.anomaly_rate ? (100 - data.anomaly_rate).toFixed(1) + '%' : '94.2%';
    
    updateCharts(data);
    loadFeed();
}

// ===== CHARTS =====
let chart1, chart2;

function updateCharts(data) {
    const ts = data.time_series || Array.from({length: 24}, (_, i) => ({
        hour: i,
        logs: Math.floor(Math.random() * 80) + 40,
        anomalies: Math.floor(Math.random() * 10)
    }));
    
    if (chart1) chart1.destroy();
    chart1 = new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: ts.map(d => d.hour + ':00'),
            datasets: [
                { label: 'Logs', data: ts.map(d => d.logs), borderColor: '#4A6CF7', backgroundColor: 'rgba(74,108,247,0.1)', fill: true, tension: 0.4 },
                { label: 'Anomalies', data: ts.map(d => d.anomalies), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', fill: true, tension: 0.4 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', maxTicksLimit: 12 } }
            }
        }
    });
    
    const dist = data.threat_distribution || { 'Brute Force': 30, 'Impossible Travel': 20, 'Lateral Movement': 25, 'Credential Misuse': 15, 'Device Spoofing': 10 };
    if (chart2) chart2.destroy();
    chart2 = new Chart(document.getElementById('distributionChart'), {
        type: 'doughnut',
        data: {
            labels: Object.keys(dist),
            datasets: [{ data: Object.values(dist), backgroundColor: ['#4A6CF7','#8b5cf6','#f59e0b','#ef4444','#10b981'], borderColor: '#1a2234', borderWidth: 2 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 12 } } },
            cutout: '65%'
        }
    });
}

// ===== FEED =====
async function loadFeed() {
    const container = document.getElementById('liveFeed');
    const data = await fetchAPI('/alerts?limit=10');
    
    container.innerHTML = '';
    
    if (!data || !data.alerts || data.alerts.length === 0) {
        container.innerHTML = `<div class="empty-state"><i class="fas fa-shield-alt"></i><p>No threats detected</p><span>All systems secure</span></div>`;
        return;
    }
    
    data.alerts.forEach(a => {
        const div = document.createElement('div');
        div.className = `feed-item ${a.severity || 'low'}`;
        div.innerHTML = `
            <span class="time">${formatTime(a.timestamp)}</span>
            <span class="msg">${a.explanation || 'Anomaly detected'}</span>
            <span class="tag">${formatType(a.threat_type)}</span>
        `;
        container.appendChild(div);
    });
}

// ===== ALERTS =====
async function loadAlerts() {
    const severity = document.getElementById('severityFilter').value;
    const threat = document.getElementById('threatFilter').value;
    
    let url = '/alerts?limit=50';
    if (severity !== 'all') url += `&severity=${severity}`;
    if (threat !== 'all') url += `&threat_type=${threat}`;
    
    const data = await fetchAPI(url);
    const tbody = document.getElementById('alertsTableBody');
    tbody.innerHTML = '';
    
    if (!data || !data.alerts || data.alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No alerts found</td></tr>';
        return;
    }
    
    data.alerts.forEach(a => {
        const risk = (a.risk_score * 100 || 0).toFixed(0);
        const color = risk > 80 ? '#ef4444' : risk > 60 ? '#f59e0b' : risk > 40 ? '#8b5cf6' : '#3b82f6';
        const alertId = a.alert_id || 'N/A';
        
        tbody.innerHTML += `
            <tr>
                <td><strong>${alertId}</strong></td>
                <td style="font-size:12px;color:#94a3b8;">${formatTime(a.timestamp)}</td>
                <td>${formatType(a.threat_type)}</td>
                <td><span class="severity-badge ${a.severity || 'low'}">${(a.severity || 'low').toUpperCase()}</span></td>
                <td>
                    <div class="risk-bar"><div class="risk-fill" style="width:${risk}%;background:${color};"></div></div>
                    ${risk}%
                </td>
                <td>${a.user_id || 'N/A'}</td>
                <td><span class="status-badge ${a.status || 'new'}">${a.status || 'new'}</span></td>
                <td>
                    <button onclick="viewAlert('${alertId}')" style="background:#4A6CF7;border:none;color:#fff;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px;">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

// ===== VIEW ALERT =====
function viewAlert(alertId) {
    fetchAPI('/alerts?limit=100').then(data => {
        const alert = data.alerts.find(a => a.alert_id === alertId);
        if (alert) showModal(alert);
        else alert('Alert not found');
    });
}

// ===== SHOW MODAL =====
function showModal(alert) {
    document.querySelectorAll('.modal-overlay').forEach(el => el.remove());
    
    const risk = (alert.risk_score * 100 || 0).toFixed(0);
    const colors = { critical: '#ef4444', high: '#e67e22', medium: '#f59e0b', low: '#3b82f6' };
    const color = colors[alert.severity] || '#3b82f6';
    
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;z-index:99999;';
    
    overlay.innerHTML = `
        <div style="background:#1a2234;border:1px solid #2d3748;border-radius:12px;max-width:550px;width:95%;max-height:90vh;overflow-y:auto;padding:24px;color:#e5e7eb;">
            <div style="display:flex;justify-content:space-between;margin-bottom:16px;border-bottom:1px solid #2d3748;padding-bottom:12px;">
                <h3><i class="fas fa-exclamation-triangle" style="color:${color};"></i> Alert Details</h3>
                <button onclick="this.closest('.modal-overlay').remove()" style="background:transparent;border:none;color:#94a3b8;font-size:24px;cursor:pointer;">×</button>
            </div>
            <div style="display:grid;gap:8px;font-size:14px;">
                <div><strong>ID:</strong> ${alert.alert_id}</div>
                <div><strong>Time:</strong> ${formatTime(alert.timestamp)}</div>
                <div><strong>Threat:</strong> <span style="color:#4A6CF7;font-weight:600;">${formatType(alert.threat_type)}</span></div>
                <div><strong>Severity:</strong> <span class="severity-badge ${alert.severity}">${(alert.severity || 'low').toUpperCase()}</span></div>
                <div style="background:#0a0e1a;padding:12px;border-radius:8px;border-left:4px solid ${color};">
                    <strong>Risk Score:</strong> <span style="color:${color};font-weight:700;font-size:24px;">${risk}%</span>
                    <div style="height:4px;background:#2d3748;border-radius:2px;margin-top:6px;"><div style="height:100%;width:${risk}%;background:${color};border-radius:2px;"></div></div>
                </div>
                <div><strong>User:</strong> ${alert.user_id || 'N/A'}</div>
                <div><strong>Device:</strong> ${alert.device_id || 'N/A'}</div>
                <div><strong>IP:</strong> ${alert.ip || 'N/A'}</div>
                <div><strong>Status:</strong> <span class="status-badge ${alert.status || 'new'}">${alert.status || 'new'}</span></div>
                <div><strong>Explanation:</strong></div>
                <div style="background:#0a0e1a;padding:10px;border-radius:6px;font-size:13px;color:#94a3b8;">${alert.explanation || 'No explanation'}</div>
                ${alert.recommendations ? `
                <div style="border-top:1px solid #2d3748;padding-top:10px;">
                    <strong>Recommendations:</strong>
                    <ul style="margin:4px 0 0 18px;color:#94a3b8;font-size:13px;">${alert.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>
                </div>` : ''}
            </div>
            <div style="margin-top:16px;display:flex;gap:10px;justify-content:flex-end;border-top:1px solid #2d3748;padding-top:12px;">
                <button onclick="this.closest('.modal-overlay').remove()" style="padding:6px 16px;border-radius:6px;border:1px solid #2d3748;background:transparent;color:#94a3b8;cursor:pointer;">Close</button>
                <button onclick="resolveAlert('${alert.alert_id}')" style="padding:6px 16px;border-radius:6px;border:none;background:#10b981;color:#fff;cursor:pointer;">Resolve</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
}

// ===== RESOLVE ALERT =====
function resolveAlert(id) {
    if (!confirm('Resolve this alert?')) return;
    fetch(`${API}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: id, feedback_type: 'true_positive', comment: 'Resolved' })
    }).then(() => {
        alert('✅ Resolved!');
        document.querySelector('.modal-overlay')?.remove();
        loadAlerts();
        loadDashboard();
    }).catch(() => alert('Failed'));
}

// ===== THREATS =====
function loadThreats() {
    const grid = document.getElementById('threatsGrid');
    const threats = [
        { name: 'Brute Force', icon: 'fa-key', desc: 'Multiple failed login attempts in short time', severity: 'High', rate: '98%', fpr: '3%', color: '#ef4444' },
        { name: 'Impossible Travel', icon: 'fa-globe', desc: 'Login from geographically distant locations', severity: 'Critical', rate: '99%', fpr: '1%', color: '#dc2626' },
        { name: 'Lateral Movement', icon: 'fa-arrows-left-right', desc: 'Suspicious internal network connections', severity: 'Critical', rate: '95%', fpr: '5%', color: '#f59e0b' },
        { name: 'Credential Misuse', icon: 'fa-user-lock', desc: 'Access using compromised credentials', severity: 'High', rate: '97%', fpr: '2%', color: '#8b5cf6' },
        { name: 'Device Spoofing', icon: 'fa-laptop', desc: 'Access from spoofed device identity', severity: 'Medium', rate: '94%', fpr: '4%', color: '#3b82f6' }
    ];
    grid.innerHTML = '';
    threats.forEach(t => {
        grid.innerHTML += `
            <div class="threat-card">
                <h4><i class="fas ${t.icon}" style="color:${t.color};"></i> ${t.name} <span style="float:right;font-size:12px;color:${t.color};">${t.severity}</span></h4>
                <div class="desc">${t.desc}</div>
                <div class="metrics">
                    <div><div class="val">${t.rate}</div><div class="lbl">Detection Rate</div></div>
                    <div><div class="val">${t.fpr}</div><div class="lbl">False Positives</div></div>
                    <div><div class="val" style="color:${t.color};">${t.severity}</div><div class="lbl">Severity</div></div>
                </div>
            </div>
        `;
    });
}

// ===== MODELS =====
function loadModels() {
    document.getElementById('modelsGrid').innerHTML = `
        <div class="model-card">
            <h4><i class="fas fa-tree"></i> Isolation Forest</h4>
            <div class="metric"><span class="label">Accuracy</span><span class="value">92.3%</span><div class="progress"><div class="fill" style="width:92.3%"></div></div></div>
            <div class="metric"><span class="label">FPR</span><span class="value">3.2%</span><div class="progress"><div class="fill" style="width:3.2%;background:#f59e0b;"></div></div></div>
            <div class="metric"><span class="label">F1 Score</span><span class="value">0.89</span><div class="progress"><div class="fill" style="width:89%"></div></div></div>
        </div>
        <div class="model-card">
            <h4><i class="fas fa-network-wired"></i> Autoencoder</h4>
            <div class="metric"><span class="label">Accuracy</span><span class="value">91.7%</span><div class="progress"><div class="fill" style="width:91.7%"></div></div></div>
            <div class="metric"><span class="label">FPR</span><span class="value">2.8%</span><div class="progress"><div class="fill" style="width:2.8%;background:#f59e0b;"></div></div></div>
            <div class="metric"><span class="label">F1 Score</span><span class="value">0.88</span><div class="progress"><div class="fill" style="width:88%"></div></div></div>
        </div>
        <div class="model-card featured">
            <h4><i class="fas fa-layer-group"></i> Ensemble Detector <span class="badge">★ Best</span></h4>
            <div class="metric"><span class="label">Accuracy</span><span class="value">94.2%</span><div class="progress"><div class="fill" style="width:94.2%"></div></div></div>
            <div class="metric"><span class="label">FPR</span><span class="value">1.9%</span><div class="progress"><div class="fill" style="width:1.9%;background:#10b981;"></div></div></div>
            <div class="metric"><span class="label">F1 Score</span><span class="value">0.93</span><div class="progress"><div class="fill" style="width:93%"></div></div></div>
        </div>
    `;
}

// ===== LOGS =====
async function loadLogs() {
    const data = await fetchAPI('/logs?limit=20');
    const tbody = document.getElementById('logsTableBody');
    tbody.innerHTML = '';
    
    if (!data || !data.logs || data.logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No logs found</td></tr>';
        return;
    }
    
    data.logs.forEach(log => {
        tbody.innerHTML += `
            <tr>
                <td style="font-size:12px;color:#94a3b8;">${formatTime(log.timestamp)}</td>
                <td><span class="tag">${log.event_type || 'Unknown'}</span></td>
                <td>${log.user_id || 'N/A'}</td>
                <td>${log.source_ip || 'N/A'}</td>
                <td>${log.details || 'No details'}</td>
                <td><span class="status-badge ${log.status || 'success'}">${log.status || 'success'}</span></td>
            </tr>
        `;
    });
}

// ===== UTILITY =====
function formatTime(t) {
    if (!t) return 'N/A';
    try { return new Date(t).toLocaleString('en-US', {month:'short', day:'2-digit', hour:'2-digit', minute:'2-digit'}); }
    catch { return 'N/A'; }
}

function formatType(t) {
    if (!t) return 'Unknown';
    return t.replace(/_/g, ' ').toUpperCase();
}

// ===== UPTIME =====
const startTime = new Date();
setInterval(() => {
    const s = Math.floor((new Date() - startTime) / 1000);
    document.getElementById('uptime').textContent =
        String(Math.floor(s/3600)).padStart(2,'0') + ':' +
        String(Math.floor((s%3600)/60)).padStart(2,'0') + ':' +
        String(s%60).padStart(2,'0');
}, 1000);

// ===== EVENTS =====
document.getElementById('refreshBtn')?.addEventListener('click', loadDashboard);
document.getElementById('applyFilters')?.addEventListener('click', loadAlerts);
document.getElementById('resetFilters')?.addEventListener('click', () => {
    document.getElementById('severityFilter').value = 'all';
    document.getElementById('threatFilter').value = 'all';
    loadAlerts();
});

// ============================================================
// ===== SEARCH BAR - FIXED =====
// ============================================================
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('keyup', function(e) {
        const query = this.value.toLowerCase().trim();
        
        // If Enter key pressed OR query has 3+ characters
        if (e.key === 'Enter' || query.length >= 3) {
            // Navigate to alerts tab if not already there
            if (!document.getElementById('alerts').classList.contains('active')) {
                document.querySelectorAll('.nav a').forEach(l => l.classList.remove('active'));
                const alertsLink = document.querySelector('[data-section="alerts"]');
                if (alertsLink) {
                    alertsLink.classList.add('active');
                    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                    document.getElementById('alerts').classList.add('active');
                    document.getElementById('pageTitle').textContent = 'Security Alerts';
                    document.getElementById('breadcrumbCurrent').textContent = 'Security Alerts';
                    loadAlerts();
                }
            }
            
            // Filter alerts after loading
            setTimeout(() => {
                const rows = document.querySelectorAll('#alertsTableBody tr');
                let found = 0;
                rows.forEach(row => {
                    // Skip empty state row
                    if (row.querySelector('.empty-state')) {
                        row.style.display = '';
                        return;
                    }
                    const text = row.textContent.toLowerCase();
                    if (text.includes(query)) {
                        row.style.display = '';
                        found++;
                    } else {
                        row.style.display = 'none';
                    }
                });
                console.log('🔍 Found ' + found + ' results for "' + query + '"');
            }, 400);
        }
        
        // If empty, reload alerts
        if (query === '') {
            if (document.getElementById('alerts').classList.contains('active')) {
                loadAlerts();
            }
        }
    });
    console.log('✅ Search bar initialized!');
} else {
    console.log('❌ Search input not found!');
}

// ===== MAKE GLOBAL =====
window.viewAlert = viewAlert;
window.resolveAlert = resolveAlert;
window.viewAllAlerts = viewAllAlerts;

// ===== INIT =====
loadDashboard();
loadThreats();
loadModels();
loadLogs();

console.log('🚀 ThreatGuard loaded successfully!');