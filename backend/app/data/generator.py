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
        self.service_accounts = [f"svc_{i}" for i in range(1, 21)]
        self.edge_devices = [f"edge_{i}" for i in range(1, 31)]
        
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
        
        # NEW: For schema compliance
        self.auth_methods = ['password', 'token', 'certificate', 'biometric']
        self.commands = ['login', 'read', 'write', 'delete', 'execute', 'configure', 'access', 'list']
        self.entity_types = ['user', 'service_account', 'edge_device']
        self.resources = [f"/api/resource_{i}" for i in range(1, 101)] + [f"/port/{i}" for i in [22, 80, 443, 3389, 445, 135]]
        
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
        """Generate a normal (benign) access log with full schema"""
        entity_type = random.choice(self.entity_types)
        
        if entity_type == 'user':
            entity_id = random.choice(self.users)
        elif entity_type == 'service_account':
            entity_id = random.choice(self.service_accounts)
        else:
            entity_id = random.choice(self.edge_devices)
        
        device = random.choice(self.devices)
        location = random.choice(self.locations)
        auth_method = random.choice(self.auth_methods)
        commands = random.sample(self.commands, random.randint(1, 4))
        
        return {
            # Core fields
            'entity_id': entity_id,
            'entity_type': entity_type,
            'timestamp': datetime.now().isoformat(),
            'source_ip': random.choice(self.ips),
            'geo_location': location,
            'resource_accessed': random.choice(self.resources),
            'auth_method': auth_method,
            'session_duration': random.randint(60, 3600),
            'command_sequence': commands,
            'device_fingerprint': device['os'],
            
            # Additional fields (keep existing)
            'device_id': device['id'],
            'os': device['os'],
            'action': random.choice(['login', 'access', 'read', 'write', 'delete']),
            'status': 'success',
            'response_time': random.uniform(0.1, 2.0),
            'session_id': str(uuid.uuid4()),
            'source_port': random.randint(1024, 65535),
            'destination_port': random.choice([80, 443, 22, 3306]),
            'bytes_transferred': random.randint(1024, 10485760),
            
            # Label (NEW - for schema compliance)
            'label': 'benign',
            'access_count': random.randint(1, 10),
            'failed_attempts': 0,
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'is_weekend': 1 if datetime.now().weekday() >= 5 else 0
        }
    
    def _generate_anomalous_log(self) -> Dict:
        """Generate an anomalous log with attack type label"""
        log = self._generate_normal_log()
        anomaly_type = random.choice(self.anomaly_types[1:])  # Exclude 'normal'
        
        # Change label to anomaly
        log['label'] = 'anomaly'
        
        if anomaly_type == 'brute_force':
            log['failed_attempts'] = random.randint(6, 15)
            log['status'] = 'failed'
            log['action'] = 'login'
            log['label'] = 'anomaly_brute_force'
            
        elif anomaly_type == 'impossible_travel':
            loc1 = random.choice(self.locations)
            loc2 = random.choice([l for l in self.locations if l != loc1])
            log['previous_location'] = loc1
            log['geo_location'] = loc2
            log['time_diff'] = random.uniform(0.1, 0.5)
            log['label'] = 'anomaly_impossible_travel'
            
        elif anomaly_type == 'lateral_movement':
            log['destination_port'] = random.choice(self.threat_rules['lateral_movement']['suspicious_ports'])
            log['action'] = 'network_connection'
            log['label'] = 'anomaly_lateral_movement'
            
        elif anomaly_type == 'credential_misuse':
            hour = random.choice([0, 1, 2, 3, 4])
            dt = datetime.now().replace(hour=hour, minute=random.randint(0, 59))
            log['timestamp'] = dt.isoformat()
            log['failed_attempts'] = random.randint(3, 8)
            log['label'] = 'anomaly_credential_misuse'
            
        elif anomaly_type == 'device_spoofing':
            device = random.choice(self.devices)
            log['device_os'] = log['os']
            log['os'] = random.choice(['Windows', 'MacOS', 'Linux'])
            while log['os'] == log['device_os']:
                log['os'] = random.choice(['Windows', 'MacOS', 'Linux'])
            log['device_fingerprint'] = log['os']
            log['label'] = 'anomaly_device_spoofing'
        
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