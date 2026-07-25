"""
Concept Drift Detection using ADWIN
"""
from river import drift
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DriftDetector:
    def __init__(self):
        self.detector = drift.ADWIN()
        self.drift_count = 0
        self.drift_history = []
        self.is_drift_detected = False
    
    def check_drift(self, value):
        """
        Check if drift occurred
        """
        self.detector.update(value)
        
        if self.detector.drift_detected:
            self.is_drift_detected = True
            self.drift_count += 1
            self.drift_history.append({
                'timestamp': datetime.now().isoformat(),
                'drift_number': self.drift_count
            })
            logger.warning(f"⚠️ Concept Drift Detected! (Count: {self.drift_count})")
            self.detector = drift.ADWIN()  # Reset after drift
            return True
        
        return False
    
    def get_drift_history(self):
        """Get drift history"""
        return self.drift_history
    
    def get_stats(self):
        """Get drift statistics"""
        return {
            'total_drifts': self.drift_count,
            'last_drift': self.drift_history[-1]['timestamp'] if self.drift_history else None
        }