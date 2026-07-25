"""
Data Preprocessing for ML Training
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

class Preprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.imputer = SimpleImputer(strategy='median')
        self.is_fitted = False
    
    def preprocess(self, df):
        """
        Complete preprocessing pipeline
        """
        df = df.copy()
        
        # 1. Handle missing values
        df = df.fillna({
            'response_time': 0.5,
            'bytes_transferred': 1024,
            'failed_attempts': 0,
            'access_count': 1
        })
        
        # 2. Encode categorical variables
        categorical_cols = ['user_id', 'device_id', 'os', 'action', 'status']
        for col in categorical_cols:
            if col in df.columns:
                if not self.is_fitted:
                    self.label_encoders[col] = LabelEncoder()
                    df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[col] = self.label_encoders[col].transform(df[col].astype(str))
        
        # 3. Create target variable (anomaly)
        if 'is_anomaly' not in df.columns:
            df['is_anomaly'] = df['status'].apply(lambda x: 1 if x == 'failed' else 0)
        
        # 4. Feature selection
        feature_cols = [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'access_count', 'failed_attempts', 'success_rate',
            'response_time', 'bytes_transferred', 'is_success',
            'user_access_frequency', 'device_access_frequency',
            'unusual_hour_score', 'location_change_score',
            'port_risk_score', 'os_match_score'
        ]
        
        # Keep only available features
        available_cols = [col for col in feature_cols if col in df.columns]
        
        X = df[available_cols]
        y = df['is_anomaly']
        
        return X, y
    
    def extract_features(self, log):
        """
        Extract features from single log
        """
        # This will be used for real-time feature extraction
        from app.core.feature_engineering import FeatureEngineer
        engineer = FeatureEngineer()
        return engineer.extract_features(log)
    
    def get_feature_names(self):
        return [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'access_count', 'failed_attempts', 'success_rate',
            'response_time', 'bytes_transferred', 'is_success',
            'user_access_frequency', 'device_access_frequency',
            'unusual_hour_score', 'location_change_score',
            'port_risk_score', 'os_match_score'
        ]