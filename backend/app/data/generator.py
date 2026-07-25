import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import uuid
from typing import Dict, List, Any
import json

class DataGenerator:
    def __init__(self):
        self.users = [f"user_{i}" for i in range(1, 101)]
        self.devices = [
            {'id': f"device_{i}", 'os': random.choice(['Windows', 'MacOS', 'Linux', 'iOS', 'Android'])}
            for i in range(1, 51)
        ]
        self.ips = [f"192.168.{random.randint(1,254)}.{random.randint(1,254)}" for _ in range(50)]
        
        # Locations for impossible travel simulation
        self.locations = [
            {'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
            {'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
            {'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
            {'city': 'Sydney', 'lat': -33.8688, 'lon': 151.2093},
            {'city': 'Dubai', 'lat': 25.2048, 'lon': 55.2708},
            {'city': 'Singapore', 'lat': 1.3521, 'lon': 103.8198},
            {'city': 'San Francisco', 'lat': 37.7749, 'lon': -122.4194},
            {'city': 'Toronto', 'lat': 43.6532, 'lon': -79.3832}
        ]
        
        self.ports = [22, 80, 443, 3389, 445, 135, 1433, 3306, 8080, 8443]
        self.anomaly_types = ['normal', 'brute_force', 'impossible_travel', 
                             'lateral_movement', 'credential_misuse', 'device_spoofing']
        
        # Add threat_rules attribute
        self.threat_rules = {
            'lateral_movement': {
                'suspicious_ports': [22, 3389, 445, 135]
            }
        }
    
    def generate_batch(self, size: int = 100, anomaly_rate: float = 0.05) -> List[Dict]:
        """Generate a batch of synthetic access logs"""
        logs = []
        for _ in range(size):
            if random.random() < anomaly_rate:
                log = self._generate_anomalous_log()
            else:
                log = self._generate_normal_log()
            logs.append(log)
        return logs
    
    def _generate_normal_log(self) -> Dict:
        """Generate a normal access log"""
        user = random.choice(self.users)
        device = random.choice(self.devices)
        location = random.choice(self.locations)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'user_id': user,
            'device_id': device['id'],
            'os': device['os'],
            'ip': random.choice(self.ips),
            'location': location,
            'action': random.choice(['login', 'access', 'read', 'write', 'delete']),
            'resource': f"/api/resource_{random.randint(1, 100)}",
            'status': random.choice(['success', 'success', 'success', 'success', 'failed']),
            'response_time': random.uniform(0.1, 2.0),
            'session_id': str(uuid.uuid4()),
            'source_port': random.randint(1024, 65535),
            'destination_port': random.choice([80, 443, 22, 3306]),
            'bytes_transferred': random.randint(1024, 10485760)
        }
    
    def _generate_anomalous_log(self) -> Dict:
        """Generate an anomalous access log"""
        log = self._generate_normal_log()
        anomaly_type = random.choice(self.anomaly_types[1:])  # Exclude 'normal'
        
        if anomaly_type == 'brute_force':
            log['failed_attempts'] = random.randint(6, 15)
            log['status'] = 'failed'
            log['action'] = 'login'
            
        elif anomaly_type == 'impossible_travel':
            # Two locations far apart with short time difference
            loc1 = random.choice(self.locations)
            loc2 = random.choice([l for l in self.locations if l != loc1])
            log['previous_location'] = loc1
            log['current_location'] = loc2
            log['time_diff'] = random.uniform(0.1, 0.5)  # Very short time
            
        elif anomaly_type == 'lateral_movement':
            log['destination_port'] = random.choice(self.threat_rules['lateral_movement']['suspicious_ports'])
            log['action'] = 'network_connection'
            
        elif anomaly_type == 'credential_misuse':
            # Unusual hour (midnight to 4 AM)
            hour = random.choice([0, 1, 2, 3, 4])
            log['timestamp'] = datetime.now().replace(hour=hour).isoformat()
            
        elif anomaly_type == 'device_spoofing':
            # Mismatched OS
            device = random.choice(self.devices)
            log['device_os'] = log['os']
            log['os'] = random.choice(['Windows', 'MacOS', 'Linux'])
            while log['os'] == log['device_os']:  # Ensure mismatch
                log['os'] = random.choice(['Windows', 'MacOS', 'Linux'])
        
        return log

    def generate_dataset(self, n_samples: int = 10000, anomaly_rate: float = 0.05) -> pd.DataFrame:
        """Generate a complete dataset for training"""
        logs = self.generate_batch(n_samples, anomaly_rate)
        df = pd.DataFrame(logs)
        return df
    
    def generate_streaming_data(self, batch_size: int = 10):
        """Generator for streaming data"""
        while True:
            yield self.generate_batch(batch_size)