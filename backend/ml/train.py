"""
Model Training with Class Imbalance Handling
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler
import joblib
import os

class ModelTrainer:
    def __init__(self):
        self.models = {}
        self.results = {}
        self.samplers = {
            'smote': SMOTE(random_state=42),
            'adasyn': ADASYN(random_state=42),
            'undersample': RandomUnderSampler(random_state=42),
            'none': None
        }
    
    def train_with_sampling(self, X, y, sampler_name='smote'):
        """
        Train model with different sampling techniques
        """
        print(f"🔄 Training with {sampler_name}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Apply sampling
        if sampler_name != 'none' and sampler_name in self.samplers:
            sampler = self.samplers[sampler_name]
            X_train_resampled, y_train_resampled = sampler.fit_resample(X_train, y_train)
            print(f"   Original: {np.bincount(y_train)}")
            print(f"   Resampled: {np.bincount(y_train_resampled)}")
        else:
            X_train_resampled, y_train_resampled = X_train, y_train
        
        # Train model with class weights
        model = RandomForestClassifier(
            n_estimators=100,
            class_weight='balanced',
            random_state=42
        )
        model.fit(X_train_resampled, y_train_resampled)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        print(f"   ✅ Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        
        return {
            'model': model,
            'accuracy': accuracy,
            'f1': f1,
            'y_pred': y_pred,
            'y_test': y_test,
            'sampler': sampler_name
        }
    
    def compare_samplers(self, X, y):
        """
        Compare all sampling techniques
        """
        results = {}
        
        for sampler_name in ['none', 'smote', 'adasyn', 'undersample']:
            results[sampler_name] = self.train_with_sampling(X, y, sampler_name)
            print("-" * 40)
        
        # Print comparison
        print("\n📊 **Sampling Comparison**")
        print("-" * 50)
        print(f"{'Sampler':<15} {'Accuracy':<12} {'F1 Score':<12}")
        print("-" * 50)
        for name, result in results.items():
            print(f"{name:<15} {result['accuracy']:.4f}     {result['f1']:.4f}")
        print("-" * 50)
        
        # Best sampler
        best = max(results, key=lambda x: results[x]['f1'])
        print(f"\n🏆 Best Sampler: {best} with F1 = {results[best]['f1']:.4f}")
        
        self.results = results
        self.models = {name: result['model'] for name, result in results.items()}
        
        # Save best model
        self.save_model(results[best]['model'], f"best_model_{best}.pkl")
        
        return results
    
    def save_model(self, model, filename):
        """Save model to disk"""
        os.makedirs('ml_models', exist_ok=True)
        joblib.dump(model, f'ml_models/{filename}')
        print(f"💾 Saved: ml_models/{filename}")
    
    def load_model(self, filename):
        """Load model from disk"""
        return joblib.load(f'ml_models/{filename}')