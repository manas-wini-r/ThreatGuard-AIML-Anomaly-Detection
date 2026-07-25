import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process and prepare data for training"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        self.target_column = None
        self.is_fitted = False
    
    def preprocess_logs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess log data"""
        df = df.copy()
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Encode categorical variables
        categorical_cols = ['user_id', 'device_id', 'os', 'action', 'status']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].astype('category')
                df[f'{col}_encoded'] = df[col].cat.codes
        
        # Handle missing values
        df = df.fillna(0)
        
        return df
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from logs"""
        features = pd.DataFrame()
        
        # Basic features
        if 'timestamp' in df.columns:
            features['hour'] = df['timestamp'].dt.hour
            features['day_of_week'] = df['timestamp'].dt.dayofweek
            features['is_weekend'] = df['timestamp'].dt.dayofweek.isin([5, 6]).astype(int)
        
        if 'status' in df.columns:
            features['is_success'] = (df['status'] == 'success').astype(int)
            features['failed_attempts'] = (df['status'] == 'failed').astype(int)
        
        # Aggregated features by user
        if 'user_id' in df.columns:
            user_stats = df.groupby('user_id').agg({
                'timestamp': 'count',
                'status': lambda x: (x == 'failed').sum()
            }).rename(columns={
                'timestamp': 'user_access_count',
                'status': 'user_failed_count'
            })
            features = features.join(user_stats, on='user_id', how='left')
        
        # Aggregated features by device
        if 'device_id' in df.columns:
            device_stats = df.groupby('device_id').agg({
                'timestamp': 'count'
            }).rename(columns={'timestamp': 'device_access_count'})
            features = features.join(device_stats, on='device_id', how='left')
        
        # Fill NaN values
        features = features.fillna(0)
        
        return features
    
    def normalize_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Normalize features"""
        if not self.is_fitted:
            self.scaler.fit(X)
            self.is_fitted = True
        
        X_scaled = self.scaler.transform(X)
        return pd.DataFrame(X_scaled, columns=X.columns)
    
    def prepare_training_data(self, df: pd.DataFrame, target_col: str = 'is_anomaly') -> Tuple:
        """Prepare data for training"""
        df_processed = self.preprocess_logs(df)
        X = self.extract_features(df_processed)
        
        if target_col in df_processed.columns:
            y = df_processed[target_col]
        else:
            y = None
        
        self.feature_columns = X.columns.tolist()
        self.target_column = target_col
        
        return X, y
    
    def split_data(self, X: pd.DataFrame, y: pd.Series = None, 
                   test_size: float = 0.2, random_state: int = 42) -> Tuple:
        """Split data into train and test sets"""
        if y is not None:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
            return X_train, X_test, y_train, y_test
        else:
            train_size = int(len(X) * (1 - test_size))
            indices = np.random.permutation(len(X))
            train_indices = indices[:train_size]
            test_indices = indices[train_size:]
            
            X_train = X.iloc[train_indices]
            X_test = X.iloc[test_indices]
            
            return X_train, X_test, None, None
    
    def create_sequence_data(self, df: pd.DataFrame, sequence_length: int = 10) -> np.ndarray:
        """Create sequence data for time series models"""
        sequences = []
        
        for i in range(len(df) - sequence_length + 1):
            seq = df.iloc[i:i+sequence_length].values
            sequences.append(seq)
        
        return np.array(sequences)
    
    def get_feature_importance(self, model, X: pd.DataFrame) -> pd.DataFrame:
        """Get feature importance from trained model"""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importance = model.coef_[0]
        else:
            return pd.DataFrame()
        
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return feature_importance