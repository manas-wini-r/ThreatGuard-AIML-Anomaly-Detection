import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import random

class FeatureEngineer:
    def __init__(self):
        self.feature_names = [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'access_count', 'failed_attempts', 'success_rate',
            'response_time', 'bytes_transferred', 'is_success',
            'user_access_frequency', 'device_access_frequency',
            'unusual_hour_score', 'location_change_score',
            'port_risk_score', 'os_match_score'
        ]
        # Cache for user/device frequencies
        self.user_frequency_cache = {}
        self.device_frequency_cache = {}
    
    def extract_features(self, log: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from a log entry"""
        features = {}
        
        # Time-based features
        timestamp = log.get('timestamp', datetime.now().isoformat())
        if isinstance(timestamp, str):
            try:
                # Handle different timestamp formats
                timestamp = timestamp.replace('Z', '+00:00')
                dt = datetime.fromisoformat(timestamp)
            except:
                try:
                    # Try parsing with pandas
                    dt = pd.to_datetime(timestamp)
                except:
                    dt = datetime.now()
        else:
            dt = timestamp
            
        features['hour'] = float(dt.hour)
        features['day_of_week'] = float(dt.weekday())
        features['month'] = float(dt.month)
        features['is_weekend'] = 1.0 if dt.weekday() >= 5 else 0.0
        
        # Access patterns
        features['access_count'] = float(log.get('access_count', 1))
        features['failed_attempts'] = float(log.get('failed_attempts', 0))
        
        # Success rate (0-1)
        total = features['access_count'] + features['failed_attempts']
        features['success_rate'] = features['access_count'] / max(total, 1.0)
        
        # Performance metrics
        features['response_time'] = float(log.get('response_time', 0.5))
        features['bytes_transferred'] = float(log.get('bytes_transferred', 1024))
        features['is_success'] = 1.0 if log.get('status') == 'success' else 0.0
        
        # Behavioral features
        features['user_access_frequency'] = self._get_user_frequency(log.get('user_id', ''))
        features['device_access_frequency'] = self._get_device_frequency(log.get('device_id', ''))
        
        # Risk scores
        features['unusual_hour_score'] = self._calculate_unusual_hour_score(features['hour'])
        features['location_change_score'] = self._calculate_location_score(log)
        features['port_risk_score'] = self._calculate_port_risk(log.get('destination_port', 0))
        features['os_match_score'] = self._calculate_os_match(log)
        
        return features
    
    def _get_user_frequency(self, user_id: str) -> float:
        """Calculate user access frequency"""
        if not user_id:
            return 0.5
        if user_id not in self.user_frequency_cache:
            # Generate consistent random value for user
            random.seed(hash(user_id) % 1000)
            self.user_frequency_cache[user_id] = random.uniform(0.1, 1.0)
        return self.user_frequency_cache[user_id]
    
    def _get_device_frequency(self, device_id: str) -> float:
        """Calculate device access frequency"""
        if not device_id:
            return 0.5
        if device_id not in self.device_frequency_cache:
            # Generate consistent random value for device
            random.seed(hash(device_id) % 1000)
            self.device_frequency_cache[device_id] = random.uniform(0.1, 1.0)
        return self.device_frequency_cache[device_id]
    
    def _calculate_unusual_hour_score(self, hour: float) -> float:
        """Calculate score for unusual access hours"""
        hour_int = int(hour)
        unusual_hours = [0, 1, 2, 3, 4, 23]
        if hour_int in unusual_hours:
            return 1.0
        elif hour_int < 6 or hour_int > 22:
            return 0.7
        else:
            return 0.1
    
    def _calculate_location_score(self, log: Dict) -> float:
        """Calculate location change risk score"""
        if 'previous_location' in log and 'current_location' in log:
            prev = log['previous_location']
            curr = log['current_location']
            if prev != curr:
                return 0.8
        return 0.1
    
    def _calculate_port_risk(self, port: int) -> float:
        """Calculate risk score for network ports"""
        if port is None:
            return 0.1
        risky_ports = [22, 23, 135, 139, 445, 3389, 5900, 8080, 8443]
        if port in risky_ports:
            return 0.9
        elif 1 <= port <= 1024:
            return 0.5
        else:
            return 0.1
    
    def _calculate_os_match(self, log: Dict) -> float:
        """Calculate OS match score"""
        if 'os' in log and 'device_os' in log:
            if log['os'] == log['device_os']:
                return 0.1
            else:
                return 0.9
        return 0.5
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalize features to [0, 1] range"""
        normalized = {}
        for key, value in features.items():
            if key in ['hour']:
                normalized[key] = value / 24.0
            elif key in ['day_of_week']:
                normalized[key] = value / 7.0
            elif key in ['month']:
                normalized[key] = value / 12.0
            elif key == 'is_weekend':
                normalized[key] = float(value)
            elif key in ['access_count', 'failed_attempts']:
                normalized[key] = min(value / 100.0, 1.0)
            elif key == 'success_rate':
                normalized[key] = value
            elif key == 'response_time':
                normalized[key] = min(value / 5.0, 1.0)
            elif key == 'bytes_transferred':
                normalized[key] = min(value / (1024*1024*10), 1.0)
            else:
                normalized[key] = min(max(value, 0.0), 1.0)
        return normalized
    
    def extract_batch(self, logs: List[Dict]) -> pd.DataFrame:
        """Extract features from a batch of logs"""
        features_list = []
        for log in logs:
            try:
                features = self.extract_features(log)
                features_list.append(features)
            except Exception as e:
                print(f"Error extracting features from log: {e}")
                # Add default features
                default_features = {name: 0.0 for name in self.feature_names}
                features_list.append(default_features)
        
        return pd.DataFrame(features_list)