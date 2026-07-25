import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.main import app
from app.core.anomaly_detector import AnomalyDetector
from app.core.feature_engineering import FeatureEngineer
from app.data.generator import DataGenerator
from app.models.ensemble import EnsembleDetector

@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)

@pytest.fixture
def sample_log():
    """Generate a sample log for testing"""
    return {
        'timestamp': datetime.now().isoformat(),
        'user_id': 'user_1',
        'device_id': 'device_1',
        'os': 'Windows',
        'ip': '192.168.1.100',
        'location': {'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
        'action': 'login',
        'resource': '/api/resource_1',
        'status': 'success',
        'response_time': 0.5,
        'session_id': 'session_123',
        'source_port': 54321,
        'destination_port': 443,
        'bytes_transferred': 1024
    }

@pytest.fixture
def sample_anomalous_log():
    """Generate a sample anomalous log for testing"""
    return {
        'timestamp': datetime.now().isoformat(),
        'user_id': 'user_1',
        'device_id': 'device_1',
        'os': 'Windows',
        'ip': '192.168.1.100',
        'location': {'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
        'action': 'login',
        'resource': '/api/resource_1',
        'status': 'failed',
        'response_time': 0.5,
        'session_id': 'session_123',
        'source_port': 54321,
        'destination_port': 443,
        'bytes_transferred': 1024,
        'failed_attempts': 10
    }

@pytest.fixture
def anomaly_detector():
    """Create anomaly detector instance"""
    from app.core.model_manager import ModelManager
    model_manager = ModelManager()
    detector = AnomalyDetector(model_manager)
    return detector

@pytest.fixture
def feature_engineer():
    """Create feature engineer instance"""
    return FeatureEngineer()

@pytest.fixture
def data_generator():
    """Create data generator instance"""
    return DataGenerator()

@pytest.fixture
def ensemble_detector():
    """Create ensemble detector instance"""
    detector = EnsembleDetector()
    # Train with sample data
    X = np.random.randn(100, 5)
    detector.train(X)
    return detector

@pytest.fixture
def sample_batch_logs():
    """Generate batch of sample logs"""
    logs = []
    for i in range(50):
        log = {
            'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
            'user_id': f'user_{i % 10}',
            'device_id': f'device_{i % 5}',
            'os': random.choice(['Windows', 'MacOS', 'Linux']),
            'ip': f'192.168.{random.randint(1,254)}.{random.randint(1,254)}',
            'location': {'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
            'action': random.choice(['login', 'access', 'read', 'write']),
            'resource': f'/api/resource_{i % 20}',
            'status': random.choice(['success', 'success', 'success', 'failed']),
            'response_time': random.uniform(0.1, 2.0),
            'session_id': f'session_{i}',
            'source_port': random.randint(1024, 65535),
            'destination_port': random.choice([80, 443, 22, 3306]),
            'bytes_transferred': random.randint(1024, 10485760)
        }
        logs.append(log)
    return logs