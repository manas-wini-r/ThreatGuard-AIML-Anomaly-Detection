import pytest
import asyncio
from fastapi.testclient import TestClient

def test_end_to_end_flow(client, sample_log, sample_anomalous_log):
    """Test complete end-to-end flow"""
    
    # 1. Health check
    health = client.get("/api/health")
    assert health.status_code == 200
    
    # 2. Get initial stats
    stats = client.get("/api/stats")
    assert stats.status_code == 200
    initial_stats = stats.json()
    
    # 3. Get alerts
    alerts = client.get("/api/alerts?limit=10")
    assert alerts.status_code == 200
    alert_data = alerts.json()
    
    # 4. Submit feedback on first alert if exists
    if alert_data.get('alerts') and len(alert_data['alerts']) > 0:
        first_alert = alert_data['alerts'][0]
        feedback = {
            "alert_id": first_alert['alert_id'],
            "feedback_type": "true_positive",
            "comment": "Valid threat detected"
        }
        response = client.post("/api/feedback", json=feedback)
        assert response.status_code == 200
    
    # 5. Check model status
    model_status = client.get("/api/model/status")
    assert model_status.status_code == 200

def test_dashboard_integration(client):
    """Test dashboard integration"""
    # Get all dashboard data
    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    
    data = summary.json()
    
    # Verify all components are present
    assert "stats" in data
    assert "recent_alerts" in data
    assert "model_status" in data
    assert "system_health" in data
    
    # Verify stats have required fields
    stats = data["stats"]
    assert "total_logs" in stats
    assert "anomalies_detected" in stats

@pytest.mark.skip(reason="WebSocket test requires running server")
def test_websocket_integration():
    """Test WebSocket integration (requires websocket client)"""
    # Skip this test as it requires a running server
    # In production, you would use websocket-client library
    pass