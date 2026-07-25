import numpy as np
from typing import List, Dict, Any
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

class MetricsCalculator:
    @staticmethod
    def calculate_metrics(y_true: List[int], y_pred: List[int], y_scores: List[float]) -> Dict[str, float]:
        """Calculate various performance metrics"""
        metrics = {}
        
        # Basic metrics
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
        metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)
        metrics['f1'] = f1_score(y_true, y_pred, zero_division=0)
        
        # AUC if scores available
        if len(np.unique(y_true)) == 2 and y_scores:
            try:
                metrics['auc'] = roc_auc_score(y_true, y_scores)
            except:
                metrics['auc'] = 0.5
        
        return metrics
    
    @staticmethod
    def confusion_matrix_stats(y_true: List[int], y_pred: List[int]) -> Dict[str, int]:
        """Calculate confusion matrix statistics"""
        tp = np.sum((np.array(y_true) == 1) & (np.array(y_pred) == 1))
        fp = np.sum((np.array(y_true) == 0) & (np.array(y_pred) == 1))
        tn = np.sum((np.array(y_true) == 0) & (np.array(y_pred) == 0))
        fn = np.sum((np.array(y_true) == 1) & (np.array(y_pred) == 0))
        
        return {
            'true_positives': int(tp),
            'false_positives': int(fp),
            'true_negatives': int(tn),
            'false_negatives': int(fn)
        }