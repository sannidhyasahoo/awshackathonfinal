"""
Tor Usage Detection Algorithm
Detects Tor network usage by analyzing connection patterns to known Tor nodes and relays.
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class TorUsageAnomaly:
    anomaly_id: str
    source_ip: str
    tor_nodes: List[str]
    connection_count: int
    tor_ports: Set[int]
    connection_pattern: str
    confidence_score: float
    threat_type: str = "TOR_USAGE"
    detection_timestamp: datetime = None

    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()

class TorUsageDetector:
    def __init__(self,
                 min_connections: int = 3,
                 confidence_threshold: float = 0.8):
        self.min_connections = min_connections
        self.confidence_threshold = confidence_threshold
        
        # Known Tor ports
        self.tor_ports = {
            9001, 9030, 9050, 9051, 9150,  # Standard Tor ports
            443, 80, 8080, 8443,           # Common Tor bridge ports
            9040, 9053, 9063, 9090         # Additional Tor ports
        }
        
        # Tor directory authority ports
        self.directory_ports = {9030, 80, 443}
        
        # Known Tor node IP patterns (simplified - in production use threat intelligence feeds)
        self.tor_ip_patterns = {
            # This would be populated with known Tor exit nodes, relays, and bridges
            # For demo purposes, using pattern matching
        }
    
    def detect(self, flow_logs: List[FlowLog]) -> List[TorUsageAnomaly]:
        """Detect Tor usage patterns in flow logs"""
        source_activities = defaultdict(lambda: {
            'connections': [],
            'tor_destinations': set(),
            'ports_used': set(),
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
                'protocol': log.protocol,
                'action': log.action
            })
            
            activity['ports_used'].add(log.destination_port)
            activity['protocols'].add(log.protocol)
            
            # Check if destination matches Tor patterns
            if self._is_potential_tor_node(log.destination_ip, log.destination_port):
                activity['tor_destinations'].add(f"{log.destination_ip}:{log.destination_port}")
        
        # Evaluate each source for Tor usage
        for source_ip, activity in source_activities.items():
            if (len(activity['connections']) >= self.min_connections and
                len(activity['tor_destinations']) > 0):
                
                # Multi-stage validation
                validation_score = self._validate_tor_indicators(activity)
                
                if validation_score > self.confidence_threshold:
                    connection_pattern = self._classify_tor_usage_pattern(activity)
                    
                    anomaly = TorUsageAnomaly(
                        anomaly_id=f"tor_{source_ip}_{int(time.time())}",
                        source_ip=source_ip,
                        tor_nodes=list(activity['tor_destinations']),
                        connection_count=len(activity['connections']),
                        tor_ports=activity['ports_used'].intersection(self.tor_ports),
                        connection_pattern=connection_pattern,
                        confidence_score=validation_score
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _is_potential_tor_node(self, dest_ip: str, dest_port: int) -> bool:
        """Check if destination matches Tor node patterns"""
        # Check port patterns
        if dest_port in self.tor_ports:
            return True
        
        # Check for Tor-like connection patterns
        # In production, this would use threat intelligence feeds
        # For demo, using heuristic patterns
        
        # Check for common Tor bridge ports on HTTPS
        if dest_port == 443 and self._looks_like_tor_bridge(dest_ip):
            return True
        
        # Check for obfuscated Tor traffic on common ports
        if dest_port in {80, 8080, 8443} and self._has_tor_characteristics(dest_ip):
            return True
        
        return False
    
    def _looks_like_tor_bridge(self, dest_ip: str) -> bool:
        """Heuristic check for Tor bridge characteristics"""
        # In production, use threat intelligence feeds
        # For demo, using simple heuristics
        
        # Check if IP is in common cloud provider ranges (bridges often hosted there)
        ip_parts = dest_ip.split('.')
        if len(ip_parts) == 4:
            try:
                first_octet = int(ip_parts[0])
                # Common cloud provider IP ranges (simplified)
                if first_octet in {3, 13, 15, 18, 34, 35, 52, 54}:  # AWS, GCP ranges
                    return True
            except ValueError:
                pass
        
        return False
    
    def _has_tor_characteristics(self, dest_ip: str) -> bool:
        """Check for Tor-like characteristics in IP"""
        # This would use threat intelligence in production
        # For demo, using basic heuristics
        return False  # Simplified for demo
    
    def _validate_tor_indicators(self, activity: Dict) -> float:
        """Multi-stage validation for Tor usage"""
        score = 0.0
        
        # Indicator 1: Connection to known Tor ports
        tor_port_connections = sum(
            1 for conn in activity['connections'] 
            if conn['dest_port'] in self.tor_ports
        )
        if tor_port_connections > 0:
            score += min(tor_port_connections / len(activity['connections']) * 0.5, 0.4)
        
        # Indicator 2: Multiple destination diversity (Tor circuit building)
        unique_destinations = len(activity['tor_destinations'])
        if unique_destinations >= 3:  # Multiple Tor nodes
            score += 0.3
        elif unique_destinations >= 2:
            score += 0.2
        
        # Indicator 3: Connection timing patterns (Tor circuit establishment)
        timing_score = self._analyze_tor_timing_patterns(activity['connections'])
        score += timing_score * 0.2
        
        # Indicator 4: Traffic volume patterns (Tor has specific patterns)
        volume_score = self._analyze_tor_traffic_volume(activity['connections'])
        score += volume_score * 0.1
        
        return min(score, 1.0)
    
    def _analyze_tor_timing_patterns(self, connections: List[Dict]) -> float:
        """Analyze timing patterns typical of Tor usage"""
        if len(connections) < 3:
            return 0.0
        
        score = 0.0
        
        # Group connections by destination
        dest_connections = defaultdict(list)
        for conn in connections:
            dest_key = f"{conn['dest_ip']}:{conn['dest_port']}"
            dest_connections[dest_key].append(conn['timestamp'])
        
        # Pattern 1: Rapid initial connections (circuit building)
        all_timestamps = sorted([conn['timestamp'] for conn in connections])
        if len(all_timestamps) >= 3:
            # Check if first 3 connections happen within 30 seconds
            first_three_span = (all_timestamps[2] - all_timestamps[0]).total_seconds()
            if first_three_span <= 30:
                score += 0.5
        
        # Pattern 2: Periodic keep-alive connections
        for dest, timestamps in dest_connections.items():
            if len(timestamps) > 2:
                timestamps.sort()
                intervals = []
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    intervals.append(interval)
                
                # Check for regular intervals (Tor keep-alive)
                if intervals:
                    mean_interval = statistics.mean(intervals)
                    if 60 <= mean_interval <= 600:  # 1-10 minute intervals
                        score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_tor_traffic_volume(self, connections: List[Dict]) -> float:
        """Analyze traffic volume patterns typical of Tor"""
        if not connections:
            return 0.0
        
        score = 0.0
        
        # Pattern 1: Small initial handshake packets
        initial_connections = sorted(connections, key=lambda x: x['timestamp'])[:3]
        small_packet_count = sum(1 for conn in initial_connections if conn['bytes'] < 1000)
        
        if small_packet_count >= 2:  # Multiple small initial packets
            score += 0.4
        
        # Pattern 2: Mixed traffic sizes (typical of Tor multiplexing)
        byte_sizes = [conn['bytes'] for conn in connections if conn['bytes'] > 0]
        if len(byte_sizes) > 5:
            # Check for variety in packet sizes
            unique_size_ranges = set()
            for size in byte_sizes:
                if size < 100:
                    unique_size_ranges.add('small')
                elif size < 1000:
                    unique_size_ranges.add('medium')
                else:
                    unique_size_ranges.add('large')
            
            if len(unique_size_ranges) >= 2:  # Mixed sizes
                score += 0.3
        
        return min(score, 1.0)
    
    def _classify_tor_usage_pattern(self, activity: Dict) -> str:
        """Classify the type of Tor usage pattern"""
        ports_used = activity['ports_used']
        connection_count = len(activity['connections'])
        
        # Check for directory authority connections
        if ports_used.intersection(self.directory_ports):
            return "TOR_DIRECTORY_ACCESS"
        
        # Check for relay/exit node connections
        if 9001 in ports_used or 9030 in ports_used:
            return "TOR_RELAY_CONNECTION"
        
        # Check for SOCKS proxy usage
        if 9050 in ports_used or 9150 in ports_used:
            return "TOR_SOCKS_PROXY"
        
        # Check for bridge usage (obfuscated)
        if ports_used.intersection({443, 80, 8080, 8443}):
            return "TOR_BRIDGE_CONNECTION"
        
        # Multiple connections suggest circuit building
        if connection_count >= 5:
            return "TOR_CIRCUIT_BUILDING"
        
        return "TOR_GENERAL_USAGE"