import numpy as np
from typing import Dict, Any, List
import shap
import json

class Explainer:
    def __init__(self):
        self.explainer = None
        
    def explain_anomaly(self, log: Dict, features: Dict, score: float, threat_type: str) -> str:
        """Generate human-readable explanation for anomaly"""
        explanations = []
        
        # General explanation
        explanations.append(f"Anomaly detected with risk score {score:.2f}")
        explanations.append(f"Threat type: {threat_type}")
        
        # Specific explanations based on threat type
        if threat_type == 'brute_force':
            explanations.append(
                f"Multiple failed login attempts detected from user {log.get('user_id')}"
            )
            explanations.append(
                f"Failed attempts: {log.get('failed_attempts', 0)} in recent period"
            )
            
        elif threat_type == 'impossible_travel':
            prev_loc = log.get('previous_location', {})
            curr_loc = log.get('current_location', {})
            explanations.append(
                f"Impossible travel detected between {prev_loc.get('city', 'unknown')} "
                f"and {curr_loc.get('city', 'unknown')}"
            )
            explanations.append(
                f"Time difference: {log.get('time_diff', 0):.2f} hours"
            )
            
        elif threat_type == 'lateral_movement':
            explanations.append(
                f"Suspicious network connection to port {log.get('destination_port')}"
            )
            explanations.append(
                f"Potential lateral movement from {log.get('source_ip')}"
            )
            
        elif threat_type == 'credential_misuse':
            explanations.append(
                f"Access attempt at unusual hour: {log.get('timestamp')}"
            )
            explanations.append(
                f"User {log.get('user_id')} accessed from unusual location"
            )
            
        elif threat_type == 'device_spoofing':
            explanations.append(
                f"Device OS mismatch detected: {log.get('os')} vs {log.get('device_os')}"
            )
            explanations.append(
                f"Potential device spoofing attempt"
            )
        
        # Add behavioral context
        explanations.append(self._get_behavioral_context(log))
        
        return "\n".join(explanations)
    
    def _get_behavioral_context(self, log: Dict) -> str:
        """Generate behavioral context for the anomaly"""
        context = []
        
        if 'user_id' in log:
            context.append(f"User: {log['user_id']}")
        if 'device_id' in log:
            context.append(f"Device: {log['device_id']}")
        if 'location' in log:
            context.append(f"Location: {log['location'].get('city', 'unknown')}")
        
        return f"Context: {' | '.join(context)}"
    
    def generate_risk_factors(self, log: Dict, features: Dict) -> List[Dict]:
        """Generate detailed risk factors"""
        risk_factors = []
        
        # Check each risk factor
        if 'failed_attempts' in log:
            risk_factors.append({
                'factor': 'Failed attempts',
                'value': log['failed_attempts'],
                'risk': 'high' if log['failed_attempts'] > 3 else 'low',
                'description': 'Multiple failed login attempts'
            })
        
        if 'hour' in features:
            hour = features['hour']
            is_unusual = hour in [0, 1, 2, 3, 4]
            risk_factors.append({
                'factor': 'Login hour',
                'value': f"{hour:02d}:00",
                'risk': 'high' if is_unusual else 'low',
                'description': 'Access during unusual hours'
            })
        
        if 'location' in log:
            risk_factors.append({
                'factor': 'Location',
                'value': log['location'].get('city', 'unknown'),
                'risk': 'medium',
                'description': 'Access from non-typical location'
            })
        
        if 'os' in log and 'device_os' in log:
            is_match = log['os'] == log['device_os']
            risk_factors.append({
                'factor': 'Device OS',
                'value': log['os'],
                'risk': 'high' if not is_match else 'low',
                'description': 'OS mismatch' if not is_match else 'OS match'
            })
        
        return risk_factors