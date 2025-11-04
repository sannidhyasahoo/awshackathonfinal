"""
DDoS Detection Algorithm
Detects Distributed Denial of Service attacks by analyzing traffic patterns and packet rates.
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class DDoSAnomaly:
    anomaly_id: str
    target_ip: str
    target_port: int
    packet_rate: float
    source_count: int
    attack_type: str
    confidence_score: float
    threat_type: str = "DDOS"
    detection_timestamp: datetime = None

    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()

class DDoSDetector:
    def __init__(self,
                 packet_rate_threshold: float = 1000.0,  # packets per second
                 critical_threshold: float = 5000.0,
                 high_threshold: float = 2000.0,
                 time_window: int = 60,
                 confidence_threshold: float = 0.8):
        self.packet_rate_threshold = packet_rate_threshold
        self.critical_threshold = critical_threshold
        self.high_threshold = high_threshold
        self.time_window = time_window
        self.confidence_threshold = confidence_threshold
    
    def detect(self, flow_logs: List[FlowLog]) -> List[DDoSAnomaly]:
        """Detect DDoS patterns in flow logs"""
        destination_traffic = {}
        anomalies = []
        
        for log in flow_logs:
            dest_key = f"{log.destination_ip}:{log.destination_port}"
            timestamp = log.timestamp
            
            if dest_key not in destination_traffic:
                destination_traffic[dest_key] = {
                    'packet_count': 0,
                    'byte_count': 0,
                    'source_ips': set(),
                    'first_packet': timestamp,
                    'last_packet': timestamp,
                    'connections': []
                }
            
            traffic = destination_traffic[dest_key]
            traffic['packet_count'] += log.packets
            traffic['byte_count'] += log.bytes
            traffic['source_ips'].add(log.source_ip)
            traffic['last_packet'] = max(traffic['last_packet'], timestamp)
            traffic['connections'].append({
                'source_ip': log.source_ip,
                'timestamp': timestamp,
                'packets': log.packets,
                'bytes': log.bytes,
                'action': log.action,
                'protocol': log.protocol
            })
            
            # Check for DDoS patterns
            time_diff = (traffic['last_packet'] - traffic['first_packet']).total_seconds()
            if time_diff > 0 and time_diff <= self.time_window:
                
                # Calculate packet rate
                packet_rate = traffic['packet_count'] / time_diff
                
                # Multi-stage validation for DDoS
                if packet_rate > self.packet_rate_threshold:
                    validation_score = self._validate_ddos_indicators(traffic, packet_rate)
                    
                    if validation_score > self.confidence_threshold:
                        dest_ip, dest_port = dest_key.split(':')
                        
                        anomaly = DDoSAnomaly(
                            anomaly_id=f"ddos_{dest_ip}_{dest_port}_{int(timestamp.timestamp())}",
                            target_ip=dest_ip,
                            target_port=int(dest_port),
                            packet_rate=packet_rate,
                            source_count=len(traffic['source_ips']),
                            attack_type=self._classify_ddos_type(traffic),
                            confidence_score=validation_score
                        )
                        anomalies.append(anomaly)
                        
                        # Reset traffic data to avoid duplicate detections
                        del destination_traffic[dest_key]
        
        return anomalies
    
    def _validate_ddos_indicators(self, traffic: Dict, packet_rate: float) -> float:
        """Multi-stage validation for DDoS attacks"""
        score = 0.0
        
        # Indicator 1: Packet rate severity
        if packet_rate > self.critical_threshold:
            score += 0.5
        elif packet_rate > self.high_threshold:
            score += 0.3
        else:
            score += 0.1
        
        # Indicator 2: Source IP diversity (distributed attack)
        source_diversity = len(traffic['source_ips'])
        if source_diversity > 100:  # Highly distributed
            score += 0.3
        elif source_diversity > 10:  # Moderately distributed
            score += 0.2
        else:  # Low distribution (possible single source)
            score += 0.1
        
        # Indicator 3: Traffic pattern analysis
        pattern_score = self._analyze_ddos_patterns(traffic['connections'])
        score += pattern_score * 0.2
        
        return min(score, 1.0)
    
    def _classify_ddos_type(self, traffic: Dict) -> str:
        """Classify the type of DDoS attack"""
        source_count = len(traffic['source_ips'])
        avg_packet_size = traffic['byte_count'] / max(traffic['packet_count'], 1)
        
        # Analyze connection patterns
        protocols = set(conn['protocol'] for conn in traffic['connections'])
        
        if source_count > 100:
            if avg_packet_size < 100:
                return "VOLUMETRIC_FLOOD"  # High volume, small packets
            else:
                return "AMPLIFICATION_ATTACK"  # Fewer but larger packets
        elif source_count > 10:
            if 'TCP' in protocols:
                return "SYN_FLOOD"  # TCP-based attack
            elif 'UDP' in protocols:
                return "UDP_FLOOD"  # UDP-based attack
            else:
                return "PROTOCOL_ATTACK"
        else:
            return "SINGLE_SOURCE_FLOOD"  # Low source diversity
    
    def _analyze_ddos_patterns(self, connections: List[Dict]) -> float:
        """Analyze traffic patterns for DDoS characteristics"""
        if len(connections) < 10:
            return 0.0
        
        score = 0.0
        
        # Pattern 1: Consistent packet sizes (indicates automated attack)
        packet_sizes = [conn['packets'] for conn in connections]
        if len(set(packet_sizes)) < len(packet_sizes) * 0.3:  # Low variance
            score += 0.3
        
        # Pattern 2: Rapid succession of connections
        timestamps = [conn['timestamp'] for conn in connections]
        if len(timestamps) > 1:
            time_intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                time_intervals.append(interval)
            
            avg_interval = statistics.mean(time_intervals)
            if avg_interval < 1.0:  # Less than 1 second between connections
                score += 0.4
        
        # Pattern 3: High rejection rate (target overwhelmed)
        rejected_connections = sum(1 for conn in connections if conn['action'] == 'REJECT')
        rejection_rate = rejected_connections / len(connections)
        if rejection_rate > 0.7:  # High rejection rate
            score += 0.3
        
        return min(score, 1.0)