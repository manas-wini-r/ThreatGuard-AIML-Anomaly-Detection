import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import random
import math

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
        self.user_frequency_cache = {}
        self.device_frequency_cache = {}
    
    def extract_features(self, log: Dict[str, Any]) -> Dict[str, float]:
        features = {}
        
        timestamp = log.get('timestamp', datetime.now().isoformat())
        if isinstance(timestamp, str):
            try:
                timestamp = timestamp.replace('Z', '+00:00')
                dt = datetime.fromisoformat(timestamp)
            except:
                try:
                    dt = pd.to_datetime(timestamp)
                except:
                    dt = datetime.now()
        else:
            dt = timestamp
            
        features['hour'] = float(dt.hour)
        features['day_of_week'] = float(dt.weekday())
        features['month'] = float(dt.month)
        features['is_weekend'] = 1.0 if dt.weekday() >= 5 else 0.0
        
        features['access_count'] = float(log.get('access_count', 1))
        features['failed_attempts'] = float(log.get('failed_attempts', 0))
        
        total = features['access_count'] + features['failed_attempts']
        features['success_rate'] = features['access_count'] / max(total, 1.0)
        
        features['response_time'] = float(log.get('response_time', 0.5))
        features['bytes_transferred'] = float(log.get('bytes_transferred', 1024))
        features['is_success'] = 1.0 if log.get('status') == 'success' else 0.0
        
        features['user_access_frequency'] = self._get_user_frequency(log.get('user_id', ''))
        features['device_access_frequency'] = self._get_device_frequency(log.get('device_id', ''))
        
        features['unusual_hour_score'] = self._calculate_unusual_hour_score(features['hour'])
        features['location_change_score'] = self._calculate_location_score(log)
        features['port_risk_score'] = self._calculate_port_risk(log.get('destination_port', 0))
        features['os_match_score'] = self._calculate_os_match(log)
        
        return features
    
    def extract_enhanced_features(self, log: Dict[str, Any]) -> Dict[str, float]:
        features = {}
        
        timestamp = log.get('timestamp', datetime.now().isoformat())
        if isinstance(timestamp, str):
            try:
                timestamp = timestamp.replace('Z', '+00:00')
                dt = datetime.fromisoformat(timestamp)
            except:
                try:
                    dt = pd.to_datetime(timestamp)
                except:
                    dt = datetime.now()
        else:
            dt = timestamp
            
        features['hour'] = float(dt.hour)
        features['day_of_week'] = float(dt.weekday())
        features['month'] = float(dt.month)
        features['is_weekend'] = 1.0 if dt.weekday() >= 5 else 0.0
        features['is_holiday'] = self._is_holiday(dt)
        features['hour_category'] = self._get_hour_category(dt.hour)
        features['login_hour'] = float(dt.hour)
        
        features['access_count'] = float(log.get('access_count', 1))
        features['failed_attempts'] = float(log.get('failed_attempts', 0))
        features['success_rate'] = features['access_count'] / max(features['access_count'] + features['failed_attempts'], 1)
        features['failed_login_streak'] = float(log.get('failed_login_streak', 0))
        features['access_velocity'] = float(log.get('login_velocity', 0.5))
        features['time_since_last_login'] = float(log.get('time_since_last_login', 24))
        
        features['response_time'] = float(log.get('response_time', 0.5))
        features['bytes_transferred'] = float(log.get('bytes_transferred', 1024))
        features['session_duration'] = float(log.get('session_duration', 0))
        
        features['user_access_frequency'] = self._get_user_frequency(log.get('user_id', ''))
        features['device_access_frequency'] = self._get_device_frequency(log.get('device_id', ''))
        features['privilege_level'] = float(log.get('privilege_level', 1))
        features['department'] = self._get_department_score(log.get('department', ''))
        features['resource_sensitivity'] = float(log.get('resource_sensitivity', 1))
        
        features['device_age'] = self._get_device_age(log.get('device_id', ''))
        features['device_trust_score'] = self._get_device_trust(log.get('device_id', ''))
        features['os_match_score'] = self._calculate_os_match(log)
        features['os_fingerprint'] = self._get_os_fingerprint(log)
        features['browser_fingerprint'] = float(log.get('browser_fingerprint', 0.5))
        
        features['ip_reputation'] = self._get_ip_reputation(log.get('ip', ''))
        features['geo_distance'] = self._calculate_geo_distance(log)
        features['location_change_score'] = self._calculate_location_score(log)
        features['port_risk_score'] = self._calculate_port_risk(log.get('destination_port', 0))
        
        features['mfa_enabled'] = 1.0 if log.get('mfa_enabled', False) else 0.0
        features['is_success'] = 1.0 if log.get('status') == 'success' else 0.0
        features['credential_misuse_score'] = self._calculate_credential_misuse(log)
        
        features['unusual_hour_score'] = self._calculate_unusual_hour_score(features['hour'])
        features['behavioral_anomaly_score'] = self._calculate_behavioral_score(log)
        
        features['risk_combined'] = (
            features['unusual_hour_score'] * 0.2 +
            features['location_change_score'] * 0.3 +
            features['port_risk_score'] * 0.2 +
            features['ip_reputation'] * 0.3
        )
        
        return features
    
    def _get_user_frequency(self, user_id: str) -> float:
        if not user_id:
            return 0.5
        if user_id not in self.user_frequency_cache:
            random.seed(hash(user_id) % 1000)
            self.user_frequency_cache[user_id] = random.uniform(0.1, 1.0)
        return self.user_frequency_cache[user_id]
    
    def _get_device_frequency(self, device_id: str) -> float:
        if not device_id:
            return 0.5
        if device_id not in self.device_frequency_cache:
            random.seed(hash(device_id) % 1000)
            self.device_frequency_cache[device_id] = random.uniform(0.1, 1.0)
        return self.device_frequency_cache[device_id]
    
    def _calculate_unusual_hour_score(self, hour: float) -> float:
        hour_int = int(hour)
        unusual_hours = [0, 1, 2, 3, 4, 23]
        if hour_int in unusual_hours:
            return 1.0
        elif hour_int < 6 or hour_int > 22:
            return 0.7
        else:
            return 0.1
    
    def _calculate_location_score(self, log: Dict) -> float:
        if 'previous_location' in log and 'current_location' in log:
            prev = log['previous_location']
            curr = log['current_location']
            if prev != curr:
                return 0.8
        return 0.1
    
    def _calculate_port_risk(self, port: int) -> float:
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
        if 'os' in log and 'device_os' in log:
            if log['os'] == log['device_os']:
                return 0.1
            else:
                return 0.9
        return 0.5
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
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
        features_list = []
        for log in logs:
            try:
                features = self.extract_features(log)
                features_list.append(features)
            except Exception as e:
                print(f"Error extracting features from log: {e}")
                default_features = {name: 0.0 for name in self.feature_names}
                features_list.append(default_features)
        
        return pd.DataFrame(features_list)
    
    # ===== ENHANCED FEATURES HELPER METHODS =====
    
    def _is_holiday(self, dt) -> float:
        holidays = [(1, 1), (7, 4), (12, 25)]
        return 1.0 if (dt.month, dt.day) in holidays else 0.0
    
    def _get_hour_category(self, hour: float) -> float:
        hour_int = int(hour)
        if 6 <= hour_int < 12:
            return 0.0
        elif 12 <= hour_int < 17:
            return 1.0
        elif 17 <= hour_int < 22:
            return 2.0
        else:
            return 3.0
    
    def _get_department_score(self, department: str) -> float:
        dept_scores = {
            'IT': 0.8, 'HR': 0.3, 'Finance': 0.9,
            'Executive': 1.0, 'Engineering': 0.7,
            'Sales': 0.4, 'Marketing': 0.3
        }
        return dept_scores.get(department, 0.5)
    
    def _get_device_age(self, device_id: str) -> float:
        if not device_id:
            return 12.0
        random.seed(hash(device_id) % 1000)
        return random.uniform(1, 36)
    
    def _get_device_trust(self, device_id: str) -> float:
        if not device_id:
            return 0.5
        random.seed(hash(device_id) % 1000)
        return random.uniform(0.3, 0.9)
    
    def _get_os_fingerprint(self, log: Dict) -> float:
        known_os = ['Windows', 'MacOS', 'Linux', 'iOS', 'Android']
        os_fingerprints = {os: i/len(known_os) for i, os in enumerate(known_os)}
        return os_fingerprints.get(log.get('os', 'Unknown'), 0.5)
    
    def _get_ip_reputation(self, ip: str) -> float:
        if not ip:
            return 0.1
        suspicious_ips = ['192.168.1.100', '10.0.0.1', '172.16.0.1']
        return 0.9 if ip in suspicious_ips else 0.1
    
    def _calculate_geo_distance(self, log: Dict) -> float:
        if 'previous_location' in log and 'current_location' in log:
            prev = log['previous_location']
            curr = log['current_location']
            lat1 = prev.get('lat', 0)
            lon1 = prev.get('lon', 0)
            lat2 = curr.get('lat', 0)
            lon2 = curr.get('lon', 0)
            distance = math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
            return min(distance * 111, 1.0)
        return 0.0
    
    def _calculate_credential_misuse(self, log: Dict) -> float:
        score = 0.0
        if log.get('failed_attempts', 0) > 3:
            score += 0.5
        if log.get('hour', 12) in [0, 1, 2, 3, 4]:
            score += 0.3
        if log.get('location_change_score', 0) > 0.5:
            score += 0.2
        return min(score, 1.0)
    
    def _calculate_behavioral_score(self, log: Dict) -> float:
        features = self.extract_features(log)
        score = (
            features.get('unusual_hour_score', 0) * 0.2 +
            features.get('location_change_score', 0) * 0.3 +
            features.get('failed_attempts', 0) / 10 * 0.3 +
            (1 - features.get('success_rate', 1)) * 0.2
        )
        return min(score, 1.0)