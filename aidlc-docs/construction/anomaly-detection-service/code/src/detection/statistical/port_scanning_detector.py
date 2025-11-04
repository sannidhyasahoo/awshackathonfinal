"""
Port Scanning Detection Algorithm
Detects port scanning attacks by analyzing connection patterns to multiple ports from single sources.
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FlowLog:
    timestamp: datetime
    source_ip: str
    destination_ip: str
    destination_port: int
    protocol: str
    action: str
    packets: int
    bytes: int

@dataclass
class PortScanAnomaly:
    anomaly_id: str
    source_ip: str
    unique_ports: int
    time_window: float
    connections: List[Dict]
    confidence_score: float
    threat_type: str = "PORT_SCANNING"
    detection_timestamp: datetime = None

    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()

class PortScanningDetector:
    def __init__(self, 
                 port_threshold: int = 20,
                 time_window: int = 60,
                 confidence_threshold: float = 0.8):
        self.port_threshold = port_threshold
        self.time_window = time_window
        self.confidence_threshold = confidence_threshold
        
    def detect(self, flow_logs: List[FlowLog]) -> List[PortScanAnomaly]:
        """Detect port scanning patterns in flow logs"""
        port_scan_candidates = {}
        anomalies = []
        
        for log in flow_logs:
            source_ip = log.source_ip
            dest_port = log.destination_port
            timestamp = log.timestamp
            
            # Initialize tracking for new source IPs
            if source_ip not in port_scan_candidates:
                port_scan_candidates[source_ip] = {
                    'unique_ports': set(),
                    'first_seen': timestamp,
                    'connections': []
                }
            
            candidate = port_scan_candidates[source_ip]
            
            # Add port to unique set
            candidate['unique_ports'].add(dest_port)
            candidate['connections'].append({
                'dest_ip': log.destination_ip,
                'dest_port': dest_port,
                'timestamp': timestamp,
                'action': log.action,
                'protocol': log.protocol
            })
            
            # Check if within time window and threshold exceeded
            time_diff = (timestamp - candidate['first_seen']).total_seconds()
            if time_diff <= self.time_window and len(candidate['unique_ports']) > self.port_threshold:
                
                # Multi-stage validation
                validation_score = self._validate_port_scan_indicators(candidate)
                if validation_score > self.confidence_threshold:
                    
                    anomaly = PortScanAnomaly(
                        anomaly_id=f"ps_{source_ip}_{int(timestamp.timestamp())}",
                        source_ip=source_ip,
                        unique_ports=len(candidate['unique_ports']),
                        time_window=time_diff,
                        connections=candidate['connections'].copy(),
                        confidence_score=validation_score
                    )
                    anomalies.append(anomaly)
                    
                    # Reset candidate to avoid duplicate detections
                    del port_scan_candidates[source_ip]
        
        return anomalies
    
    def _validate_port_scan_indicators(self, candidate: Dict) -> float:
        """Multi-stage validation for port scanning"""
        score = 0.0
        
        # Indicator 1: Port diversity (higher diversity = more suspicious)
        port_diversity = self._calculate_port_diversity(candidate['unique_ports'])
        score += port_diversity * 0.3
        
        # Indicator 2: Connection success rate (low success = scanning)
        success_rate = self._calculate_connection_success_rate(candidate['connections'])
        if success_rate < 0.1:  # Less than 10% successful connections
            score += 0.4
        
        # Indicator 3: Sequential port patterns (common in scanning)
        sequential_score = self._detect_sequential_patterns(candidate['unique_ports'])
        score += sequential_score * 0.3
        
        return min(score, 1.0)
    
    def _calculate_port_diversity(self, ports: Set[int]) -> float:
        """Calculate port diversity score"""
        if len(ports) < 5:
            return 0.0
        
        # Check for well-known ports vs random ports
        well_known_ports = {21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995}
        well_known_count = len(ports.intersection(well_known_ports))
        
        # Higher diversity score for mix of well-known and random ports
        diversity_ratio = well_known_count / len(ports)
        if 0.2 <= diversity_ratio <= 0.8:  # Good mix indicates scanning
            return 0.8
        elif diversity_ratio < 0.2:  # Mostly random ports
            return 0.6
        else:  # Mostly well-known ports
            return 0.4
    
    def _calculate_connection_success_rate(self, connections: List[Dict]) -> float:
        """Calculate connection success rate"""
        if not connections:
            return 0.0
        
        successful_connections = sum(1 for conn in connections if conn['action'] == 'ACCEPT')
        return successful_connections / len(connections)
    
    def _detect_sequential_patterns(self, ports: Set[int]) -> float:
        """Detect sequential port scanning patterns"""
        if len(ports) < 5:
            return 0.0
        
        sorted_ports = sorted(ports)
        sequential_count = 0
        
        for i in range(len(sorted_ports) - 1):
            if sorted_ports[i + 1] - sorted_ports[i] == 1:
                sequential_count += 1
        
        # Higher score for more sequential patterns
        sequential_ratio = sequential_count / (len(sorted_ports) - 1)
        return min(sequential_ratio * 2, 1.0)  # Cap at 1.0