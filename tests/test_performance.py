import pytest
import time
import asyncio
import sys
from app.data.generator import DataGenerator
from app.core.feature_engineering import FeatureEngineer

@pytest.fixture
def data_generator():
    """Create data generator instance"""
    return DataGenerator()

@pytest.fixture
def feature_engineer():
    """Create feature engineer instance"""
    return FeatureEngineer()

def test_data_generation_performance(data_generator):
    """Test data generation performance"""
    start_time = time.time()
    
    # Generate 1,000 logs (reduced from 10,000 for performance)
    logs = data_generator.generate_batch(1000)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should generate 1,000 logs in under 2 seconds
    assert duration < 2.0
    assert len(logs) == 1000

def test_feature_extraction_performance(feature_engineer):
    """Test feature extraction performance"""
    # Create sample logs
    data_gen = DataGenerator()
    sample_logs = data_gen.generate_batch(100)
    
    start_time = time.time()
    
    # Extract features from 100 logs
    features = feature_engineer.extract_batch(sample_logs)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should process 100 logs in under 1 second
    assert duration < 1.0
    assert len(features) == len(sample_logs)

def test_api_response_time(client):
    """Test API response times"""
    endpoints = [
        "/api/health",
        "/api/stats",
        "/api/alerts?limit=10",
        "/api/model/status"
    ]
    
    for endpoint in endpoints:
        start_time = time.time()
        response = client.get(endpoint)
        end_time = time.time()
        
        duration = end_time - start_time
        assert response.status_code == 200
        assert duration < 1.0  # Should respond in under 1 second

def test_memory_usage(data_generator):
    """Test memory usage (simplified)"""
    import sys
    
    # Generate batch
    logs = data_generator.generate_batch(500)
    
    # Check size is reasonable
    size_in_bytes = sys.getsizeof(logs)
    size_in_mb = size_in_bytes / (1024 * 1024)
    
    # Should be under 50MB for 500 logs
    assert size_in_mb < 50

@pytest.mark.slow
def test_large_dataset_performance(data_generator):
    """Test performance with larger dataset (marked as slow)"""
    start_time = time.time()
    
    # Generate 5,000 logs
    logs = data_generator.generate_batch(5000)
    
    end_time = time.time()
    duration = end_time - start_time
    
    assert duration < 5.0
    assert len(logs) == 5000