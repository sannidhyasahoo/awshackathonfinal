"""
C2 Beaconing Detection Algorithm
Detects Command and Control beaconing by analyzing periodic communication patterns.
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class C2BeaconingAnomaly:
    anomaly_id: str
    source_ip: str
    destination_ip: str
    destination_port: int
    connection_count: int
    mean_interval: float
    coefficient_variation: float
    confidence_score: float
    threat_type: str = "C2_BEACONING"
    detection_timestamp: datetime = None

    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()

class C2BeaconingDetector:
    def __init__(self,
                 min_connections: int = 10,
                 cv_threshold: float = 15.0,  # Coefficient of variation threshold
                 confidence_threshold: float = 0.8):
        self.min_connections = min_connections
        self.cv_threshold = cv_threshold
        self.confidence_threshold = confidence_threshold
    
    def detect(self, flow_logs: List[FlowLog]) -> List[C2BeaconingAnomaly]:
        """Detect C2 beaconing patterns in flow logs"""
        connection_patterns = defaultdict(list)
        anomalies = []
        
        # Group connections by source-destination pair
        for log in flow_logs:
            conn_key = f"{log.source_ip}->{log.destination_ip}:{log.destination_port}"
            connection_patterns[conn_key].append(log.timestamp)
        
        # Analyze each connection pattern
        for conn_key, timestamps in connection_patterns.items():
            if len(timestamps) >= self.min_connections:
                
                # Sort timestamps
                timestamps.sort()
                
                # Calculate intervals between connections
                intervals = []
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    intervals.append(interval)
                
                # Calculate coefficient of variation
                if len(intervals) > 1:
                    mean_interval = statistics.mean(intervals)
                    std_interval = statistics.stdev(intervals)
                    
                    if mean_interval > 0:
                        coefficient_variation = (std_interval / mean_interval) * 100
                        
                        # Check for beaconing pattern
                        if coefficient_variation < self.cv_threshold:
                            
                            # Multi-stage validation
                            validation_score = self._validate_beaconing_indicators(
                                intervals, mean_interval, coefficient_variation, timestamps
                            )
                            
                            if validation_score > self.confidence_threshold:
                                source_ip, dest_info = conn_key.split('->')
                                dest_ip, dest_port = dest_info.split(':')
                                
                                anomaly = C2BeaconingAnomaly(
                                    anomaly_id=f"c2_{source_ip}_{dest_ip}_{int(timestamps[0].timestamp())}",
                                    source_ip=source_ip,
                                    destination_ip=dest_ip,
                                    destination_port=int(dest_port),
                                    connection_count=len(timestamps),
                                    mean_interval=mean_interval,
                                    coefficient_variation=coefficient_variation,
                                    confidence_score=validation_score
                                )
                                anomalies.append(anomaly)
        
        return anomalies
    
    def _validate_beaconing_indicators(self, intervals: List[float], 
                                     mean_interval: float, 
                                     cv: float,
                                     timestamps: List[datetime]) -> float:
        """Multi-stage validation for C2 beaconing"""
        score = 0.0
        
        # Indicator 1: Regularity (lower CV = more regular = more suspicious)
        if cv < 5:  # Very regular
            score += 0.5
        elif cv < 10:  # Moderately regular
            score += 0.3
        elif cv < 15:  # Somewhat regular
            score += 0.2
        
        # Indicator 2: Reasonable beacon interval (not too fast/slow)
        if 60 <= mean_interval <= 3600:  # 1 minute to 1 hour (typical C2)
            score += 0.3
        elif 30 <= mean_interval <= 7200:  # 30 seconds to 2 hours
            score += 0.2
        elif 10 <= mean_interval <= 14400:  # 10 seconds to 4 hours
            score += 0.1
        
        # Indicator 3: Persistence (long-running pattern)
        total_duration = (timestamps[-1] - timestamps[0]).total_seconds()
        if total_duration > 3600:  # More than 1 hour
            score += 0.2
        elif total_duration > 1800:  # More than 30 minutes
            score += 0.1
        
        # Indicator 4: Consistent timing patterns
        timing_consistency = self._analyze_timing_consistency(intervals)
        score += timing_consistency * 0.1
        
        return min(score, 1.0)
    
    def _analyze_timing_consistency(self, intervals: List[float]) -> float:
        """Analyze consistency of timing intervals"""
        if len(intervals) < 5:
            return 0.0
        
        # Look for patterns in intervals
        # Check if intervals cluster around specific values
        interval_buckets = defaultdict(int)
        
        for interval in intervals:
            # Round to nearest 10 seconds for bucketing
            bucket = round(interval / 10) * 10
            interval_buckets[bucket] += 1
        
        # Calculate consistency score based on bucket distribution
        max_bucket_count = max(interval_buckets.values())
        consistency_ratio = max_bucket_count / len(intervals)
        
        # Higher consistency indicates more regular beaconing
        return min(consistency_ratio * 2, 1.0)