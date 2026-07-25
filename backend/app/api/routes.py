from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import numpy as np
import random
import pandas as pd
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.1"
    }

@router.get("/alerts")
async def get_alerts(
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    threat_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None, regex="^(new|investigating|resolved)$")
):
    """Get recent alerts with optional filtering"""
    # In production, this would query a database
    # For demo, return sample alerts
    alerts = generate_sample_alerts(limit)
    
    if severity:
        alerts = [a for a in alerts if a.get('severity') == severity]
    if threat_type:
        alerts = [a for a in alerts if a.get('threat_type') == threat_type]
    if status:
        alerts = [a for a in alerts if a.get('status') == status]
    
    return {
        "total": len(alerts),
        "alerts": alerts,
        "filters_applied": {
            "severity": severity,
            "threat_type": threat_type,
            "status": status
        }
    }

@router.get("/stats")
async def get_stats(time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$")):
    """Get statistics for dashboard"""
    # Generate realistic stats
    total_logs = random.randint(5000, 15000)
    anomalies = random.randint(50, 500)
    
    threat_types = ['brute_force', 'impossible_travel', 'lateral_movement', 
                    'credential_misuse', 'device_spoofing']
    
    # Generate threat distribution
    threat_distribution = {}
    for threat in threat_types:
        threat_distribution[threat] = random.randint(5, 100)
    
    # Generate severity distribution
    severity_distribution = {
        "critical": random.randint(5, 20),
        "high": random.randint(20, 50),
        "medium": random.randint(30, 80),
        "low": random.randint(40, 100)
    }
    
    # Generate top users
    top_users = []
    for i in range(5):
        top_users.append({
            "user_id": f"user_{random.randint(1, 100)}",
            "access_count": random.randint(50, 500),
            "risk_score": random.uniform(0.1, 0.8)
        })
    
    # Generate top devices
    top_devices = []
    for i in range(5):
        top_devices.append({
            "device_id": f"device_{random.randint(1, 50)}",
            "access_count": random.randint(30, 400),
            "risk_score": random.uniform(0.1, 0.7)
        })
    
    # Generate time series data (last 24 hours)
    time_series = []
    for i in range(24):
        time_series.append({
            "hour": i,
            "logs": random.randint(50, 200),
            "anomalies": random.randint(0, 15)
        })
    
    stats = {
        "total_logs": total_logs,
        "anomalies_detected": anomalies,
        "anomaly_rate": round(anomalies / max(total_logs, 1) * 100, 2),
        "threat_distribution": threat_distribution,
        "severity_distribution": severity_distribution,
        "top_users": sorted(top_users, key=lambda x: x['access_count'], reverse=True),
        "top_devices": sorted(top_devices, key=lambda x: x['access_count'], reverse=True),
        "time_series": time_series,
        "timestamp": datetime.now().isoformat()
    }
    
    return stats

@router.get("/stats/realtime")
async def get_realtime_stats():
    """Get real-time statistics for live dashboard updates"""
    return {
        "timestamp": datetime.now().isoformat(),
        "logs_per_second": random.randint(10, 100),
        "anomalies_per_minute": random.randint(1, 10),
        "active_sessions": random.randint(50, 200),
        "system_load": round(random.uniform(0.1, 0.8), 2)
    }

@router.get("/threats/{threat_type}")
async def get_threat_details(threat_type: str):
    """Get detailed information about a specific threat type"""
    threat_info = {
        "brute_force": {
            "name": "Brute Force Attack",
            "description": "Multiple failed login attempts in short time",
            "severity": "high",
            "mitigation": [
                "Enable account lockout after 5 failed attempts",
                "Implement CAPTCHA after 3 failed attempts",
                "Use rate limiting on login endpoints",
                "Monitor for unusual login patterns"
            ],
            "detection_method": "Rule-based + ML",
            "false_positive_rate": 0.03,
            "detection_rate": 0.98,
            "typical_indicators": [
                "Many failed login attempts from same IP",
                "Rapid successive login attempts",
                "Access from unusual locations"
            ]
        },
        "impossible_travel": {
            "name": "Impossible Travel",
            "description": "Login from two geographically distant locations in short time",
            "severity": "critical",
            "mitigation": [
                "Require additional authentication",
                "Notify user of suspicious login",
                "Implement risk-based authentication",
                "Block access from conflicting locations"
            ],
            "detection_method": "Rule-based + ML",
            "false_positive_rate": 0.01,
            "detection_rate": 0.99,
            "typical_indicators": [
                "Login from two locations within minutes",
                "Geographic distance impossible to travel",
                "Different time zones in short period"
            ]
        },
        "lateral_movement": {
            "name": "Lateral Movement",
            "description": "Suspicious network connections indicating internal movement",
            "severity": "critical",
            "mitigation": [
                "Block suspicious ports",
                "Implement network segmentation",
                "Monitor internal network traffic",
                "Use Zero Trust architecture"
            ],
            "detection_method": "Behavioral + ML",
            "false_positive_rate": 0.05,
            "detection_rate": 0.95,
            "typical_indicators": [
                "Connection to sensitive internal services",
                "Unusual internal network paths",
                "Unexpected service access patterns"
            ]
        },
        "credential_misuse": {
            "name": "Credential Misuse",
            "description": "Access using compromised credentials",
            "severity": "high",
            "mitigation": [
                "Force password reset",
                "Enable MFA for all users",
                "Monitor for credential sharing",
                "Implement password policies"
            ],
            "detection_method": "Behavioral + ML",
            "false_positive_rate": 0.02,
            "detection_rate": 0.97,
            "typical_indicators": [
                "Access from unusual hours",
                "Access from unfamiliar locations",
                "Anomalous access patterns"
            ]
        },
        "device_spoofing": {
            "name": "Device Spoofing",
            "description": "Access from device with spoofed identity",
            "severity": "medium",
            "mitigation": [
                "Block unknown devices",
                "Implement device fingerprinting",
                "Require device registration",
                "Monitor for device anomalies"
            ],
            "detection_method": "Device fingerprinting + ML",
            "false_positive_rate": 0.04,
            "detection_rate": 0.94,
            "typical_indicators": [
                "Device OS mismatch",
                "Spoofed device IDs",
                "Unusual device characteristics"
            ]
        }
    }
    
    if threat_type not in threat_info:
        raise HTTPException(status_code=404, detail=f"Threat type '{threat_type}' not found")
    
    return threat_info[threat_type]

@router.post("/feedback")
async def submit_feedback(feedback: Dict[str, Any]):
    """Submit feedback on alert (true positive/false positive)"""
    required_fields = ['alert_id', 'feedback_type', 'comment']
    
    # Validate required fields
    for field in required_fields:
        if field not in feedback:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Validate feedback type
    if feedback['feedback_type'] not in ['true_positive', 'false_positive', 'uncertain']:
        raise HTTPException(
            status_code=400, 
            detail="feedback_type must be 'true_positive', 'false_positive', or 'uncertain'"
        )
    
    # In production, store feedback for model improvement
    # For demo, just acknowledge
    return {
        "status": "success", 
        "message": "Feedback received",
        "feedback_id": f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/model/status")
async def get_model_status():
    """Get current model status"""
    return {
        "status": "active",
        "last_training": (datetime.now() - timedelta(hours=2)).isoformat(),
        "next_training": (datetime.now() + timedelta(hours=22)).isoformat(),
        "accuracy": 0.942,
        "precision": 0.938,
        "recall": 0.946,
        "false_positive_rate": 0.019,
        "false_negative_rate": 0.021,
        "f1_score": 0.942,
        "training_data_size": 10000,
        "feature_count": 15,
        "model_version": "3.0.1",
        "ensemble_type": "Isolation Forest + Autoencoder",
        "last_improvement": "0.8% improvement in accuracy"
    }

@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """Get audit logs with filtering"""
    logs = generate_sample_logs(limit)
    
    if event_type:
        logs = [l for l in logs if l.get('event_type') == event_type]
    if user_id:
        logs = [l for l in logs if l.get('user_id') == user_id]
    
    return {
        "total": len(logs),
        "logs": logs
    }

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get complete dashboard summary"""
    stats = await get_stats("24h")
    recent_alerts = await get_alerts(limit=5)
    model_status = await get_model_status()
    
    return {
        "stats": stats,
        "recent_alerts": recent_alerts['alerts'],
        "model_status": model_status,
        "system_health": {
            "status": "operational",
            "uptime": "99.98%",
            "last_incident": None
        }
    }

def generate_sample_alerts(count: int) -> List[Dict]:
    """Generate sample alerts for demo"""
    alerts = []
    threat_types = ['brute_force', 'impossible_travel', 'lateral_movement', 
                    'credential_misuse', 'device_spoofing']
    severities = ['low', 'medium', 'high', 'critical']
    statuses = ['new', 'investigating', 'resolved']
    
    for i in range(min(count, 1000)):
        threat_type = random.choice(threat_types)
        severity = random.choices(severities, weights=[0.1, 0.3, 0.4, 0.2])[0]
        status = random.choices(statuses, weights=[0.6, 0.3, 0.1])[0]
        
        # Generate timestamp within last 24 hours
        minutes_ago = random.randint(0, 1440)
        timestamp = datetime.now() - timedelta(minutes=minutes_ago)
        
        # Generate realistic explanation
        explanations = {
            'brute_force': f'Multiple failed login attempts detected for user_{random.randint(1,100)}',
            'impossible_travel': f'Login from {random.choice(["New York", "London", "Tokyo", "Sydney"])} and {random.choice(["Dubai", "Singapore", "Toronto", "San Francisco"])} within 5 minutes',
            'lateral_movement': f'Suspicious connection to port {random.choice([22, 3389, 445, 135])} detected',
            'credential_misuse': f'Unusual access pattern detected at {random.randint(0,4):02d}:00 hours',
            'device_spoofing': f'Device OS mismatch: {random.choice(["Windows", "MacOS", "Linux"])} vs {random.choice(["iOS", "Android", "Windows"])}'
        }
        
        alert = {
            "alert_id": f"ALT-{datetime.now().strftime('%Y%m%d')}-{i:04d}",
            "timestamp": timestamp.isoformat(),
            "threat_type": threat_type,
            "severity": severity,
            "risk_score": round(random.uniform(0.5, 0.99), 2),
            "user_id": f"user_{random.randint(1, 100)}",
            "device_id": f"device_{random.randint(1, 50)}",
            "ip": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
            "explanation": explanations.get(threat_type, f"Anomaly detected: {threat_type}"),
            "status": status,
            "location": random.choice(["New York", "London", "Tokyo", "Sydney", "Dubai", "Singapore", "Toronto", "San Francisco"]),
            "port": random.choice([22, 80, 443, 3389, 445, 135, 3306, 8080])
        }
        alerts.append(alert)
    
    return alerts

def generate_sample_logs(count: int) -> List[Dict]:
    """Generate sample audit logs"""
    logs = []
    event_types = ['login', 'access_granted', 'access_denied', 'file_accessed', 
                   'file_modified', 'config_change', 'threat_detected']
    statuses = ['success', 'failed', 'blocked', 'pending']
    
    for i in range(min(count, 500)):
        event_type = random.choice(event_types)
        status = random.choices(statuses, weights=[0.7, 0.15, 0.1, 0.05])[0]
        
        log = {
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 1440))).isoformat(),
            "event_type": event_type,
            "user_id": f"user_{random.randint(1, 100)}",
            "source_ip": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
            "status": status,
            "details": f"User performed {event_type} operation",
            "resource": f"/api/resource_{random.randint(1, 100)}",
            "duration_ms": random.randint(10, 5000)
        }
        logs.append(log)
    
    return sorted(logs, key=lambda x: x['timestamp'], reverse=True)