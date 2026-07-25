"""
Model Evaluation and Comparison
"""
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import matplotlib.pyplot as plt
import seaborn as sns

class Evaluator:
    def __init__(self):
        self.results = {}
    
    def evaluate(self, y_test, y_pred, y_proba=None):
        """
        Evaluate model performance
        """
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }
        
        if y_proba is not None:
            try:
                metrics['auc'] = roc_auc_score(y_test, y_proba, multi_class='ovr')
            except:
                metrics['auc'] = None
        
        return metrics
    
    def compare_models(self, results):
        """
        Compare multiple models
        """
        comparison = pd.DataFrame()
        
        for name, result in results.items():
            metrics = self.evaluate(result['y_test'], result['y_pred'])
            metrics['model'] = name
            comparison = pd.concat([comparison, pd.DataFrame([metrics])], ignore_index=True)
        
        comparison = comparison.set_index('model')
        print("\n📊 **Model Comparison**")
        print("-" * 60)
        print(comparison.round(4))
        print("-" * 60)
        
        # Best model
        best_model = comparison['f1'].idxmax()
        print(f"\n🏆 Best Model: {best_model} (F1: {comparison.loc[best_model, 'f1']:.4f})")
        
        return comparison
    
    def plot_confusion_matrix(self, y_test, y_pred, title="Confusion Matrix"):
        """
        Plot confusion matrix
        """
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title(title)
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png')
        plt.close()
        print("📊 Confusion matrix saved as 'confusion_matrix.png'")
    
    def generate_report(self, results):
        """
        Generate full evaluation report
        """
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'models': {}
        }
        
        for name, result in results.items():
            report['models'][name] = {
                'metrics': self.evaluate(result['y_test'], result['y_pred']),
                'confusion_matrix': confusion_matrix(result['y_test'], result['y_pred']).tolist()
            }
        
        return report