import pytest
import asyncio
from datetime import datetime, timedelta
import json

@pytest.mark.asyncio
async def test_process_normal_log(anomaly_detector, sample_log):
    """Test processing normal log"""
    result = await anomaly_detector.process_log(sample_log)
    assert result["status"] == "normal"
    assert "log" in result

@pytest.mark.asyncio
async def test_process_anomalous_log(anomaly_detector, sample_anomalous_log):
    """Test processing anomalous log"""
    result = await anomaly_detector.process_log(sample_anomalous_log)
    if result["status"] == "anomaly":
        assert "alert_id" in result
        assert "risk_score" in result
        assert "threat_type" in result
        assert "severity" in result
        assert "explanation" in result

@pytest.mark.asyncio
async def test_process_real_time(anomaly_detector, sample_log):
    """Test real-time processing"""
    data = json.dumps(sample_log)
    result = await anomaly_detector.process_real_time(data)
    assert result["status"] in ["normal", "anomaly", "error"]

@pytest.mark.asyncio
async def test_real_time_with_anomaly(anomaly_detector, sample_anomalous_log):
    """Test real-time processing of anomaly"""
    data = json.dumps(sample_anomalous_log)
    result = await anomaly_detector.process_real_time(data)
    if result["status"] == "anomaly":
        assert "risk_score" in result
        assert result["risk_score"] > 0.5

def test_baseline_update(anomaly_detector, sample_log):
    """Test baseline update"""
    # Process multiple logs to build baseline
    for _ in range(10):
        anomaly_detector._update_baselines(sample_log, {"hour": 10})
    
    # Check user baseline
    user = sample_log.get('user_id')
    assert user in anomaly_detector.user_baselines
    assert 'hours' in anomaly_detector.user_baselines[user]

def test_statistical_anomaly(anomaly_detector, sample_anomalous_log):
    """Test statistical anomaly detection"""
    features = {"hour": 2, "access_count": 15, "failed_attempts": 5}
    score = anomaly_detector._statistical_anomaly_score(features, sample_anomalous_log)
    assert 0 <= score <= 1

def test_rule_based_detection(anomaly_detector, sample_log):
    """Test rule-based detection"""
    score = anomaly_detector._rule_based_score(sample_log)
    assert 0 <= score <= 1

def test_threat_classification(anomaly_detector, sample_anomalous_log):
    """Test threat classification"""
    features = {"hour": 2}
    threat_type = anomaly_detector._classify_threat(sample_anomalous_log, features)
    assert threat_type in ["brute_force", "impossible_travel", "lateral_movement", 
                          "credential_misuse", "device_spoofing", "unknown"]

def test_severity_calculation(anomaly_detector):
    """Test severity calculation"""
    assert anomaly_detector._calculate_severity(0.95) == "critical"
    assert anomaly_detector._calculate_severity(0.8) == "high"
    assert anomaly_detector._calculate_severity(0.6) == "medium"
    assert anomaly_detector._calculate_severity(0.4) == "low"

def test_recommendations(anomaly_detector):
    """Test recommendation generation"""
    recommendations = anomaly_detector._generate_recommendations("brute_force")
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0

def test_distance_calculation(anomaly_detector):
    """Test distance calculation between locations"""
    loc1 = {"lat": 40.7128, "lon": -74.0060}
    loc2 = {"lat": 51.5074, "lon": -0.1278}
    distance = anomaly_detector._calculate_distance(loc1, loc2)
    assert distance > 0
    assert distance < 20000  # Reasonable max distance