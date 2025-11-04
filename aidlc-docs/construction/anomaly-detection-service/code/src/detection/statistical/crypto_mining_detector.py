"""
Crypto Mining Detection Algorithm
Detects cryptocurrency mining activities by analyzing network traffic patterns.
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CryptoMiningAnomaly:
    anomaly_id: str
    source_ip: str
    mining_pools: List[str]
    connection_count: int
    data_volume: int
    mining_protocol: str
    confidence_score: float
    threat_type: str = "CRYPTO_MINING"
    detection_timestamp: datetime = None

    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()

class CryptoMiningDetector:
    def __init__(self,
                 min_connections: int = 5,
                 data_threshold: int = 1024 * 1024,  # 1MB
                 confidence_threshold: float = 0.8):
        self.min_connections = min_connections
        self.data_threshold = data_threshold
        self.confidence_threshold = confidence_threshold
        
        # Known mining pool ports and patterns
        self.mining_ports = {
            3333, 4444, 8333, 8080, 9999,  # Common mining ports
            14444, 25565, 30303, 8545      # Alternative mining ports
        }
        
        # Known mining pool domains/IPs (simplified patterns)
        self.mining_pool_patterns = {
            'stratum', 'pool', 'mining', 'mine', 'crypto',
            'btc', 'eth', 'xmr', 'monero', 'bitcoin', 'ethereum'
        }
    
    def detect(self, flow_logs: List[FlowLog]) -> List[CryptoMiningAnomaly]:
        """Detect crypto mining patterns in flow logs"""
        source_activities = defaultdict(lambda: {
            'connections': [],
            'total_bytes': 0,
            'mining_destinations': set(),
            'protocols': set()
        })
        
        anomalies = []
        
        # Analyze traffic patterns by source IP
        for log in flow_logs:
            source_ip = log.source_ip
            activity = source_activities[source_ip]
            
            activity['connections'].append({
                'dest_ip': log.destination_ip,
                'dest_port': log.destination_port,
                'timestamp': log.timestamp,
                'bytes': log.bytes,
                'packets': log.packets,
                'protocol': log.protocol
            })
            
            activity['total_bytes'] += log.bytes
            activity['protocols'].add(log.protocol)
            
            # Check if destination matches mining patterns
            if self._is_potential_mining_destination(log.destination_ip, log.destination_port):
                activity['mining_destinations'].add(f"{log.destination_ip}:{log.destination_port}")
        
        # Evaluate each source for mining activity
        for source_ip, activity in source_activities.items():
            if (len(activity['connections']) >= self.min_connections and
                activity['total_bytes'] >= self.data_threshold and
                len(activity['mining_destinations']) > 0):
                
                # Multi-stage validation
                validation_score = self._validate_mining_indicators(activity)
                
                if validation_score > self.confidence_threshold:
                    mining_protocol = self._identify_mining_protocol(activity)
                    
                    anomaly = CryptoMiningAnomaly(
                        anomaly_id=f"crypto_{source_ip}_{int(time.time())}",
                        source_ip=source_ip,
                        mining_pools=list(activity['mining_destinations']),
                        connection_count=len(activity['connections']),
                        data_volume=activity['total_bytes'],
                        mining_protocol=mining_protocol,
                        confidence_score=validation_score
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _is_potential_mining_destination(self, dest_ip: str, dest_port: int) -> bool:
        """Check if destination matches mining pool patterns"""
        # Check port patterns
        if dest_port in self.mining_ports:
            return True
        
        # Check IP patterns (simplified - in real implementation, use threat intelligence)
        # This is a basic heuristic check
        if any(pattern in dest_ip.lower() for pattern in self.mining_pool_patterns):
            return True
        
        return False
    
    def _validate_mining_indicators(self, activity: Dict) -> float:
        """Multi-stage validation for crypto mining"""
        score = 0.0
        
        # Indicator 1: Connection to known mining ports
        mining_port_connections = sum(
            1 for conn in activity['connections'] 
            if conn['dest_port'] in self.mining_ports
        )
        if mining_port_connections > 0:
            score += min(mining_port_connections / len(activity['connections']), 0.4)
        
        # Indicator 2: Persistent connections (mining requires sustained connections)
        connection_duration = self._analyze_connection_persistence(activity['connections'])
        if connection_duration > 300:  # More than 5 minutes
            score += 0.3
        elif connection_duration > 60:  # More than 1 minute
            score += 0.2
        
        # Indicator 3: Data volume patterns (mining has specific traffic patterns)
        data_pattern_score = self._analyze_data_patterns(activity['connections'])
        score += data_pattern_score * 0.2
        
        # Indicator 4: Protocol analysis
        if 'TCP' in activity['protocols']:
            score += 0.1  # Mining typically uses TCP
        
        return min(score, 1.0)
    
    def _analyze_connection_persistence(self, connections: List[Dict]) -> float:
        """Analyze connection persistence patterns"""
        if len(connections) < 2:
            return 0.0
        
        # Group connections by destination
        dest_connections = defaultdict(list)
        for conn in connections:
            dest_key = f"{conn['dest_ip']}:{conn['dest_port']}"
            dest_connections[dest_key].append(conn['timestamp'])
        
        max_duration = 0.0
        for dest, timestamps in dest_connections.items():
            if len(timestamps) > 1:
                timestamps.sort()
                duration = (timestamps[-1] - timestamps[0]).total_seconds()
                max_duration = max(max_duration, duration)
        
        return max_duration
    
    def _analyze_data_patterns(self, connections: List[Dict]) -> float:
        """Analyze data transfer patterns typical of mining"""
        if not connections:
            return 0.0
        
        score = 0.0
        
        # Pattern 1: Consistent data sizes (mining work units)
        byte_sizes = [conn['bytes'] for conn in connections if conn['bytes'] > 0]
        if len(byte_sizes) > 5:
            # Check for consistency in data sizes
            size_variance = statistics.variance(byte_sizes) if len(byte_sizes) > 1 else 0
            mean_size = statistics.mean(byte_sizes)
            
            if mean_size > 0:
                cv = (size_variance ** 0.5) / mean_size
                if cv < 0.5:  # Low variance indicates consistent work units
                    score += 0.5
        
        # Pattern 2: Bidirectional traffic (mining involves both sending and receiving)
        outbound_bytes = sum(conn['bytes'] for conn in connections)
        if outbound_bytes > 1000:  # Significant outbound traffic
            score += 0.3
        
        # Pattern 3: Regular intervals (mining work submission)
        timestamps = [conn['timestamp'] for conn in connections]
        if len(timestamps) > 3:
            intervals = []
            timestamps.sort()
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            if intervals:
                mean_interval = statistics.mean(intervals)
                if 10 <= mean_interval <= 300:  # Regular intervals between 10s and 5min
                    score += 0.2
        
        return min(score, 1.0)
    
    def _identify_mining_protocol(self, activity: Dict) -> str:
        """Identify the mining protocol being used"""
        # Analyze port patterns to identify protocol
        ports_used = set(conn['dest_port'] for conn in activity['connections'])
        
        if 3333 in ports_used or 4444 in ports_used:
            return "STRATUM"
        elif 8333 in ports_used:
            return "BITCOIN_RPC"
        elif 30303 in ports_used:
            return "ETHEREUM"
        elif any(port in {8080, 8545} for port in ports_used):
            return "HTTP_MINING"
        else:
            return "UNKNOWN_MINING_PROTOCOL"