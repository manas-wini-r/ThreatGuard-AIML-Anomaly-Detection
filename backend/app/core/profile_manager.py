"""
User and Device Profile Management for Cold Start
"""
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

class ProfileManager:
    def __init__(self):
        self.user_profiles = {}
        self.device_profiles = {}
        self.global_profile = {
            'confidence': 0.4,  # Start with 40% confidence
            'observations': 0,
            'max_observations': 20,  # After 20 observations, personal profile
            'behaviors': {
                'avg_hour': 12,
                'avg_failures': 0.5,
                'avg_response_time': 0.5,
                'avg_bytes': 1024
            }
        }
        self._load_profiles()
    
    def get_profile(self, user_id=None, device_id=None, log=None):
        """
        Get profile with cold start handling
        """
        if user_id and user_id in self.user_profiles:
            # Return personal profile
            return self._get_personal_profile(user_id)
        
        elif user_id:
            # New user - use global profile with observation mode
            return self._get_observation_profile(user_id, log)
        
        else:
            # Use global profile
            return self.global_profile
    
    def _get_personal_profile(self, user_id):
        """Get personal profile for existing user"""
        profile = self.user_profiles[user_id]
        profile['confidence'] = 0.85  # High confidence for personal profile
        return profile
    
    def _get_observation_profile(self, user_id, log):
        """Get observation mode profile for new user"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'confidence': 0.4,
                'observations': 0,
                'behaviors': {'hours': [], 'failures': [], 'responses': []}
            }
        
        profile = self.user_profiles[user_id]
        profile['observations'] += 1
        
        # Update behaviors
        if log:
            if 'hour' in log:
                profile['behaviors']['hours'].append(log['hour'])
            if 'status' in log and log['status'] == 'failed':
                profile['behaviors']['failures'].append(1)
            if 'response_time' in log:
                profile['behaviors']['responses'].append(log['response_time'])
        
        # Check if we have enough observations
        if profile['observations'] >= 20:
            # Promote to personal profile
            profile['confidence'] = 0.85
            self._save_profile(user_id)
        
        return profile
    
    def get_confidence(self, user_id=None):
        """Get confidence level for user"""
        if user_id and user_id in self.user_profiles:
            return self.user_profiles[user_id]['confidence']
        return self.global_profile['confidence']
    
    def update_user_profile(self, user_id, log):
        """Update user profile with new log"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'confidence': 0.4,
                'observations': 0,
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
        
        # After 20 observations, increase confidence
        if profile['observations'] >= 20:
            profile['confidence'] = 0.85
            self._save_profile(user_id)
        
        return profile
    
    def _save_profile(self, user_id):
        """Save profile to disk"""
        os.makedirs('data/profiles', exist_ok=True)
        with open(f'data/profiles/{user_id}.json', 'w') as f:
            json.dump(self.user_profiles[user_id], f)
    
    def _load_profiles(self):
        """Load profiles from disk"""
        if os.path.exists('data/profiles'):
            for file in os.listdir('data/profiles'):
                if file.endswith('.json'):
                    user_id = file.replace('.json', '')
                    with open(f'data/profiles/{file}', 'r') as f:
                        self.user_profiles[user_id] = json.load(f)
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            return {
                'observations': profile['observations'],
                'confidence': profile['confidence'],
                'is_established': profile['observations'] >= 20
            }
        return {'observations': 0, 'confidence': 0.4, 'is_established': False}