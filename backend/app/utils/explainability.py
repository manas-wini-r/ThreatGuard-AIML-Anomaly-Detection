"""
Advanced Explainability using SHAP and LIME
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)

class Explainer:
    def __init__(self):
        self.shap_explainer = None
        self.lime_explainer = None
        self.is_initialized = False
        self.feature_names = [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'access_count', 'failed_attempts', 'success_rate',
            'response_time', 'bytes_transferred', 'is_success',
            'user_access_frequency', 'device_access_frequency',
            'unusual_hour_score', 'location_change_score',
            'port_risk_score', 'os_match_score'
        ]
    
    def init_explainers(self, model, X_train=None):
        """
        Initialize SHAP and LIME explainers
        """
        try:
            import shap
            # SHAP explainer
            if X_train is not None:
                self.shap_explainer = shap.TreeExplainer(model, X_train)
            else:
                self.shap_explainer = shap.TreeExplainer(model)
            
            # LIME explainer
            from lime.lime_tabular import LimeTabularExplainer
            if X_train is not None:
                self.lime_explainer = LimeTabularExplainer(
                    X_train,
                    feature_names=self.feature_names,
                    mode='classification',
                    discretize_continuous=True
                )
            
            self.is_initialized = True
            logger.info("✅ SHAP and LIME explainers initialized!")
        except ImportError as e:
            logger.warning(f"⚠️ SHAP/LIME not available: {e}")
            self.is_initialized = False
    
    def explain_anomaly(self, log: Dict, features: Dict, score: float, threat_type: str) -> str:
        """
        Generate human-readable explanation for anomaly
        """
        explanations = []
        
        # General explanation
        explanations.append(f"🚨 Anomaly detected with risk score {score:.2f}")
        explanations.append(f"📌 Threat type: {threat_type}")
        
        # Specific explanations based on threat type
        if threat_type == 'brute_force':
            explanations.append(
                f"🔑 Multiple failed login attempts detected from user {log.get('user_id')}"
            )
            explanations.append(
                f"📊 Failed attempts: {log.get('failed_attempts', 0)} in recent period"
            )
            
        elif threat_type == 'impossible_travel':
            prev_loc = log.get('previous_location', {})
            curr_loc = log.get('current_location', {})
            explanations.append(
                f"🌍 Impossible travel detected between {prev_loc.get('city', 'unknown')} "
                f"and {curr_loc.get('city', 'unknown')}"
            )
            explanations.append(
                f"⏱️ Time difference: {log.get('time_diff', 0):.2f} hours"
            )
            
        elif threat_type == 'lateral_movement':
            explanations.append(
                f"🔌 Suspicious network connection to port {log.get('destination_port')}"
            )
            explanations.append(
                f"🔄 Potential lateral movement from {log.get('source_ip')}"
            )
            
        elif threat_type == 'credential_misuse':
            explanations.append(
                f"⏰ Access attempt at unusual hour: {log.get('timestamp')}"
            )
            explanations.append(
                f"👤 User {log.get('user_id')} accessed from unusual location"
            )
            
        elif threat_type == 'device_spoofing':
            explanations.append(
                f"💻 Device OS mismatch detected: {log.get('os')} vs {log.get('device_os')}"
            )
            explanations.append(
                f"⚠️ Potential device spoofing attempt"
            )
        
        # Add behavioral context
        explanations.append(self._get_behavioral_context(log))
        
        # Add SHAP explanation if available
        shap_explanation = self._get_shap_explanation(features)
        if shap_explanation:
            explanations.append(f"🧠 Top contributing features: {shap_explanation}")
        
        return "\n".join(explanations)
    
    def _get_behavioral_context(self, log: Dict) -> str:
        """Generate behavioral context for the anomaly"""
        context = []
        
        if 'user_id' in log:
            context.append(f"👤 User: {log['user_id']}")
        if 'device_id' in log:
            context.append(f"💻 Device: {log['device_id']}")
        if 'location' in log:
            context.append(f"📍 Location: {log['location'].get('city', 'unknown')}")
        if 'hour' in log:
            context.append(f"🕐 Hour: {log['hour']}:00")
        
        return f"📋 Context: {' | '.join(context)}"
    
    def _get_shap_explanation(self, features: Dict) -> str:
        """
        Get SHAP explanation for the prediction
        """
        if not self.is_initialized or self.shap_explainer is None:
            return None
        
        try:
            import shap
            # Convert features to array
            feature_array = np.array([list(features.values())])
            
            # Get SHAP values
            shap_values = self.shap_explainer.shap_values(feature_array)
            
            # Get top 3 features
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # For binary classification
            
            abs_shap = np.abs(shap_values[0])
            top_indices = np.argsort(abs_shap)[-3:][::-1]
            
            top_features = []
            for idx in top_indices:
                if idx < len(self.feature_names):
                    feature_name = self.feature_names[idx]
                    feature_value = features.get(feature_name, 0)
                    shap_value = shap_values[0][idx]
                    direction = "↑" if shap_value > 0 else "↓"
                    top_features.append(f"{feature_name}: {feature_value:.2f} {direction}")
            
            return ", ".join(top_features)
            
        except Exception as e:
            logger.error(f"SHAP explanation error: {e}")
            return None
    
    def get_lime_explanation(self, model, features: Dict) -> Dict:
        """
        Get LIME explanation for the prediction
        """
        if not self.is_initialized or self.lime_explainer is None:
            return None
        
        try:
            feature_array = np.array([list(features.values())])
            
            # Get LIME explanation
            explanation = self.lime_explainer.explain_instance(
                feature_array[0],
                model.predict_proba,
                num_features=5
            )
            
            return {
                'feature_importance': explanation.as_list(),
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"LIME explanation error: {e}")
            return None
    
    def generate_risk_factors(self, log: Dict, features: Dict) -> List[Dict]:
    
        risk_factors = []
        
        # Check each risk factor
        if 'failed_attempts' in log:
            risk_factors.append({
                'factor': 'Failed attempts',
                'value': log['failed_attempts'],
                'risk': 'high' if log['failed_attempts'] > 3 else 'low',
                'description': 'Multiple failed login attempts',
                'explanation': f'{log["failed_attempts"]} failed attempts detected'
            })
        
        if 'hour' in features:
            hour = features['hour']
            is_unusual = hour in [0, 1, 2, 3, 4, 23]
            risk_factors.append({
                'factor': 'Login hour',
                # FIX: Convert hour to int before formatting
                'value': f"{int(hour):02d}:00",
                'risk': 'high' if is_unusual else 'low',
                'description': 'Access during unusual hours',
                'explanation': f'Access at {int(hour):02d}:00 {"(unusual)" if is_unusual else "(normal)"}'
            })
        
        if 'location' in log:
            risk_factors.append({
                'factor': 'Location',
                'value': log['location'].get('city', 'unknown'),
                'risk': 'medium',
                'description': 'Access from non-typical location',
                'explanation': f'Access from {log["location"].get("city", "unknown")}'
            })
        
        if 'os' in log and 'device_os' in log:
            is_match = log['os'] == log['device_os']
            risk_factors.append({
                'factor': 'Device OS',
                'value': log['os'],
                'risk': 'high' if not is_match else 'low',
                'description': 'OS mismatch' if not is_match else 'OS match',
                'explanation': f'OS: {log["os"]} vs Device OS: {log["device_os"]}'
            })
        
        if 'port_risk_score' in features:
            risk_factors.append({
                'factor': 'Port Risk',
                'value': f"{features['port_risk_score']:.2f}",
                'risk': 'high' if features['port_risk_score'] > 0.7 else 'low',
                'description': 'Network port risk assessment',
                'explanation': f'Port risk score: {features["port_risk_score"]:.2f}'
            })
        
        return risk_factors