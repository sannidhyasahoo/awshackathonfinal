"""
Multi-Stage Validation Engine
Validates anomalies through multiple stages to achieve <5% false positive rate.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

@dataclass
class ValidationResult:
    is_valid: bool
    confidence_score: float
    validation_stages: Dict[str, bool]
    failure_reasons: List[str]
    validation_metadata: Dict[str, Any]

@dataclass
class ValidatedAnomaly:
    correlation_group: Any
    confidence_score: float
    validation_result: ValidationResult
    final_threat_assessment: Dict[str, Any]
    validation_timestamp: datetime = None

    def __post_init__(self):
        if self.validation_timestamp is None:
            self.validation_timestamp = datetime.utcnow()

class MultiStageValidationEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Validation thresholds
        self.min_confidence_threshold = config.get('min_confidence', 0.8)
        self.false_positive_threshold = config.get('false_positive_threshold', 0.05)
        
        # Whitelist configurations
        self.whitelisted_ips = set(config.get('whitelisted_ips', []))
        self.whitelisted_subnets = set(config.get('whitelisted_subnets', []))
        self.trusted_domains = set(config.get('trusted_domains', []))
        
        # Business hours and context
        self.business_hours = config.get('business_hours', {'start': 8, 'end': 18})
        self.weekend_factor = config.get('weekend_factor', 0.8)  # Reduce threshold on weekends
        
        # Threat-specific validation rules
        self.threat_validation_rules = {
            'PORT_SCANNING': {
                'min_ports': 10,
                'max_false_positive_rate': 0.03,
                'require_multiple_destinations': True
            },
            'DDOS': {
                'min_packet_rate': 500,
                'min_source_diversity': 5,
                'max_false_positive_rate': 0.02
            },
            'C2_BEACONING': {
                'min_regularity': 0.8,
                'min_duration': 300,  # 5 minutes
                'max_false_positive_rate': 0.04
            },
            'CRYPTO_MINING': {
                'min_connection_duration': 60,
                'min_data_volume': 1024,
                'max_false_positive_rate': 0.05
            },
            'TOR_USAGE': {
                'min_tor_indicators': 2,
                'max_false_positive_rate': 0.03
            }
        }
    
    def validate_correlation_groups(self, correlation_groups: List[Any]) -> List[ValidatedAnomaly]:
        """Apply multi-stage validation to correlation groups"""
        validated_anomalies = []
        
        for group in correlation_groups:
            validation_result = self._apply_multistage_validation(group)
            
            if validation_result.is_valid:
                group_confidence = self._calculate_group_confidence(group)
                
                if group_confidence >= self.min_confidence_threshold:
                    threat_assessment = self._assess_threat_level(group, group_confidence)
                    
                    validated_anomaly = ValidatedAnomaly(
                        correlation_group=group,
                        confidence_score=group_confidence,
                        validation_result=validation_result,
                        final_threat_assessment=threat_assessment
                    )
                    validated_anomalies.append(validated_anomaly)
        
        return validated_anomalies
    
    def _apply_multistage_validation(self, group: Any) -> ValidationResult:
        """Apply multi-stage validation process"""
        validation_stages = {}
        failure_reasons = []
        validation_metadata = {}
        
        # Stage 1: Whitelist validation
        stage1_result = self._stage1_whitelist_validation(group)
        validation_stages['whitelist'] = stage1_result['passed']
        if not stage1_result['passed']:
            failure_reasons.extend(stage1_result['reasons'])
        validation_metadata['whitelist'] = stage1_result['metadata']
        
        # Stage 2: Contextual validation
        stage2_result = self._stage2_contextual_validation(group)
        validation_stages['contextual'] = stage2_result['passed']
        if not stage2_result['passed']:
            failure_reasons.extend(stage2_result['reasons'])
        validation_metadata['contextual'] = stage2_result['metadata']
        
        # Stage 3: Threat-specific validation
        stage3_result = self._stage3_threat_specific_validation(group)
        validation_stages['threat_specific'] = stage3_result['passed']
        if not stage3_result['passed']:
            failure_reasons.extend(stage3_result['reasons'])
        validation_metadata['threat_specific'] = stage3_result['metadata']
        
        # Stage 4: Historical pattern validation
        stage4_result = self._stage4_historical_validation(group)
        validation_stages['historical'] = stage4_result['passed']
        if not stage4_result['passed']:
            failure_reasons.extend(stage4_result['reasons'])
        validation_metadata['historical'] = stage4_result['metadata']
        
        # Overall validation result
        all_stages_passed = all(validation_stages.values())
        confidence_score = self._calculate_validation_confidence(validation_stages, validation_metadata)
        
        return ValidationResult(
            is_valid=all_stages_passed,
            confidence_score=confidence_score,
            validation_stages=validation_stages,
            failure_reasons=failure_reasons,
            validation_metadata=validation_metadata
        )
    
    def _stage1_whitelist_validation(self, group: Any) -> Dict[str, Any]:
        """Stage 1: Whitelist and trusted entity validation"""
        result = {'passed': True, 'reasons': [], 'metadata': {}}
        
        primary_anomaly = group.primary_anomaly
        
        # Check source IP whitelist
        source_ip = getattr(primary_anomaly, 'source_ip', None)
        if source_ip:
            if source_ip in self.whitelisted_ips:
                result['passed'] = False
                result['reasons'].append(f"Source IP {source_ip} is whitelisted")
            
            # Check subnet whitelist
            for subnet in self.whitelisted_subnets:
                if self._ip_in_subnet(source_ip, subnet):
                    result['passed'] = False
                    result['reasons'].append(f"Source IP {source_ip} in whitelisted subnet {subnet}")
        
        # Check destination whitelist
        dest_ip = getattr(primary_anomaly, 'destination_ip', getattr(primary_anomaly, 'target_ip', None))
        if dest_ip:
            if dest_ip in self.whitelisted_ips:
                result['passed'] = False
                result['reasons'].append(f"Destination IP {dest_ip} is whitelisted")
        
        result['metadata'] = {
            'source_ip_checked': source_ip,
            'destination_ip_checked': dest_ip,
            'whitelist_matches': len(result['reasons'])
        }
        
        return result
    
    def _stage2_contextual_validation(self, group: Any) -> Dict[str, Any]:
        """Stage 2: Business context and timing validation"""
        result = {'passed': True, 'reasons': [], 'metadata': {}}
        
        primary_anomaly = group.primary_anomaly
        detection_time = getattr(primary_anomaly, 'detection_timestamp', datetime.utcnow())
        
        # Business hours context
        hour = detection_time.hour
        is_business_hours = self.business_hours['start'] <= hour <= self.business_hours['end']
        is_weekend = detection_time.weekday() >= 5
        
        # Adjust validation based on context
        context_factor = 1.0
        if not is_business_hours:
            context_factor *= 0.9  # Slightly more suspicious outside business hours
        if is_weekend:
            context_factor *= self.weekend_factor
        
        # Check for legitimate business activity patterns
        threat_type = getattr(primary_anomaly, 'threat_type', 'UNKNOWN')
        
        if threat_type == 'PORT_SCANNING' and is_business_hours and not is_weekend:
            # Port scanning during business hours might be legitimate network scanning
            confidence = getattr(primary_anomaly, 'confidence_score', 1.0)
            if confidence < 0.9:  # Lower confidence during business hours
                result['passed'] = False
                result['reasons'].append("Port scanning during business hours with low confidence")
        
        result['metadata'] = {
            'detection_hour': hour,
            'is_business_hours': is_business_hours,
            'is_weekend': is_weekend,
            'context_factor': context_factor
        }
        
        return result
    
    def _stage3_threat_specific_validation(self, group: Any) -> Dict[str, Any]:
        """Stage 3: Threat-specific validation rules"""
        result = {'passed': True, 'reasons': [], 'metadata': {}}
        
        primary_anomaly = group.primary_anomaly
        threat_type = getattr(primary_anomaly, 'threat_type', 'UNKNOWN')
        
        if threat_type not in self.threat_validation_rules:
            result['metadata']['validation_rule'] = 'none'
            return result
        
        rules = self.threat_validation_rules[threat_type]
        result['metadata']['validation_rule'] = threat_type
        
        # Apply threat-specific validation
        if threat_type == 'PORT_SCANNING':
            unique_ports = getattr(primary_anomaly, 'unique_ports', 0)
            if unique_ports < rules['min_ports']:
                result['passed'] = False
                result['reasons'].append(f"Port scanning: insufficient ports ({unique_ports} < {rules['min_ports']})")
        
        elif threat_type == 'DDOS':
            packet_rate = getattr(primary_anomaly, 'packet_rate', 0)
            source_count = getattr(primary_anomaly, 'source_count', 0)
            
            if packet_rate < rules['min_packet_rate']:
                result['passed'] = False
                result['reasons'].append(f"DDoS: insufficient packet rate ({packet_rate} < {rules['min_packet_rate']})")
            
            if source_count < rules['min_source_diversity']:
                result['passed'] = False
                result['reasons'].append(f"DDoS: insufficient source diversity ({source_count} < {rules['min_source_diversity']})")
        
        elif threat_type == 'C2_BEACONING':
            cv = getattr(primary_anomaly, 'coefficient_variation', 100)
            connection_count = getattr(primary_anomaly, 'connection_count', 0)
            
            regularity = 1.0 - (cv / 100.0)  # Convert CV to regularity score
            if regularity < rules['min_regularity']:
                result['passed'] = False
                result['reasons'].append(f"C2 beaconing: insufficient regularity ({regularity:.2f} < {rules['min_regularity']})")
        
        elif threat_type == 'CRYPTO_MINING':
            connection_count = getattr(primary_anomaly, 'connection_count', 0)
            data_volume = getattr(primary_anomaly, 'data_volume', 0)
            
            if data_volume < rules['min_data_volume']:
                result['passed'] = False
                result['reasons'].append(f"Crypto mining: insufficient data volume ({data_volume} < {rules['min_data_volume']})")
        
        elif threat_type == 'TOR_USAGE':
            tor_nodes = getattr(primary_anomaly, 'tor_nodes', [])
            if len(tor_nodes) < rules['min_tor_indicators']:
                result['passed'] = False
                result['reasons'].append(f"Tor usage: insufficient indicators ({len(tor_nodes)} < {rules['min_tor_indicators']})")
        
        return result
    
    def _stage4_historical_validation(self, group: Any) -> Dict[str, Any]:
        """Stage 4: Historical pattern and false positive validation"""
        result = {'passed': True, 'reasons': [], 'metadata': {}}
        
        primary_anomaly = group.primary_anomaly
        source_ip = getattr(primary_anomaly, 'source_ip', None)
        threat_type = getattr(primary_anomaly, 'threat_type', 'UNKNOWN')
        
        # Check historical false positive rate for this source
        if source_ip:
            historical_fp_rate = self._get_historical_false_positive_rate(source_ip, threat_type)
            
            if threat_type in self.threat_validation_rules:
                max_fp_rate = self.threat_validation_rules[threat_type]['max_false_positive_rate']
                
                if historical_fp_rate > max_fp_rate:
                    result['passed'] = False
                    result['reasons'].append(f"Historical false positive rate too high ({historical_fp_rate:.3f} > {max_fp_rate})")
            
            result['metadata']['historical_fp_rate'] = historical_fp_rate
        
        # Check for repeated patterns that might indicate false positives
        pattern_score = self._analyze_pattern_repetition(group)
        if pattern_score > 0.8:  # High repetition might indicate false positive
            result['passed'] = False
            result['reasons'].append(f"High pattern repetition score ({pattern_score:.2f})")
        
        result['metadata']['pattern_repetition_score'] = pattern_score
        
        return result
    
    def _calculate_group_confidence(self, group: Any) -> float:
        """Calculate overall confidence for correlation group"""
        if not hasattr(group, 'related_anomalies'):
            return getattr(group.primary_anomaly, 'confidence_score', 0.5)
        
        if not group.related_anomalies:
            return getattr(group.primary_anomaly, 'confidence_score', 0.5)
        
        # Multi-anomaly group confidence calculation
        primary_confidence = getattr(group.primary_anomaly, 'confidence_score', 0.5)
        
        # Average confidence of related anomalies
        related_confidences = []
        for related in group.related_anomalies:
            anomaly = related['anomaly']
            confidence = getattr(anomaly, 'confidence_score', 0.5)
            correlation_score = related['correlation_score']
            
            # Weight by correlation score
            weighted_confidence = confidence * correlation_score
            related_confidences.append(weighted_confidence)
        
        if related_confidences:
            avg_related_confidence = sum(related_confidences) / len(related_confidences)
            # Combine primary and related confidences
            group_confidence = (primary_confidence * 0.6) + (avg_related_confidence * 0.4)
        else:
            group_confidence = primary_confidence
        
        # Correlation bonus
        correlation_bonus = min(len(group.related_anomalies) * 0.05, 0.2)
        
        return min(group_confidence + correlation_bonus, 1.0)
    
    def _calculate_validation_confidence(self, stages: Dict[str, bool], metadata: Dict[str, Any]) -> float:
        """Calculate confidence based on validation stages"""
        stage_weights = {
            'whitelist': 0.3,
            'contextual': 0.2,
            'threat_specific': 0.3,
            'historical': 0.2
        }
        
        confidence = 0.0
        for stage, passed in stages.items():
            if passed:
                confidence += stage_weights.get(stage, 0.0)
        
        return confidence
    
    def _assess_threat_level(self, group: Any, confidence: float) -> Dict[str, Any]:
        """Assess final threat level and priority"""
        primary_anomaly = group.primary_anomaly
        threat_type = getattr(primary_anomaly, 'threat_type', 'UNKNOWN')
        
        # Base severity from threat type
        threat_severity_map = {
            'DDOS': 'HIGH',
            'C2_BEACONING': 'HIGH',
            'PORT_SCANNING': 'MEDIUM',
            'CRYPTO_MINING': 'MEDIUM',
            'TOR_USAGE': 'LOW',
            'ML_BEHAVIORAL_ANOMALY': 'MEDIUM',
            'BEHAVIORAL_DEVIATION': 'LOW'
        }
        
        base_severity = threat_severity_map.get(threat_type, 'LOW')
        
        # Adjust based on confidence and correlation
        if confidence > 0.9:
            severity_modifier = 1
        elif confidence > 0.8:
            severity_modifier = 0
        else:
            severity_modifier = -1
        
        # Adjust based on correlation group size
        group_size = 1 + len(getattr(group, 'related_anomalies', []))
        if group_size > 3:
            severity_modifier += 1
        
        # Final severity calculation
        severity_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        base_index = severity_levels.index(base_severity)
        final_index = max(0, min(len(severity_levels) - 1, base_index + severity_modifier))
        final_severity = severity_levels[final_index]
        
        return {
            'severity': final_severity,
            'priority': self._calculate_priority(final_severity, confidence),
            'threat_type': threat_type,
            'confidence': confidence,
            'group_size': group_size,
            'assessment_timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_priority(self, severity: str, confidence: float) -> int:
        """Calculate numeric priority (1-10, higher = more urgent)"""
        severity_scores = {'LOW': 2, 'MEDIUM': 5, 'HIGH': 8, 'CRITICAL': 10}
        base_score = severity_scores.get(severity, 1)
        
        # Adjust by confidence
        confidence_modifier = int((confidence - 0.5) * 4)  # -2 to +2
        
        return max(1, min(10, base_score + confidence_modifier))
    
    def _ip_in_subnet(self, ip: str, subnet: str) -> bool:
        """Check if IP is in subnet (simplified)"""
        try:
            if '/' not in subnet:
                return ip == subnet
            
            network, prefix = subnet.split('/')
            prefix = int(prefix)
            
            # Simple /24 subnet check for demo
            if prefix == 24:
                return ip.rsplit('.', 1)[0] == network.rsplit('.', 1)[0]
            
            return False
        except Exception:
            return False
    
    def _get_historical_false_positive_rate(self, source_ip: str, threat_type: str) -> float:
        """Get historical false positive rate (simplified implementation)"""
        # In production, this would query historical data
        # For demo, return simulated rates
        return 0.02  # 2% default false positive rate
    
    def _analyze_pattern_repetition(self, group: Any) -> float:
        """Analyze pattern repetition to detect potential false positives"""
        # Simplified pattern analysis
        # In production, this would analyze detailed patterns
        return 0.3  # Default low repetition score