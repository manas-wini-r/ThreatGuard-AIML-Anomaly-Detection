"""
Train the Attack Classifier
Run this script to train the attack classifier model
"""

import sys
import os
import pandas as pd
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from ml.attack_classifier import AttackClassifier
from app.data.generator import DataGenerator
from app.core.feature_engineering import FeatureEngineer

def train_attack_classifier():
    """Train the attack classifier"""
    print("🚀 Training Attack Classifier...")
    print("=" * 50)
    
    # Generate training data
    print("📊 Generating training data...")
    gen = DataGenerator()
    
    # Generate logs with more anomalies for better training
    logs = []
    for _ in range(10):  # Generate in batches to get more variety
        batch = gen.generate_batch(500, anomaly_rate=0.3)
        logs.extend(batch)
    
    print(f"   Generated {len(logs)} logs")
    
    # Convert to DataFrame
    df = pd.DataFrame(logs)
    print(f"   DataFrame shape: {df.shape}")
    
    # Extract features
    print("🔍 Extracting features...")
    engineer = FeatureEngineer()
    
    # Extract features one by one to avoid errors
    features_list = []
    for idx, log in enumerate(logs):
        try:
            features = engineer.extract_features(log)
            features_list.append(features)
        except Exception as e:
            print(f"   Error on log {idx}: {e}")
            continue
    
    # Convert to DataFrame
    X = pd.DataFrame(features_list)
    print(f"   Extracted features shape: {X.shape}")
    
    if X.empty:
        print("❌ No features extracted! Check the data format.")
        return
    
    # Create labels based on log patterns
    print("🏷️ Creating labels...")
    y = []
    for log in logs:
        # Check for different attack types
        if log.get('failed_attempts', 0) > 5:
            y.append('brute_force')
        elif 'previous_location' in log and 'current_location' in log:
            y.append('impossible_travel')
        elif log.get('destination_port', 0) in [22, 3389, 445, 135]:
            y.append('lateral_movement')
        elif log.get('os') != log.get('device_os'):
            y.append('device_spoofing')
        elif log.get('hour', 12) in [0, 1, 2, 3, 4]:
            y.append('credential_misuse')
        else:
            y.append('normal')
    
    # Make sure y matches X length
    y = y[:len(X)]
    
    # Count labels
    unique, counts = np.unique(y, return_counts=True)
    print("   Label distribution:")
    for label, count in zip(unique, counts):
        print(f"      {label}: {count}")
    
    # Check if we have enough data
    if len(X) < 10:
        print("❌ Not enough data to train! Need at least 10 samples.")
        return
    
    # Train classifier
    print("\n🧠 Training classifier...")
    classifier = AttackClassifier()
    classifier.train(X, y)
    
    print("\n✅ Attack Classifier trained successfully!")
    print("   Model saved to: ml_models/attack_classifier.pkl")
    print("   Label encoder saved to: ml_models/attack_label_encoder.pkl")
    print("=" * 50)

if __name__ == "__main__":
    train_attack_classifier()