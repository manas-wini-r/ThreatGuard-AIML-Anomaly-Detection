import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict
import json
import math

from app.core.feature_engineering import FeatureEngineer
from app.core.profile_manager import ProfileManager
from app.models.ensemble import EnsembleDetector
from app.utils.explainability import Explainer

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.feature_engineer = FeatureEngineer()
        self.explainer = Explainer()
        self.ensemble = EnsembleDetector()
        self.profile_manager = ProfileManager()
        
        # Behavioral baselines
        self.user_baselines = defaultdict(dict)
        self.device_baselines = defaultdict(dict)
        self.access_patterns = defaultdict(list)
        
        # Real-time buffer
        self.buffer = []
        self.buffer_size = 1000
        
        # Threat detection rules
        self.threat_rules = {
            'brute_force': {'threshold': 3, 'time_window': 60},  # Lowered from 5 to 3
            'impossible_travel': {'max_speed': 800},
            'lateral_movement': {'suspicious_ports': [22, 3389, 445, 135, 1433, 3306]},
            'credential_misuse': {'unusual_hours': [0, 1, 2, 3, 4, 23]},
            'device_spoofing': {'os_mismatch': True}
        }
        
    async def process_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single log entry"""
        try:
            # Extract features
            features = self.feature_engineer.extract_features(log)
            
            # Update behavioral baselines
            self._update_baselines(log, features)
            
            # Detect anomaly with lower threshold
            anomaly_score = self._detect_anomaly(features, log)
            
            # DEBUG: Print score for suspicious logs
            if anomaly_score > 0.3:
                logger.info(f"🔍 Anomaly Score: {anomaly_score:.3f} for user {log.get('user_id')}")
            
            # Lower threshold from 0.7 to 0.4
            if anomaly_score > 0.4:
                # Classify threat type
                threat_type = self._classify_threat(log, features)
                
                # Generate explanation
                explanation = self.explainer.explain_anomaly(
                    log, features, anomaly_score, threat_type
                )
                
                # Calculate risk score (0-100)
                risk_score = anomaly_score * 100
                
                # Create alert
                alert = self._create_alert(log, risk_score, threat_type, explanation)
                logger.info(f"🚨 ALERT: {threat_type} - Score: {anomaly_score:.3f}")
                return alert
            
            return {'status': 'normal', 'log': log}
            
        except Exception as e:
            logger.error(f"Error processing log: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def process_real_time(self, data: str) -> Dict[str, Any]:
        """Process real-time WebSocket data"""
        try:
            log = json.loads(data)
            return await self.process_log(log)
        except Exception as e:
            logger.error(f"Error processing real-time data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _update_baselines(self, log: Dict, features: Dict):
        """Update behavioral baselines"""
        user = log.get('user_id')
        device = log.get('device_id')
        
        if user:
            if 'hour' in features:
                if 'hours' not in self.user_baselines[user]:
                    self.user_baselines[user]['hours'] = []
                self.user_baselines[user]['hours'].append(features['hour'])
                
            if 'failed_attempts' in features:
                if 'failures' not in self.user_baselines[user]:
                    self.user_baselines[user]['failures'] = []
                self.user_baselines[user]['failures'].append(features['failed_attempts'])
        
        if device:
            if 'os' in log:
                self.device_baselines[device]['os'] = log['os']
            if 'ip' in log:
                self.device_baselines[device]['ip'] = log['ip']
    
    def _detect_anomaly(self, features: Dict, log: Dict) -> float:
        """Detect anomaly using ensemble of methods"""
        scores = []
        
        # 1. Statistical anomaly detection
        stat_score = self._statistical_anomaly_score(features, log)
        scores.append(stat_score)
        
        # 2. Rule-based detection
        rule_score = self._rule_based_score(log)
        scores.append(rule_score)
        
        # 3. Behavioral deviation
        behavior_score = self._behavioral_deviation_score(features, log)
        scores.append(behavior_score)
        
        # 4. ML ensemble score (if available)
        try:
            if self.ensemble and hasattr(self.ensemble, 'predict'):
                ml_result = self.ensemble.predict(features)
                ml_score = ml_result.get('ensemble', 0.5)
                scores.append(ml_score)
        except:
            pass
        
        # Weighted average
        if scores:
            # Give more weight to rule-based and statistical for initial detection
            weights = [0.25, 0.30, 0.25, 0.20]  # Stat, Rule, Behavior, ML
            weights = weights[:len(scores)]
            final_score = np.average(scores, weights=weights)
            return float(min(max(final_score, 0), 1))
        
        return 0.0
    
    def _statistical_anomaly_score(self, features: Dict, log: Dict) -> float:
        """Statistical anomaly detection"""
        score = 0.0
        anomalies = 0
        total_checks = 0
        
        # Check unusual hours
        if 'hour' in features:
            total_checks += 1
            hour = features['hour']
            if hour in self.threat_rules['credential_misuse']['unusual_hours']:
                anomalies += 1
        
        # Check failed attempts
        if 'failed_attempts' in features:
            total_checks += 1
            if features['failed_attempts'] >= 3:  # Lowered from 5 to 3
                anomalies += 2  # Weight more heavily
        
        # Check success rate
        if 'success_rate' in features:
            total_checks += 1
            if features['success_rate'] < 0.5:
                anomalies += 1
        
        # Check access frequency
        if 'access_count' in features:
            total_checks += 1
            if features['access_count'] > 10:
                anomalies += 0.5
        
        # Check response time deviation
        if 'response_time' in features:
            total_checks += 1
            if features['response_time'] > 2.0:
                anomalies += 0.5
        
        if total_checks > 0:
            score = anomalies / total_checks
        
        return min(score, 1.0)
    
    def _rule_based_score(self, log: Dict) -> float:
        """Rule-based threat detection"""
        score = 0.0
        rules_triggered = 0
        total_rules = 6
        
        # Check brute force
        if log.get('failed_attempts', 0) >= 3:  # Lowered from 5 to 3
            rules_triggered += 2  # Higher weight
        elif log.get('failed_attempts', 0) >= 1:
            rules_triggered += 0.5
        
        # Check impossible travel
        if 'previous_location' in log and 'current_location' in log:
            distance = self._calculate_distance(
                log['previous_location'], log['current_location']
            )
            time_diff = log.get('time_diff', 1)
            speed = distance / time_diff if time_diff > 0 else 0
            if speed > self.threat_rules['impossible_travel']['max_speed']:
                rules_triggered += 2
        
        # Check lateral movement
        if 'destination_port' in log:
            if log['destination_port'] in self.threat_rules['lateral_movement']['suspicious_ports']:
                rules_triggered += 1.5
        
        # Check unusual hours
        if 'hour' in log:
            if log['hour'] in self.threat_rules['credential_misuse']['unusual_hours']:
                rules_triggered += 1
        
        # Check device spoofing
        if 'os' in log and 'device_os' in log:
            if log['os'] != log['device_os']:
                rules_triggered += 2
        
        # Check failed status
        if log.get('status') == 'failed':
            rules_triggered += 1
        
        if total_rules > 0:
            score = rules_triggered / total_rules
        
        return min(score, 1.0)
    
    def _behavioral_deviation_score(self, features: Dict, log: Dict) -> float:
        """Calculate behavioral deviation score"""
        score = 0.0
        factors = 0
        
        # Unusual hour
        if features.get('unusual_hour_score', 0) > 0.5:
            score += 0.3
            factors += 1
        
        # Location change
        if features.get('location_change_score', 0) > 0.5:
            score += 0.3
            factors += 1
        
        # Failed attempts
        if features.get('failed_attempts', 0) > 2:
            score += 0.3
            factors += 1
        
        # Low success rate
        if features.get('success_rate', 1) < 0.6:
            score += 0.2
            factors += 1
        
        # High access count
        if features.get('access_count', 0) > 8:
            score += 0.2
            factors += 1
        
        # OS mismatch
        if features.get('os_match_score', 0) > 0.7:
            score += 0.3
            factors += 1
        
        if factors > 0:
            return score / factors
        return 0.1
    
    def _classify_threat(self, log: Dict, features: Dict) -> str:
        """Classify the type of threat"""
        scores = {}
        
        # Brute force
        if log.get('failed_attempts', 0) >= 3:
            scores['brute_force'] = min(0.9, 0.5 + log.get('failed_attempts', 0) * 0.08)
        
        # Impossible travel
        if 'previous_location' in log and 'current_location' in log:
            distance = self._calculate_distance(log['previous_location'], log['current_location'])
            time_diff = log.get('time_diff', 1)
            speed = distance / time_diff if time_diff > 0 else 0
            if speed > 800:
                scores['impossible_travel'] = 0.85
        
        # Lateral movement
        if log.get('destination_port', 0) in [22, 3389, 445, 135]:
            scores['lateral_movement'] = 0.8
        
        # Credential misuse
        if log.get('hour', 12) in [0, 1, 2, 3, 4]:
            if log.get('failed_attempts', 0) > 1:
                scores['credential_misuse'] = 0.75
            else:
                scores['credential_misuse'] = 0.5
        
        # Device spoofing
        if log.get('os') != log.get('device_os'):
            scores['device_spoofing'] = 0.9
        
        # Check for multiple indicators
        if len(scores) >= 2:
            # If multiple threats detected, pick the one with highest score
            pass
        
        if scores:
            return max(scores, key=scores.get)
        
        # Default if no specific threat
        if log.get('status') == 'failed':
            return 'credential_misuse'
        
        return 'unknown'
    
    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """Calculate distance between two locations in km"""
        lat1 = loc1.get('lat', 0)
        lon1 = loc1.get('lon', 0)
        lat2 = loc2.get('lat', 0)
        lon2 = loc2.get('lon', 0)
        
        # Haversine formula
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def _create_alert(self, log: Dict, risk_score: float, threat_type: str, explanation: str) -> Dict:
        """Create an alert for detected threat"""
        severity = self._get_risk_level(risk_score)
        
        return {
            'status': 'anomaly',
            'alert_id': f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'risk_score': float(risk_score) / 100,  # Normalize to 0-1
            'threat_type': threat_type,
            'severity': severity,
            'explanation': explanation,
            'log': log,
            'recommendations': self._generate_recommendations(threat_type)
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert numeric risk score to severity level"""
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        elif risk_score >= 20:
            return 'low'
        else:
            return 'info'
    
    def _generate_recommendations(self, threat_type: str) -> List[str]:
        """Generate mitigation recommendations"""
        recommendations = {
            'brute_force': [
                'Enable account lockout after 3 failed attempts',
                'Implement CAPTCHA after 3 failed attempts',
                'Use rate limiting on login endpoints'
            ],
            'impossible_travel': [
                'Require additional authentication for location mismatch',
                'Notify user of suspicious login location',
                'Implement risk-based authentication'
            ],
            'lateral_movement': [
                'Block suspicious network connections',
                'Implement network segmentation',
                'Enable advanced threat protection'
            ],
            'credential_misuse': [
                'Force password reset for affected accounts',
                'Enable MFA for all users',
                'Review access logs for similar patterns'
            ],
            'device_spoofing': [
                'Block unknown device types',
                'Implement device fingerprinting',
                'Require device registration'
            ],
            'unknown': [
                'Monitor the activity',
                'Review access logs',
                'Investigate further'
            ]
        }
        return recommendations.get(threat_type, ['Monitor and investigate the activity'])