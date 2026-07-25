"""
Model Manager with Drift Detection
"""
import asyncio
import joblib
import os
from datetime import datetime
import logging
from .drift_detector import DriftDetector

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.drift_detector = DriftDetector()
        self.current_model_version = "1.0.0"
        self.model_history = []
        self.is_retraining = False
        self.models_dir = "ml_models"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Load initial model
        self.load_model()
    
    def load_model(self):
        """Load latest model"""
        try:
            model_path = f"{self.models_dir}/best_model_smote.pkl"
            if os.path.exists(model_path):
                self.current_model = joblib.load(model_path)
                logger.info(f"✅ Loaded model version: {self.current_model_version}")
            else:
                logger.warning("⚠️ No model found, using default")
                self.current_model = None
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.current_model = None
    
    def check_drift(self, prediction_score):
        """Check for concept drift"""
        drift_detected = self.drift_detector.check_drift(prediction_score)
        
        if drift_detected:
            logger.warning("🔄 Concept Drift Detected - Starting Retraining...")
            asyncio.create_task(self.retrain_model())
        
        return drift_detected
    
    async def retrain_model(self):
        """Retrain model with new data"""
        if self.is_retraining:
            return
        
        self.is_retraining = True
        logger.info("🔧 Starting model retraining...")
        
        try:
            # Get new data
            from app.data.generator import DataGenerator
            from ml.train import ModelTrainer
            from ml.preprocessing import Preprocessor
            import pandas as pd
            
            # Generate fresh data
            gen = DataGenerator()
            logs = gen.generate_batch(5000, anomaly_rate=0.05)
            df = pd.DataFrame(logs)
            
            # Preprocess
            prep = Preprocessor()
            X, y = prep.preprocess(df)
            
            # Train
            trainer = ModelTrainer()
            result = trainer.train_with_sampling(X, y, 'smote')
            
            # Save new model
            new_version = self._bump_version()
            model_path = f"{self.models_dir}/model_v{new_version}.pkl"
            joblib.dump(result['model'], model_path)
            
            self.current_model = result['model']
            self.current_model_version = new_version
            
            # Log history
            self.model_history.append({
                'version': new_version,
                'timestamp': datetime.now().isoformat(),
                'accuracy': result['accuracy'],
                'f1': result['f1']
            })
            
            logger.info(f"✅ Model retrained successfully! Version: {new_version}")
            
        except Exception as e:
            logger.error(f"❌ Retraining failed: {e}")
        finally:
            self.is_retraining = False
    
    def _bump_version(self):
        """Increment version number"""
        parts = self.current_model_version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)
    
    def predict(self, features):
        """Make prediction with current model"""
        if self.current_model is None:
            return 0.5  # Default score
        
        try:
            # Convert features to array
            if isinstance(features, dict):
                import numpy as np
                feature_array = np.array([list(features.values())])
            else:
                feature_array = features
            
            prediction = self.current_model.predict_proba(feature_array)[0][1]
            return float(prediction)
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 0.5
    
    def get_model_status(self):
        """Get model status"""
        return {
            'version': self.current_model_version,
            'drift_count': self.drift_detector.drift_count,
            'is_retraining': self.is_retraining,
            'history': self.model_history[-5:]  # Last 5 versions
        }