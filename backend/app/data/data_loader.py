import pandas as pd
import numpy as np
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """Load data from various sources"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.synthetic_dir = self.data_dir / "synthetic"
        self.cache_dir = self.data_dir / "cache"
        
        # Create directories if they don't exist
        for dir_path in [self.raw_dir, self.processed_dir, self.synthetic_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def load_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Load CSV file"""
        full_path = self.data_dir / file_path
        if not full_path.exists():
            logger.warning(f"File not found: {full_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(full_path, **kwargs)
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return pd.DataFrame()
    
    def load_json(self, file_path: str) -> Dict:
        """Load JSON file"""
        full_path = self.data_dir / file_path
        if not full_path.exists():
            logger.warning(f"File not found: {full_path}")
            return {}
        
        try:
            with open(full_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded data from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    def load_raw_data(self, filename: str = "sample_logs.csv") -> pd.DataFrame:
        """Load raw data"""
        return self.load_csv(f"raw/{filename}")
    
    def load_processed_data(self, filename: str = "features.csv") -> pd.DataFrame:
        """Load processed data"""
        return self.load_csv(f"processed/{filename}")
    
    def load_synthetic_data(self, filename: str = "mixed_logs.csv") -> pd.DataFrame:
        """Load synthetic data"""
        return self.load_csv(f"synthetic/{filename}")
    
    def load_training_data(self) -> pd.DataFrame:
        """Load training data"""
        df = self.load_processed_data("training_data.csv")
        if df.empty:
            df = self.load_synthetic_data("mixed_logs.csv")
        return df
    
    def load_cache(self, key: str) -> Optional[Any]:
        """Load cached data"""
        cache_file = self.cache_dir / f"{key}.pkl"
        if not cache_file.exists():
            return None
        
        try:
            import joblib
            data = joblib.load(cache_file)
            logger.info(f"Loaded cache: {key}")
            return data
        except Exception as e:
            logger.error(f"Error loading cache {key}: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> Dict:
        """Get information about a file"""
        full_path = self.data_dir / file_path
        if not full_path.exists():
            return {"exists": False}
        
        return {
            "exists": True,
            "size_bytes": full_path.stat().st_size,
            "size_mb": full_path.stat().st_size / (1024 * 1024),
            "modified": full_path.stat().st_mtime,
            "name": full_path.name,
            "extension": full_path.suffix
        }
    
    def list_files(self, directory: str = "") -> List[str]:
        """List all files in a directory"""
        target_dir = self.data_dir / directory if directory else self.data_dir
        if not target_dir.exists():
            return []
        
        return [f.name for f in target_dir.iterdir() if f.is_file()]