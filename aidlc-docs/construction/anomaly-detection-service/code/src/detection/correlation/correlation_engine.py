"""
Multi-Dimensional Correlation Engine
Correlates anomalies across time, entity, and threat type dimensions.
"""

import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

@dataclass
class CorrelationGroup:
    group_id: str
    primary_anomaly: Any
    related_anomalies: List[Dict[str, Any]]
    correlation_scores: Dict[str, float]
    group_confidence: float
    creation_timestamp: datetime
    last_updated: datetime

    def add_related_anomaly(self, anomaly: Any, correlation_score: float):
        """Add related anomaly to the group"""
        self.related_anomalies.append({
            'anomaly': anomaly,
            'correlation_score': correlation_score,
            'added_timestamp': datetime.utcnow()
        })
        self.correlation_scores[getattr(anomaly, 'anomaly_id', str(id(anomaly)))] = correlation_score
        self.last_updated = datetime.utcnow()

class MultiDimensionalCorrelationEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Correlation parameters
        self.time_window = config.get('time_window', 300)  # 5 minutes
        self.entity_correlation_threshold = config.get('entity_threshold', 0.7)
        self.temporal_correlation_threshold = config.get('temporal_threshold', 0.6)
        self.threat_correlation_threshold = config.get('threat_threshold', 0.5)
        
        # Threat type correlation weights
        self.threat_correlation_weights = {
            'PORT_SCANNING': {'DDOS': 0.8, 'C2_BEACONING': 0.3, 'CRYPTO_MINING': 0.2},
            'DDOS': {'PORT_SCANNING': 0.8, 'CRYPTO_MINING': 0.2, 'TOR_USAGE': 0.3},
            'C2_BEACONING': {'CRYPTO_MINING': 0.6, 'TOR_USAGE': 0.7, 'PORT_SCANNING': 0.3},
            'CRYPTO_MINING': {'C2_BEACONING': 0.6, 'TOR_USAGE': 0.5, 'DDOS': 0.2},
            'TOR_USAGE': {'C2_BEACONING': 0.7, 'CRYPTO_MINING': 0.5, 'PORT_SCANNING': 0.4},
            'ML_BEHAVIORAL_ANOMALY': {'PORT_SCANNING': 0.5, 'DDOS': 0.5, 'C2_BEACONING': 0.6},
            'BEHAVIORAL_DEVIATION': {'C2_BEACONING': 0.7, 'CRYPTO_MINING': 0.6, 'TOR_USAGE': 0.5}
        }
    
    def correlate_anomalies(self, anomalies: List[Any]) -> List[CorrelationGroup]:
        """Perform multi-dimensional correlation of detected anomalies"""
        if len(anomalies) < 2:
            # Single anomaly - create individual group
            if anomalies:
                return [self._create_single_anomaly_group(anomalies[0])]
            return []
        
        correlation_groups = []
        processed_anomalies = set()
        
        # Sort anomalies by timestamp for temporal analysis
        sorted_anomalies = sorted(anomalies, key=lambda x: getattr(x, 'detection_timestamp', datetime.utcnow()))
        
        for i, anomaly in enumerate(sorted_anomalies):
            if i in processed_anomalies:
                continue
            
            # Start new correlation group
            group_id = f"corr_{int(datetime.utcnow().timestamp())}_{i}"
            correlation_group = CorrelationGroup(
                group_id=group_id,
                primary_anomaly=anomaly,
                related_anomalies=[],
                correlation_scores={},
                group_confidence=0.0,
                creation_timestamp=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            processed_anomalies.add(i)
            
            # Find related anomalies
            for j, other_anomaly in enumerate(sorted_anomalies[i+1:], i+1):
                if j in processed_anomalies:
                    continue
                
                correlation_score = self._calculate_correlation_score(anomaly, other_anomaly)
                
                if correlation_score > self.entity_correlation_threshold:
                    correlation_group.add_related_anomaly(other_anomaly, correlation_score)
                    processed_anomalies.add(j)
            
            # Calculate group confidence
            correlation_group.group_confidence = self._calculate_group_confidence(correlation_group)
            correlation_groups.append(correlation_group)
        
        return correlation_groups
    
    def _calculate_correlation_score(self, anomaly1: Any, anomaly2: Any) -> float:
        """Calculate multi-dimensional correlation score between two anomalies"""
        total_score = 0.0
        
        # Temporal correlation (40% weight)
        temporal_score = self._calculate_temporal_correlation(anomaly1, anomaly2)
        total_score += temporal_score * 0.4
        
        # Entity correlation (40% weight)
        entity_score = self._calculate_entity_correlation(anomaly1, anomaly2)
        total_score += entity_score * 0.4
        
        # Threat type correlation (20% weight)
        threat_score = self._calculate_threat_correlation(anomaly1, anomaly2)
        total_score += threat_score * 0.2
        
        return min(total_score, 1.0)
    
    def _calculate_temporal_correlation(self, anomaly1: Any, anomaly2: Any) -> float:
        """Calculate temporal correlation between anomalies"""
        timestamp1 = getattr(anomaly1, 'detection_timestamp', datetime.utcnow())
        timestamp2 = getattr(anomaly2, 'detection_timestamp', datetime.utcnow())
        
        time_diff = abs((timestamp1 - timestamp2).total_seconds())
        
        if time_diff <= self.time_window:
            # Linear decay within time window
            correlation = 1.0 - (time_diff / self.time_window)
            return max(correlation, 0.0)
        
        return 0.0
    
    def _calculate_entity_correlation(self, anomaly1: Any, anomaly2: Any) -> float:
        """Calculate entity-based correlation between anomalies"""
        similarity = 0.0
        
        # Source IP similarity
        source1 = getattr(anomaly1, 'source_ip', None)
        source2 = getattr(anomaly2, 'source_ip', None)
        if source1 and source2 and source1 == source2:
            similarity += 0.5
        
        # Destination IP similarity
        dest1 = getattr(anomaly1, 'destination_ip', getattr(anomaly1, 'target_ip', None))
        dest2 = getattr(anomaly2, 'destination_ip', getattr(anomaly2, 'target_ip', None))
        if dest1 and dest2 and dest1 == dest2:
            similarity += 0.3
        
        # Port similarity
        port1 = getattr(anomaly1, 'destination_port', getattr(anomaly1, 'target_port', None))
        port2 = getattr(anomaly2, 'destination_port', getattr(anomaly2, 'target_port', None))
        if port1 and port2 and port1 == port2:
            similarity += 0.2
        
        # Subnet correlation (same /24 network)
        if source1 and source2 and self._same_subnet(source1, source2):
            similarity += 0.1
        
        return min(similarity, 1.0)
    
    def _calculate_threat_correlation(self, anomaly1: Any, anomaly2: Any) -> float:
        """Calculate threat type correlation between anomalies"""
        threat1 = getattr(anomaly1, 'threat_type', 'UNKNOWN')
        threat2 = getattr(anomaly2, 'threat_type', 'UNKNOWN')
        
        if threat1 == threat2:
            return 1.0  # Same threat type
        
        # Check correlation weights
        if threat1 in self.threat_correlation_weights:
            weights = self.threat_correlation_weights[threat1]
            return weights.get(threat2, 0.0)
        
        return 0.0
    
    def _same_subnet(self, ip1: str, ip2: str, subnet_mask: int = 24) -> bool:
        """Check if two IPs are in the same subnet"""
        try:
            # Simple /24 subnet check
            parts1 = ip1.split('.')
            parts2 = ip2.split('.')
            
            if len(parts1) == 4 and len(parts2) == 4:
                # Compare first 3 octets for /24
                return parts1[:3] == parts2[:3]
        except Exception:
            pass
        
        return False
    
    def _calculate_group_confidence(self, group: CorrelationGroup) -> float:
        """Calculate overall confidence for correlation group"""
        if not group.related_anomalies:
            # Single anomaly group
            primary_confidence = getattr(group.primary_anomaly, 'confidence_score', 0.5)
            return primary_confidence
        
        # Multi-anomaly group
        total_score = 0.0
        total_weight = 0.0
        
        # Primary anomaly weight
        primary_confidence = getattr(group.primary_anomaly, 'confidence_score', 0.5)
        total_score += primary_confidence * 0.5
        total_weight += 0.5
        
        # Related anomalies weighted by correlation score
        for related in group.related_anomalies:
            anomaly = related['anomaly']
            correlation_score = related['correlation_score']
            anomaly_confidence = getattr(anomaly, 'confidence_score', 0.5)
            
            weight = correlation_score * 0.5 / len(group.related_anomalies)
            total_score += anomaly_confidence * weight
            total_weight += weight
        
        # Correlation bonus (more correlated anomalies = higher confidence)
        correlation_bonus = min(len(group.related_anomalies) * 0.1, 0.3)
        
        final_confidence = (total_score / total_weight) + correlation_bonus
        return min(final_confidence, 1.0)
    
    def _create_single_anomaly_group(self, anomaly: Any) -> CorrelationGroup:
        """Create correlation group for single anomaly"""
        group_id = f"single_{int(datetime.utcnow().timestamp())}_{id(anomaly)}"
        
        return CorrelationGroup(
            group_id=group_id,
            primary_anomaly=anomaly,
            related_anomalies=[],
            correlation_scores={},
            group_confidence=getattr(anomaly, 'confidence_score', 0.5),
            creation_timestamp=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
    
    def get_correlation_statistics(self, groups: List[CorrelationGroup]) -> Dict[str, Any]:
        """Get correlation statistics for analysis"""
        if not groups:
            return {}
        
        stats = {
            'total_groups': len(groups),
            'single_anomaly_groups': 0,
            'multi_anomaly_groups': 0,
            'avg_group_size': 0.0,
            'avg_confidence': 0.0,
            'threat_type_distribution': defaultdict(int),
            'correlation_strength_distribution': {
                'high': 0,  # > 0.8
                'medium': 0,  # 0.5 - 0.8
                'low': 0  # < 0.5
            }
        }
        
        total_anomalies = 0
        total_confidence = 0.0
        
        for group in groups:
            group_size = 1 + len(group.related_anomalies)
            total_anomalies += group_size
            total_confidence += group.group_confidence
            
            if group_size == 1:
                stats['single_anomaly_groups'] += 1
            else:
                stats['multi_anomaly_groups'] += 1
            
            # Threat type distribution
            primary_threat = getattr(group.primary_anomaly, 'threat_type', 'UNKNOWN')
            stats['threat_type_distribution'][primary_threat] += 1
            
            # Correlation strength
            if group.group_confidence > 0.8:
                stats['correlation_strength_distribution']['high'] += 1
            elif group.group_confidence > 0.5:
                stats['correlation_strength_distribution']['medium'] += 1
            else:
                stats['correlation_strength_distribution']['low'] += 1
        
        stats['avg_group_size'] = total_anomalies / len(groups)
        stats['avg_confidence'] = total_confidence / len(groups)
        
        return dict(stats)