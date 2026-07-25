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
from ml.drift_detector import DriftDetector
from ml.attack_classifier import AttackClassifier

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.feature_engineer = FeatureEngineer()
        self.explainer = Explainer()
        self.ensemble = EnsembleDetector()
        self.profile_manager = ProfileManager()
        self.drift_detector = DriftDetector()
        self.attack_classifier = AttackClassifier()
        
        if hasattr(self.ensemble, 'model'):
            self.explainer.init_explainers(self.ensemble.model)
        
        self.user_baselines = defaultdict(dict)
        self.device_baselines = defaultdict(dict)
        self.access_patterns = defaultdict(list)
        
        self.buffer = []
        self.buffer_size = 1000
        
        self.threat_rules = {
            'brute_force': {'threshold': 3, 'time_window': 60},
            'impossible_travel': {'max_speed': 800},
            'lateral_movement': {'suspicious_ports': [22, 3389, 445, 135, 1433, 3306]},
            'credential_misuse': {'unusual_hours': [0, 1, 2, 3, 4, 23]},
            'device_spoofing': {'os_mismatch': True}
        }
        
    async def process_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_id = log.get('user_id')
            device_id = log.get('device_id')
            
            if user_id:
                user_stats = self.profile_manager.get_user_stats(user_id)
                if not user_stats['is_established']:
                    return await self._process_cold_start(log, user_stats)
            
            features = self.feature_engineer.extract_enhanced_features(log)
            self._update_baselines(log, features)
            
            threshold_multiplier = self.profile_manager.get_threshold_multiplier(user_id)
            anomaly_score = self._detect_anomaly(features, log)
            
            drift_detected = self.drift_detector.check_drift(anomaly_score)
            
            threshold = 0.5 * threshold_multiplier
            
            if anomaly_score > threshold:
                attack_type, attack_confidence = self.attack_classifier.predict(features)
                
                if attack_confidence < 0.5:
                    attack_type = self._classify_threat(log, features)
                
                risk_score = self._calculate_dynamic_risk(
                    log, features, anomaly_score, attack_type
                )
                
                explanation = self.explainer.explain_anomaly(
                    log, features, anomaly_score, attack_type
                )
                
                risk_factors = self.explainer.generate_risk_factors(log, features)
                
                alert = self._create_alert(log, risk_score, attack_type, explanation)
                alert['attack_confidence'] = attack_confidence
                alert['risk_factors'] = risk_factors
                alert['confidence'] = self.profile_manager.get_confidence(user_id)
                alert['drift_detected'] = drift_detected
                alert['cold_start'] = False
                
                logger.info(f"🚨 ALERT: {attack_type} - Score: {float(anomaly_score):.3f}")
                return alert
            
            return {'status': 'normal', 'log': log}
            
        except Exception as e:
            logger.error(f"Error processing log: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    async def _process_cold_start(self, log: Dict, user_stats: Dict) -> Dict[str, Any]:
        user_id = log.get('user_id')
        self.profile_manager.update_user_profile(user_id, log)
        
        features = self.feature_engineer.extract_enhanced_features(log)
        anomaly_score = self._detect_anomaly(features, log)
        
        confidence = user_stats['confidence']
        adjusted_score = anomaly_score * (1 + (1 - confidence) * 0.5)
        
        if adjusted_score > 0.6:
            threat_type = self._classify_threat(log, features)
            risk_score = self._calculate_dynamic_risk(log, features, adjusted_score, threat_type)
            explanation = self.explainer.explain_anomaly(log, features, adjusted_score, threat_type)
            
            alert = self._create_alert(log, risk_score, threat_type, explanation)
            alert['cold_start'] = True
            alert['observations'] = user_stats['observations']
            alert['confidence'] = confidence
            alert['is_established'] = False
            
            logger.info(f"🚨 COLD START ALERT: {threat_type} - Observations: {user_stats['observations']}/20")
            return alert
        
        return {
            'status': 'observation',
            'confidence': confidence,
            'observations': user_stats['observations'],
            'message': f"User {user_id} in observation mode ({user_stats['observations']}/20)"
        }
    
    async def process_real_time(self, data: str) -> Dict[str, Any]:
        try:
            log = json.loads(data)
            return await self.process_log(log)
        except Exception as e:
            logger.error(f"Error processing real-time data: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def _update_baselines(self, log: Dict, features: Dict):
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
        scores = []
        
        stat_score = self._statistical_anomaly_score(features, log)
        scores.append(stat_score)
        
        rule_score = self._rule_based_score(log)
        scores.append(rule_score)
        
        behavior_score = self._behavioral_deviation_score(features, log)
        scores.append(behavior_score)
        
        try:
            if self.ensemble and hasattr(self.ensemble, 'predict'):
                ml_result = self.ensemble.predict(features)
                ml_score = ml_result.get('ensemble', 0.5)
                scores.append(ml_score)
        except:
            pass
        
        if scores:
            weights = [0.25, 0.30, 0.25, 0.20]
            weights = weights[:len(scores)]
            final_score = np.average(scores, weights=weights)
            return float(min(max(final_score, 0), 1))
        
        return 0.0
    
    def _statistical_anomaly_score(self, features: Dict, log: Dict) -> float:
        score = 0.0
        anomalies = 0
        total_checks = 0
        
        if 'hour' in features:
            total_checks += 1
            hour = features['hour']
            if hour in self.threat_rules['credential_misuse']['unusual_hours']:
                anomalies += 1
        
        if 'failed_attempts' in features:
            total_checks += 1
            if features['failed_attempts'] >= 3:
                anomalies += 2
        
        if 'success_rate' in features:
            total_checks += 1
            if features['success_rate'] < 0.5:
                anomalies += 1
        
        if 'access_count' in features:
            total_checks += 1
            if features['access_count'] > 10:
                anomalies += 0.5
        
        if 'response_time' in features:
            total_checks += 1
            if features['response_time'] > 2.0:
                anomalies += 0.5
        
        if total_checks > 0:
            score = anomalies / total_checks
        
        return min(score, 1.0)
    
    def _rule_based_score(self, log: Dict) -> float:
        score = 0.0
        rules_triggered = 0
        total_rules = 6
        
        if log.get('failed_attempts', 0) >= 3:
            rules_triggered += 2
        elif log.get('failed_attempts', 0) >= 1:
            rules_triggered += 0.5
        
        if 'previous_location' in log and 'current_location' in log:
            distance = self._calculate_distance(
                log['previous_location'], log['current_location']
            )
            time_diff = log.get('time_diff', 1)
            speed = distance / time_diff if time_diff > 0 else 0
            if speed > self.threat_rules['impossible_travel']['max_speed']:
                rules_triggered += 2
        
        if 'destination_port' in log:
            if log['destination_port'] in self.threat_rules['lateral_movement']['suspicious_ports']:
                rules_triggered += 1.5
        
        if 'hour' in log:
            if log['hour'] in self.threat_rules['credential_misuse']['unusual_hours']:
                rules_triggered += 1
        
        if 'os' in log and 'device_os' in log:
            if log['os'] != log['device_os']:
                rules_triggered += 2
        
        if log.get('status') == 'failed':
            rules_triggered += 1
        
        if total_rules > 0:
            score = rules_triggered / total_rules
        
        return min(score, 1.0)
    
    def _behavioral_deviation_score(self, features: Dict, log: Dict) -> float:
        score = 0.0
        factors = 0
        
        if features.get('unusual_hour_score', 0) > 0.5:
            score += 0.3
            factors += 1
        
        if features.get('location_change_score', 0) > 0.5:
            score += 0.3
            factors += 1
        
        if features.get('failed_attempts', 0) > 2:
            score += 0.3
            factors += 1
        
        if features.get('success_rate', 1) < 0.6:
            score += 0.2
            factors += 1
        
        if features.get('access_count', 0) > 8:
            score += 0.2
            factors += 1
        
        if features.get('os_match_score', 0) > 0.7:
            score += 0.3
            factors += 1
        
        if factors > 0:
            return score / factors
        return 0.1
    
    def _classify_threat(self, log: Dict, features: Dict) -> str:
        scores = {}
        
        if log.get('failed_attempts', 0) >= 3:
            scores['brute_force'] = min(0.9, 0.5 + log.get('failed_attempts', 0) * 0.08)
        
        if 'previous_location' in log and 'current_location' in log:
            distance = self._calculate_distance(log['previous_location'], log['current_location'])
            time_diff = log.get('time_diff', 1)
            speed = distance / time_diff if time_diff > 0 else 0
            if speed > 800:
                scores['impossible_travel'] = 0.85
        
        if log.get('destination_port', 0) in [22, 3389, 445, 135]:
            scores['lateral_movement'] = 0.8
        
        if log.get('hour', 12) in [0, 1, 2, 3, 4]:
            if log.get('failed_attempts', 0) > 1:
                scores['credential_misuse'] = 0.75
            else:
                scores['credential_misuse'] = 0.5
        
        if log.get('os') != log.get('device_os'):
            scores['device_spoofing'] = 0.9
        
        if scores:
            return max(scores, key=scores.get)
        
        if log.get('status') == 'failed':
            return 'credential_misuse'
        
        return 'unknown'
    
    def _calculate_dynamic_risk(self, log: Dict, features: Dict, ml_score: float, attack_type: str = None) -> float:
        ml_weight = 0.4
        ml_contribution = ml_score * ml_weight
        
        rule_score = self._calculate_rule_score(log)
        rule_weight = 0.3
        rule_contribution = rule_score * rule_weight
        
        behavior_score = self._calculate_behavior_score(log, features)
        behavior_weight = 0.2
        behavior_contribution = behavior_score * behavior_weight
        
        confidence = self._get_confidence(log)
        confidence_weight = 0.1
        confidence_contribution = confidence * confidence_weight
        
        risk_score = (
            ml_contribution +
            rule_contribution +
            behavior_contribution +
            confidence_contribution
        ) * 100
        
        return float(min(max(risk_score, 0), 100))
    
    def _calculate_rule_score(self, log: Dict) -> float:
        score = 0.0
        rules_triggered = 0
        total_rules = 6
        
        if log.get('failed_attempts', 0) >= 5:
            rules_triggered += 1
        
        if 'previous_location' in log and 'current_location' in log:
            distance = self._calculate_distance(log['previous_location'], log['current_location'])
            if distance > 800:
                rules_triggered += 1
        
        if log.get('destination_port', 0) in [22, 3389, 445, 135]:
            rules_triggered += 1
        
        if log.get('hour', 12) in [0, 1, 2, 3, 4]:
            rules_triggered += 1
        
        if log.get('os') != log.get('device_os'):
            rules_triggered += 1
        
        if log.get('failed_attempts', 0) > 3 and log.get('hour', 12) in [0, 1, 2, 3, 4]:
            rules_triggered += 1
        
        score = rules_triggered / total_rules
        return min(score, 1.0)
    
    def _calculate_behavior_score(self, log: Dict, features: Dict) -> float:
        score = 0.0
        factors = 0
        
        if features.get('unusual_hour_score', 0) > 0.7:
            score += 0.3
            factors += 1
        
        if features.get('location_change_score', 0) > 0.7:
            score += 0.3
            factors += 1
        
        if features.get('success_rate', 1) < 0.5:
            score += 0.2
            factors += 1
        
        if features.get('access_count', 0) > 10:
            score += 0.2
            factors += 1
        
        return score / max(factors, 1) if factors > 0 else 0.5
    
    def _get_confidence(self, log: Dict) -> float:
        user_id = log.get('user_id')
        if user_id:
            stats = self.profile_manager.get_user_stats(user_id)
            return stats['confidence']
        return 0.5
    
    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        lat1 = loc1.get('lat', 0)
        lon1 = loc1.get('lon', 0)
        lat2 = loc2.get('lat', 0)
        lon2 = loc2.get('lon', 0)
        
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def _create_alert(self, log: Dict, risk_score: float, threat_type: str, explanation: str) -> Dict:
        severity = self._get_risk_level(risk_score)
        
        try:
            risk_value = float(risk_score) / 100.0
        except (TypeError, ValueError):
            risk_value = 0.0
        
        # FIXED: No f-string with strftime
        now = datetime.now()
        alert_id = "ALT-" + now.strftime("%Y%m%d%H%M%S")
        timestamp = now.isoformat()
        
        return {
            'status': 'anomaly',
            'alert_id': alert_id,
            'timestamp': timestamp,
            'risk_score': risk_value,
            'threat_type': threat_type,
            'severity': severity,
            'explanation': explanation,
            'log': log,
            'recommendations': self._generate_recommendations(threat_type)
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        try:
            score = float(risk_score)
        except (TypeError, ValueError):
            score = 0.0
        
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        elif score >= 20:
            return 'low'
        else:
            return 'info'
    
    def _generate_recommendations(self, threat_type: str) -> List[str]:
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
    
    def get_drift_stats(self) -> Dict:
        return self.drift_detector.get_drift_stats()
    
    def get_profile_stats(self, user_id: str) -> Dict:
        return self.profile_manager.get_user_stats(user_id)