from datetime import datetime, timedelta
import json
import os
from collections import defaultdict
import numpy as np
import logging
logger = logging.getLogger(__name__)

class ProfileManager:
    def __init__(self):
        self.user_profiles = {}
        self.device_profiles = {}
        self.global_profile = {
            'confidence': 0.4,  # Start with 40% confidence
            'observations': 0,
            'max_observations': 20,  # After 20 observations -> personal profile
            'behaviors': {
                'avg_hour': 12,
                'avg_failures': 0.5,
                'avg_response_time': 0.5,
                'avg_bytes': 1024,
                'avg_access_count': 5
            },
            'threshold_multiplier': 1.5  # Higher threshold for new users
        }
        self._load_profiles()
    
    def get_profile(self, user_id=None, device_id=None, log=None):
        """
        Get profile with cold start handling
        """
        # For device
        if device_id and device_id in self.device_profiles:
            return self._get_device_profile(device_id)
        elif device_id:
            return self._get_observation_device_profile(device_id, log)
        
        # For user
        if user_id and user_id in self.user_profiles:
            return self._get_personal_profile(user_id)
        elif user_id:
            return self._get_observation_profile(user_id, log)
        
        # Fallback to global profile
        return self.global_profile
    
    def _get_personal_profile(self, user_id):
        """Get personal profile for existing user"""
        profile = self.user_profiles[user_id]
        profile['confidence'] = 0.85  # High confidence for personal profile
        profile['is_established'] = True
        return profile
    
    def _get_observation_profile(self, user_id, log):
        """Get observation mode profile for new user"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'confidence': 0.4,
                'observations': 0,
                'is_established': False,
                'behaviors': {
                    'hours': [],
                    'failures': [],
                    'responses': [],
                    'access_counts': [],
                    'successes': []
                },
                'start_time': datetime.now().isoformat()
            }
        
        profile = self.user_profiles[user_id]
        profile['observations'] += 1
        
        # Update behaviors
        if log:
            if 'hour' in log:
                profile['behaviors']['hours'].append(log['hour'])
            if 'status' in log:
                profile['behaviors']['successes'].append(1 if log['status'] == 'success' else 0)
            if 'response_time' in log:
                profile['behaviors']['responses'].append(log['response_time'])
            if 'access_count' in log:
                profile['behaviors']['access_counts'].append(log['access_count'])
        
        # Check if we have enough observations
        if profile['observations'] >= 20:
            # Promote to personal profile
            profile['confidence'] = 0.85
            profile['is_established'] = True
            self._save_profile(user_id)
            logger.info(f"✅ User {user_id} promoted to personal profile!")
        
        return profile
    
    def _get_device_profile(self, device_id):
        """Get existing device profile"""
        return self.device_profiles[device_id]
    
    def _get_observation_device_profile(self, device_id, log):
        """Get observation mode for new device"""
        if device_id not in self.device_profiles:
            self.device_profiles[device_id] = {
                'confidence': 0.4,
                'observations': 0,
                'is_established': False,
                'behaviors': {
                    'os': [],
                    'ips': [],
                    'ports': []
                }
            }
        
        profile = self.device_profiles[device_id]
        profile['observations'] += 1
        
        if log:
            if 'os' in log:
                profile['behaviors']['os'].append(log['os'])
            if 'ip' in log:
                profile['behaviors']['ips'].append(log['ip'])
            if 'destination_port' in log:
                profile['behaviors']['ports'].append(log['destination_port'])
        
        if profile['observations'] >= 20:
            profile['confidence'] = 0.85
            profile['is_established'] = True
            self._save_device_profile(device_id)
        
        return profile
    
    def get_confidence(self, user_id=None, device_id=None):
        """Get confidence level for user or device"""
        if user_id and user_id in self.user_profiles:
            return self.user_profiles[user_id]['confidence']
        if device_id and device_id in self.device_profiles:
            return self.device_profiles[device_id]['confidence']
        return self.global_profile['confidence']
    
    def get_threshold_multiplier(self, user_id=None):
        """Get threshold multiplier for cold start"""
        if user_id and user_id in self.user_profiles:
            if not self.user_profiles[user_id]['is_established']:
                return 1.5  # Higher threshold for new users
        return 1.0
    
    def update_user_profile(self, user_id, log):
        """Update user profile with new log"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'confidence': 0.4,
                'observations': 0,
                'is_established': False,
                'behaviors': {'hours': [], 'failures': [], 'responses': []}
            }
        
        profile = self.user_profiles[user_id]
        profile['observations'] += 1
        
        if 'hour' in log:
            profile['behaviors']['hours'].append(log['hour'])
        if 'status' in log and log['status'] == 'failed':
            profile['behaviors']['failures'].append(1)
        if 'response_time' in log:
            profile['behaviors']['responses'].append(log['response_time'])
        
        if profile['observations'] >= 20:
            profile['confidence'] = 0.85
            profile['is_established'] = True
            self._save_profile(user_id)
        
        return profile
    
    def _save_profile(self, user_id):
        """Save profile to disk"""
        os.makedirs('data/profiles', exist_ok=True)
        with open(f'data/profiles/{user_id}.json', 'w') as f:
            json.dump(self.user_profiles[user_id], f)
    
    def _save_device_profile(self, device_id):
        """Save device profile to disk"""
        os.makedirs('data/profiles', exist_ok=True)
        with open(f'data/profiles/device_{device_id}.json', 'w') as f:
            json.dump(self.device_profiles[device_id], f)
    
    def _load_profiles(self):
        """Load profiles from disk"""
        if os.path.exists('data/profiles'):
            for file in os.listdir('data/profiles'):
                if file.endswith('.json'):
                    with open(f'data/profiles/{file}', 'r') as f:
                        data = json.load(f)
                        if file.startswith('device_'):
                            self.device_profiles[file.replace('.json', '')] = data
                        else:
                            self.user_profiles[file.replace('.json', '')] = data
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            return {
                'observations': profile['observations'],
                'confidence': profile['confidence'],
                'is_established': profile.get('is_established', False)
            }
        return {'observations': 0, 'confidence': 0.4, 'is_established': False}