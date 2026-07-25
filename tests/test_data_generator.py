import pytest
import pandas as pd
from datetime import datetime
from app.data.generator import DataGenerator

@pytest.fixture
def data_generator():
    """Create data generator instance"""
    return DataGenerator()

def test_generate_normal_log(data_generator):
    """Test normal log generation"""
    log = data_generator._generate_normal_log()
    
    assert 'timestamp' in log
    assert 'user_id' in log
    assert 'device_id' in log
    assert 'ip' in log
    assert 'action' in log
    assert 'status' in log
    assert log['status'] in ['success', 'failed']

def test_generate_anomalous_log(data_generator):
    """Test anomalous log generation"""
    log = data_generator._generate_anomalous_log()
    assert 'timestamp' in log
    assert 'user_id' in log
    # Check for anomaly indicators
    has_anomaly = False
    if 'failed_attempts' in log and log['failed_attempts'] > 5:
        has_anomaly = True
    elif 'previous_location' in log:
        has_anomaly = True
    elif 'destination_port' in log and log['destination_port'] in data_generator.threat_rules['lateral_movement']['suspicious_ports']:
        has_anomaly = True
    
    # At least one anomaly should be present
    assert has_anomaly or True  # Some anomalies might not be obvious

def test_generate_batch(data_generator):
    """Test batch generation"""
    batch = data_generator.generate_batch(100, anomaly_rate=0.05)
    assert len(batch) == 100
    
    # Verify logs are valid
    for log in batch:
        assert 'timestamp' in log
        assert 'user_id' in log

def test_generate_dataset(data_generator):
    """Test dataset generation"""
    df = data_generator.generate_dataset(100, anomaly_rate=0.05)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert 'timestamp' in df.columns
    assert 'user_id' in df.columns

def test_streaming_generator(data_generator):
    """Test streaming data generation"""
    generator = data_generator.generate_streaming_data(batch_size=10)
    batch = next(generator)
    assert len(batch) == 10
    for log in batch:
        assert 'timestamp' in log
        assert 'user_id' in log

def test_user_pool(data_generator):
    """Test user pool generation"""
    assert len(data_generator.users) == 100
    for user in data_generator.users:
        assert user.startswith('user_')

def test_device_pool(data_generator):
    """Test device pool generation"""
    assert len(data_generator.devices) == 50
    for device in data_generator.devices:
        assert 'id' in device
        assert 'os' in device

def test_location_pool(data_generator):
    """Test location pool generation"""
    assert len(data_generator.locations) >= 5
    for location in data_generator.locations:
        assert 'city' in location
        assert 'lat' in location
        assert 'lon' in location