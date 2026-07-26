import pandas as pd
import numpy as np
import os
import json
import joblib
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataSaver:
    """Save data to various formats with schema support"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.synthetic_dir = self.data_dir / "synthetic"
        self.models_dir = self.data_dir / "models"
        self.cache_dir = self.data_dir / "cache"
        
        for dir_path in [self.raw_dir, self.processed_dir, self.synthetic_dir, 
                        self.models_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_csv(self, df: pd.DataFrame, file_path: str, **kwargs) -> bool:
        """Save DataFrame to CSV"""
        try:
            full_path = self.data_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_csv(full_path, index=False, **kwargs)
            logger.info(f"Saved {len(df)} rows to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            return False
    
    def save_json(self, data: Dict, file_path: str) -> bool:
        """Save data to JSON"""
        try:
            full_path = self.data_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved data to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            return False
    
    def save_raw_data(self, df: pd.DataFrame, filename: str = "sample_logs.csv") -> bool:
        """Save raw data"""
        return self.save_csv(df, f"raw/{filename}")
    
    def save_processed_data(self, df: pd.DataFrame, filename: str = "features.csv") -> bool:
        """Save processed data"""
        return self.save_csv(df, f"processed/{filename}")
    
    def save_synthetic_data(self, df: pd.DataFrame, filename: str = "mixed_logs.csv") -> bool:
        """Save synthetic data"""
        return self.save_csv(df, f"synthetic/{filename}")
    
    def save_model(self, model: Any, filename: str) -> bool:
        """Save trained model"""
        try:
            full_path = self.models_dir / filename
            joblib.dump(model, full_path)
            logger.info(f"Saved model to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving model {filename}: {e}")
            return False
    
    def save_cache(self, data: Any, key: str) -> bool:
        """Save data to cache"""
        try:
            cache_file = self.cache_dir / f"{key}.pkl"
            joblib.dump(data, cache_file)
            logger.info(f"Saved cache: {key}")
            return True
        except Exception as e:
            logger.error(f"Error saving cache {key}: {e}")
            return False
    
    def save_feature_stats(self, stats: Dict, filename: str = "feature_stats.json") -> bool:
        """Save feature statistics"""
        return self.save_json(stats, f"processed/{filename}")
    
    def save_training_metadata(self, metadata: Dict) -> bool:
        """Save training metadata"""
        metadata['timestamp'] = datetime.now().isoformat()
        return self.save_json(metadata, "models/training_metadata.json")
    
    def save_schema_info(self, df: pd.DataFrame, filename: str = "schema_info.json") -> bool:
        """Save schema information"""
        schema_info = {
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'row_count': len(df),
            'timestamp': datetime.now().isoformat()
        }
        return self.save_json(schema_info, f"processed/{filename}")