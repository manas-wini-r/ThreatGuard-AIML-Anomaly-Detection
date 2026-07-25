"""
Attack Classification using Random Forest/XGBoost
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import logging

logger = logging.getLogger(__name__)

class AttackClassifier:
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.attack_types = [
            'credential_misuse',
            'brute_force',
            'impossible_travel',
            'device_spoofing',
            'lateral_movement',
            'normal'
        ]
        self.is_trained = False
        self._load_model()
    
    def train(self, X, y):
        """
        Train attack classifier
        """
        print("🔧 Training Attack Classifier...")
        
        # Convert X to numpy if it's a DataFrame
        if hasattr(X, 'values'):
            X = X.values
        
        # Handle empty or invalid data
        if len(X) == 0:
            print("❌ No training data provided!")
            return
        
        # Encode labels
        try:
            y_encoded = self.label_encoder.fit_transform(y)
        except Exception as e:
            print(f"❌ Error encoding labels: {e}")
            # Fallback: use only known labels
            valid_labels = ['normal', 'brute_force', 'credential_misuse', 'device_spoofing', 'impossible_travel', 'lateral_movement']
            y = [label if label in valid_labels else 'normal' for label in y]
            y_encoded = self.label_encoder.fit_transform(y)
        
        print(f"   Training samples: {len(X)}, Features: {X.shape[1] if len(X.shape) > 1 else 1}")
        print(f"   Classes: {self.label_encoder.classes_}")
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            random_state=42,
            class_weight='balanced'
        )
        
        try:
            self.model.fit(X, y_encoded)
            self.is_trained = True
            self._save_model()
            print("✅ Attack Classifier trained!")
        except Exception as e:
            print(f"❌ Training failed: {e}")
            # Create a dummy model that always returns 'normal'
            self.model = None
            self.is_trained = False
    
    def predict(self, features):
        """
        Predict attack type
        """
        if self.model is None or not self.is_trained:
            return 'normal', 0.0
        
        try:
            # Convert features to array
            if isinstance(features, dict):
                feature_array = np.array([list(features.values())])
            elif isinstance(features, list):
                feature_array = np.array([features])
            else:
                feature_array = features
            
            # Predict
            pred_encoded = self.model.predict(feature_array)[0]
            proba = self.model.predict_proba(feature_array)[0]
            
            # Get attack type and confidence
            attack_type = self.label_encoder.inverse_transform([pred_encoded])[0]
            confidence = float(max(proba))
            
            return attack_type, confidence
            
        except Exception as e:
            logger.error(f"Attack classification error: {e}")
            return 'normal', 0.0
    
    def predict_batch(self, X):
        """
        Predict attack types for batch
        """
        if self.model is None or not self.is_trained:
            return ['normal'] * len(X)
        
        try:
            predictions = self.model.predict(X)
            return self.label_encoder.inverse_transform(predictions)
        except:
            return ['normal'] * len(X)
    
    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs('ml_models', exist_ok=True)
            joblib.dump(self.model, 'ml_models/attack_classifier.pkl')
            joblib.dump(self.label_encoder, 'ml_models/attack_label_encoder.pkl')
        except Exception as e:
            print(f"❌ Error saving model: {e}")
    
    def _load_model(self):
        """Load model from disk"""
        try:
            if os.path.exists('ml_models/attack_classifier.pkl'):
                self.model = joblib.load('ml_models/attack_classifier.pkl')
                self.label_encoder = joblib.load('ml_models/attack_label_encoder.pkl')
                self.is_trained = True
                logger.info("✅ Attack classifier loaded!")
            else:
                logger.warning("⚠️ No attack classifier found")
        except Exception as e:
            logger.error(f"Error loading attack classifier: {e}")