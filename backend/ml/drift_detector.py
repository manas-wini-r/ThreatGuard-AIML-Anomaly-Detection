"""
Concept Drift Detection using River + ADWIN
Automatic Retraining Trigger
"""
from river import drift
import numpy as np
import logging
from datetime import datetime
import json
import os
import asyncio

logger = logging.getLogger(__name__)

class DriftDetector:
    def __init__(self):
        self.detector = drift.ADWIN()
        self.drift_count = 0
        self.drift_history = []
        self.is_drift_detected = False
        self.drift_threshold = 0.05  # 5% change triggers drift
        self.retraining_in_progress = False
        self.retraining_history = []
        
    def check_drift(self, prediction_score, true_label=None):
        """
        Check if concept drift occurred
        """
        # Update detector with prediction score
        self.detector.update(prediction_score)
        
        if self.detector.drift_detected:
            self.is_drift_detected = True
            self.drift_count += 1
            self.drift_history.append({
                'timestamp': datetime.now().isoformat(),
                'drift_number': self.drift_count,
                'score': prediction_score,
                'true_label': true_label
            })
            logger.warning(f"⚠️ CONCEPT DRIFT DETECTED! (Count: {self.drift_count})")
            
            # Trigger retraining
            asyncio.create_task(self.trigger_retraining())
            
            # Reset detector after drift
            self.detector = drift.ADWIN()
            return True
        
        return False
    
    async def trigger_retraining(self):
        """
        Trigger automatic retraining
        """
        if self.retraining_in_progress:
            logger.info("⚠️ Retraining already in progress")
            return
        
        self.retraining_in_progress = True
        logger.info("🔄 Starting automatic retraining due to concept drift...")
        
        try:
            # Import here to avoid circular imports
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
            
            # Retrain
            trainer = ModelTrainer()
            result = trainer.train_with_sampling(X, y, 'smote')
            
            # Save new model
            self.retraining_history.append({
                'timestamp': datetime.now().isoformat(),
                'drift_number': self.drift_count,
                'new_accuracy': result['metrics']['accuracy'],
                'new_f1': result['metrics']['f1']
            })
            
            logger.info(f"✅ Retraining complete! New F1: {result['metrics']['f1']:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Retraining failed: {e}")
        finally:
            self.retraining_in_progress = False
    
    def get_drift_stats(self):
        """Get drift statistics"""
        return {
            'total_drifts': self.drift_count,
            'last_drift': self.drift_history[-1] if self.drift_history else None,
            'retraining_in_progress': self.retraining_in_progress,
            'retraining_history': self.retraining_history[-5:]  # Last 5 retrainings
        }
    
    def get_drift_history(self):
        """Get drift history"""
        return self.drift_history
    
    def reset(self):
        """Reset drift detector"""
        self.detector = drift.ADWIN()
        self.is_drift_detected = False
        logger.info("🔄 Drift detector reset")