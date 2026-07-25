import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_get_alerts(client):
    """Test alerts endpoint"""
    response = client.get("/api/alerts?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "alerts" in data
    assert len(data["alerts"]) <= 10

def test_get_alerts_with_filters(client):
    """Test alerts with severity filter"""
    response = client.get("/api/alerts?severity=critical&limit=5")
    assert response.status_code == 200
    data = response.json()
    for alert in data["alerts"]:
        assert alert["severity"] == "critical"

def test_get_stats(client):
    """Test stats endpoint"""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_logs" in data
    assert "anomalies_detected" in data
    assert "threat_distribution" in data
    assert "severity_distribution" in data

def test_get_threat_details(client):
    """Test threat details endpoint"""
    response = client.get("/api/threats/brute_force")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Brute Force Attack"
    assert "mitigation" in data
    assert "detection_method" in data

def test_get_threat_details_not_found(client):
    """Test threat details for non-existent threat"""
    response = client.get("/api/threats/unknown_threat")
    assert response.status_code == 404

def test_submit_feedback(client):
    """Test feedback submission"""
    feedback = {
        "alert_id": "ALT-20240101-0001",
        "feedback_type": "true_positive",
        "comment": "This is a valid threat"
    }
    response = client.post("/api/feedback", json=feedback)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_submit_feedback_invalid(client):
    """Test feedback with invalid data"""
    feedback = {
        "alert_id": "ALT-20240101-0001",
        "feedback_type": "invalid_type"
    }
    response = client.post("/api/feedback", json=feedback)
    assert response.status_code == 400

def test_get_model_status(client):
    """Test model status endpoint"""
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "accuracy" in data
    assert "model_version" in data

def test_get_realtime_stats(client):
    """Test real-time stats endpoint"""
    response = client.get("/api/stats/realtime")
    assert response.status_code == 200
    data = response.json()
    assert "logs_per_second" in data
    assert "anomalies_per_minute" in data
    assert "timestamp" in data

def test_get_logs(client):
    """Test logs endpoint"""
    response = client.get("/api/logs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "logs" in data

def test_get_logs_with_filters(client):
    """Test logs with filters"""
    response = client.get("/api/logs?event_type=login&limit=5")
    assert response.status_code == 200
    data = response.json()
    for log in data["logs"]:
        assert log["event_type"] == "login"

def test_dashboard_summary(client):
    """Test dashboard summary endpoint"""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "recent_alerts" in data
    assert "model_status" in data
    assert "system_health" in data

def test_cors_headers(client):
    """Test CORS headers"""
    # OPTIONS request (preflight) should return CORS headers
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    # OPTIONS should return 200 or 204
    assert response.status_code in [200, 204]
    # Check if CORS headers are present
    assert "access-control-allow-origin" in response.headers
    
    # Also test that the actual endpoint works
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"