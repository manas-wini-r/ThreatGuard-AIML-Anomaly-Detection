import pytest
import numpy as np
import torch

def test_ensemble_initialization(ensemble_detector):
    """Test ensemble detector initialization"""
    assert ensemble_detector.is_trained == True
    assert ensemble_detector.isolation_forest is not None
    assert ensemble_detector.autoencoder is not None

def test_isolation_forest_score(ensemble_detector):
    """Test isolation forest scoring"""
    features = {'hour': 10, 'day_of_week': 3, 'access_count': 5, 
                'failed_attempts': 0, 'response_time': 0.5, 
                'bytes_transferred': 1024, 'is_success': 1}
    
    score = ensemble_detector.isolation_forest_score(features)
    assert 0 <= score <= 1

def test_autoencoder_score(ensemble_detector):
    """Test autoencoder scoring"""
    features = {'hour': 10, 'day_of_week': 3, 'access_count': 5, 
                'failed_attempts': 0, 'response_time': 0.5, 
                'bytes_transferred': 1024, 'is_success': 1}
    
    score = ensemble_detector.autoencoder_score(features)
    assert 0 <= score <= 1

def test_ensemble_predict(ensemble_detector):
    """Test ensemble prediction"""
    features = {'hour': 10, 'day_of_week': 3, 'access_count': 5, 
                'failed_attempts': 0, 'response_time': 0.5, 
                'bytes_transferred': 1024, 'is_success': 1}
    
    predictions = ensemble_detector.predict(features)
    assert 'isolation_forest' in predictions
    assert 'autoencoder' in predictions
    assert 'ensemble' in predictions
    
    for key, value in predictions.items():
        assert 0 <= value <= 1

def test_autoencoder_architecture():
    """Test autoencoder architecture"""
    from app.models.ensemble import Autoencoder
    model = Autoencoder(input_dim=10, encoding_dim=4)
    
    # Test forward pass
    x = torch.randn(5, 10)
    output = model(x)
    assert output.shape == (5, 10)

def test_ensemble_training():
    """Test ensemble training"""
    from app.models.ensemble import EnsembleDetector
    
    detector = EnsembleDetector()
    X = np.random.randn(100, 5)
    detector.train(X)
    
    assert detector.is_trained == True
    assert detector.input_dim == 5

def test_features_to_array(ensemble_detector):
    """Test feature conversion to array"""
    features = {'hour': 10, 'day_of_week': 3, 'access_count': 5, 
                'failed_attempts': 0, 'response_time': 0.5, 
                'bytes_transferred': 1024, 'is_success': 1}
    
    arr = ensemble_detector._features_to_array(features)
    assert isinstance(arr, np.ndarray)
    assert len(arr) == 7  # Number of features