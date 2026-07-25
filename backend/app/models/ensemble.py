import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Autoencoder(nn.Module):
    def __init__(self, input_dim, encoding_dim=32):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class EnsembleDetector:
    def __init__(self):
        self.isolation_forest = None
        self.autoencoder = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.input_dim = None
        
    def train(self, X: np.ndarray):
        """Train ensemble model"""
        try:
            self.input_dim = X.shape[1]
            
            # Train Isolation Forest
            self.isolation_forest = IsolationForest(
                contamination=0.05,
                random_state=42,
                n_estimators=100
            )
            self.isolation_forest.fit(X)
            
            # Train Autoencoder
            self.autoencoder = Autoencoder(self.input_dim)
            optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            # Convert to tensor
            X_tensor = torch.FloatTensor(X)
            
            # Training loop
            self.autoencoder.train()
            for epoch in range(50):
                optimizer.zero_grad()
                reconstructed = self.autoencoder(X_tensor)
                loss = criterion(reconstructed, X_tensor)
                loss.backward()
                optimizer.step()
            
            self.is_trained = True
            logger.info("Ensemble model trained successfully")
            
        except Exception as e:
            logger.error(f"Error training ensemble model: {e}")
            raise
    
    def isolation_forest_score(self, features: Dict) -> float:
        """Get anomaly score from Isolation Forest"""
        if not self.is_trained or self.isolation_forest is None:
            return 0.5
        
        try:
            # Convert features to array
            X = self._features_to_array(features)
            score = self.isolation_forest.score_samples([X])[0]
            # Normalize to [0, 1]
            score = 1 - (score + 0.5)  # Simple normalization
            return max(0, min(1, score))
        except Exception as e:
            logger.error(f"Error in isolation forest score: {e}")
            return 0.5
    
    def autoencoder_score(self, features: Dict) -> float:
        """Get reconstruction error from autoencoder"""
        if not self.is_trained or self.autoencoder is None:
            return 0.5
        
        try:
            X = self._features_to_array(features)
            X_tensor = torch.FloatTensor([X])
            
            self.autoencoder.eval()
            with torch.no_grad():
                reconstructed = self.autoencoder(X_tensor)
                loss = nn.MSELoss()(reconstructed, X_tensor)
            
            # Normalize error
            score = min(1, float(loss) * 10)  # Scale factor
            return score
        except Exception as e:
            logger.error(f"Error in autoencoder score: {e}")
            return 0.5
    
    def _features_to_array(self, features: Dict) -> np.ndarray:
        """Convert features dict to numpy array"""
        # This should match the feature extraction in FeatureEngineer
        feature_keys = ['hour', 'day_of_week', 'access_count', 'failed_attempts',
                       'response_time', 'bytes_transferred', 'is_success']
        
        arr = []
        for key in feature_keys:
            arr.append(features.get(key, 0))
        
        return np.array(arr)
    
    def predict(self, features: Dict) -> Dict[str, float]:
        """Get predictions from all models"""
        return {
            'isolation_forest': self.isolation_forest_score(features),
            'autoencoder': self.autoencoder_score(features),
            'ensemble': (self.isolation_forest_score(features) + 
                        self.autoencoder_score(features)) / 2
        }