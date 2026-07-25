"""
Model Training with Class Imbalance Handling
SMOTE, ADASYN, RandomUnderSampler, Class Weights
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, recall_score, precision_score
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek
import joblib
import os
import json
from datetime import datetime

class ModelTrainer:
    def __init__(self):
        self.models = {}
        self.results = {}
        self.samplers = {
            'smote': SMOTE(random_state=42),
            'adasyn': ADASYN(random_state=42),
            'undersample': RandomUnderSampler(random_state=42),
            'smote_tomek': SMOTETomek(random_state=42),
            'none': None
        }
        self.best_model = None
        self.best_sampler = None
        
    def train_with_sampling(self, X, y, sampler_name='smote', use_class_weights=True):
        """
        Train model with different sampling techniques and class weights
        """
        print(f"🔄 Training with {sampler_name}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Count original distribution
        print(f"   Original: {np.bincount(y_train)}")
        
        # Apply sampling
        if sampler_name != 'none' and sampler_name in self.samplers:
            sampler = self.samplers[sampler_name]
            X_train_resampled, y_train_resampled = sampler.fit_resample(X_train, y_train)
            print(f"   Resampled: {np.bincount(y_train_resampled)}")
        else:
            X_train_resampled, y_train_resampled = X_train, y_train
        
        # Calculate class weights
        if use_class_weights:
            from sklearn.utils.class_weight import compute_class_weight
            classes = np.unique(y_train_resampled)
            weights = compute_class_weight('balanced', classes=classes, y=y_train_resampled)
            class_weight_dict = dict(zip(classes, weights))
            print(f"   Class Weights: {class_weight_dict}")
        else:
            class_weight_dict = None
        
        # Train Random Forest with class weights
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight=class_weight_dict,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_resampled, y_train_resampled)
        
        # Evaluate
        y_pred = model.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }
        
        # Cross-validation score
        cv_scores = cross_val_score(model, X_train_resampled, y_train_resampled, cv=5)
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        print(f"   ✅ Accuracy: {metrics['accuracy']:.4f}")
        print(f"   ✅ F1 Score: {metrics['f1']:.4f}")
        print(f"   ✅ CV Mean: {metrics['cv_mean']:.4f}")
        
        return {
            'model': model,
            'metrics': metrics,
            'y_pred': y_pred,
            'y_test': y_test,
            'sampler': sampler_name,
            'class_weights_used': use_class_weights
        }
    
    def compare_samplers(self, X, y):
        """
        Compare all sampling techniques
        """
        results = {}
        
        for sampler_name in ['none', 'smote', 'adasyn', 'undersample', 'smote_tomek']:
            print("=" * 50)
            results[sampler_name] = self.train_with_sampling(X, y, sampler_name)
        
        # Print comparison
        print("\n" + "=" * 60)
        print("📊 **SAMPLING TECHNIQUE COMPARISON**")
        print("=" * 60)
        print(f"{'Sampler':<15} {'Accuracy':<12} {'F1 Score':<12} {'CV Mean':<12}")
        print("-" * 60)
        
        for name, result in results.items():
            m = result['metrics']
            print(f"{name:<15} {m['accuracy']:.4f}     {m['f1']:.4f}     {m['cv_mean']:.4f}")
        
        print("-" * 60)
        
        # Best sampler
        best = max(results, key=lambda x: results[x]['metrics']['f1'])
        print(f"\n🏆 Best Sampler: {best} with F1 = {results[best]['metrics']['f1']:.4f}")
        
        self.results = results
        self.models = {name: result['model'] for name, result in results.items()}
        self.best_model = results[best]['model']
        self.best_sampler = best
        
        # Save best model
        self.save_model(results[best]['model'], f"best_model_{best}.pkl")
        
        # Save results
        self.save_results(results)
        
        return results
    
    def save_model(self, model, filename):
        """Save model to disk"""
        os.makedirs('ml_models', exist_ok=True)
        joblib.dump(model, f'ml_models/{filename}')
        print(f"💾 Saved: ml_models/{filename}")
    
    def save_results(self, results):
        """Save training results"""
        os.makedirs('ml_models', exist_ok=True)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'best_sampler': self.best_sampler,
            'results': {}
        }
        
        for name, result in results.items():
            report['results'][name] = {
                'metrics': result['metrics'],
                'sampler': result['sampler'],
                'class_weights_used': result['class_weights_used']
            }
        
        with open('ml_models/training_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"💾 Saved: ml_models/training_report.json")
    
    def load_model(self, filename):
        """Load model from disk"""
        return joblib.load(f'ml_models/{filename}')