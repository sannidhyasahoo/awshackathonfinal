"""
ThreatClassifierAgent Business Logic
Core threat classification algorithms and decision logic
"""

import json
import boto3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ThreatSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ThreatType(Enum):
    PORT_SCAN = "port_scan"
    DDOS = "ddos"
    C2_BEACON = "c2_beacon"
    CRYPTO_MINING = "crypto_mining"
    TOR_USAGE = "tor_usage"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    UNKNOWN = "unknown"

@dataclass
class ThreatClassification:
    """Threat classification result"""
    is_threat: bool
    severity: ThreatSeverity
    confidence: float
    threat_type: ThreatType
    mitre_techniques: List[str]
    reasoning: str
    recommended_actions: List[str]
    evidence_summary: Dict[str, Any]

class ThreatClassifierEngine:
    """Core threat classification engine"""
    
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-agent-runtime')
        self.mitre_mappings = self._load_mitre_mappings()
        
    def classify_anomaly(self, anomaly_data: Dict[str, Any], context_data: Dict[str, Any]) -> ThreatClassification:
        """Main classification method"""
        
        # Step 1: Rule-based initial screening
        initial_assessment = self._rule_based_screening(anomaly_data)
        
        # Step 2: AI-driven detailed analysis (if needed)
        if initial_assessment['confidence'] < 0.8:
            ai_assessment = self._ai_driven_analysis(anomaly_data, context_data)
            final_assessment = self._merge_assessments(initial_assessment, ai_assessment)
        else:
            final_assessment = initial_assessment
        
        # Step 3: MITRE ATT&CK mapping
        mitre_techniques = self._map_to_mitre(final_assessment['threat_type'], anomaly_data)
        
        # Step 4: Generate recommendations
        recommendations = self._generate_recommendations(final_assessment, context_data)
        
        return ThreatClassification(
            is_threat=final_assessment['is_threat'],
            severity=ThreatSeverity(final_assessment['severity']),
            confidence=final_assessment['confidence'],
            threat_type=ThreatType(final_assessment['threat_type']),
            mitre_techniques=mitre_techniques,
            reasoning=final_assessment['reasoning'],
            recommended_actions=recommendations,
            evidence_summary=final_assessment['evidence']
        )
    
    def _rule_based_screening(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based threat pattern matching"""
        
        anomaly_type = anomaly_data.get('anomaly_type', '')
        source_ip = anomaly_data.get('source_ip', '')
        dest_ports = anomaly_data.get('destination_ports', [])
        connection_count = anomaly_data.get('connection_count', 0)
        
        # Port scanning detection
        if anomaly_type == 'port_scan' or len(dest_ports) > 20:
            return {
                'is_threat': True,
                'severity': 'MEDIUM',
                'confidence': 0.85,
                'threat_type': 'port_scan',
                'reasoning': f'Port scanning detected: {len(dest_ports)} unique ports accessed',
                'evidence': {'ports_scanned': len(dest_ports), 'source_ip': source_ip}
            }
        
        # DDoS detection
        if anomaly_type == 'ddos' or connection_count > 10000:
            severity = 'CRITICAL' if connection_count > 50000 else 'HIGH'
            return {
                'is_threat': True,
                'severity': severity,
                'confidence': 0.9,
                'threat_type': 'ddos',
                'reasoning': f'DDoS attack detected: {connection_count} connections per minute',
                'evidence': {'connection_rate': connection_count, 'attack_type': 'volumetric'}
            }
        
        # C2 beaconing detection
        if anomaly_type == 'c2_beacon':
            return {
                'is_threat': True,
                'severity': 'HIGH',
                'confidence': 0.8,
                'threat_type': 'c2_beacon',
                'reasoning': 'Regular periodic connections indicating C2 communication',
                'evidence': {'beacon_pattern': True, 'regularity_score': anomaly_data.get('regularity_score')}
            }
        
        # Crypto mining detection
        mining_ports = [3333, 4444, 9999, 8333, 14444]
        if any(port in mining_ports for port in dest_ports):
            return {
                'is_threat': True,
                'severity': 'MEDIUM',
                'confidence': 0.75,
                'threat_type': 'crypto_mining',
                'reasoning': 'Connection to known cryptocurrency mining ports',
                'evidence': {'mining_ports': [p for p in dest_ports if p in mining_ports]}
            }
        
        # Default: requires AI analysis
        return {
            'is_threat': False,
            'severity': 'LOW',
            'confidence': 0.3,
            'threat_type': 'unknown',
            'reasoning': 'Anomaly requires detailed AI analysis',
            'evidence': {'anomaly_type': anomaly_type}
        }
    
    def _ai_driven_analysis(self, anomaly_data: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered threat analysis using Bedrock"""
        
        # Prepare prompt for Claude
        analysis_prompt = self._build_analysis_prompt(anomaly_data, context_data)
        
        try:
            response = self.bedrock_client.invoke_agent(
                agentId='threat-classifier-agent-id',
                agentAliasId='TSTALIASID',
                sessionId=f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                inputText=analysis_prompt
            )
            
            # Parse AI response
            ai_result = self._parse_ai_response(response)
            return ai_result
            
        except Exception as e:
            # Fallback to conservative assessment
            return {
                'is_threat': True,
                'severity': 'MEDIUM',
                'confidence': 0.5,
                'threat_type': 'unknown',
                'reasoning': f'AI analysis failed, using conservative assessment: {str(e)}',
                'evidence': {'ai_error': str(e)}
            }
    
    def _build_analysis_prompt(self, anomaly_data: Dict[str, Any], context_data: Dict[str, Any]) -> str:
        """Build structured prompt for AI analysis"""
        
        prompt = f"""
        Analyze this network security anomaly:
        
        ANOMALY DATA:
        - Type: {anomaly_data.get('anomaly_type')}
        - Source IP: {anomaly_data.get('source_ip')}
        - Destination IPs: {anomaly_data.get('destination_ips', [])}
        - Ports: {anomaly_data.get('destination_ports', [])}
        - Time Window: {anomaly_data.get('time_window')}
        - Connection Count: {anomaly_data.get('connection_count')}
        - Data Volume: {anomaly_data.get('data_volume_mb')} MB
        
        CONTEXT DATA:
        - Resource Type: {context_data.get('resource_type')}
        - Environment: {context_data.get('environment')}
        - Business Hours: {context_data.get('business_hours')}
        - Baseline Behavior: {context_data.get('baseline_summary')}
        - Threat Intelligence: {context_data.get('threat_intel_matches')}
        
        Provide your assessment in this exact format:
        THREAT: [true/false]
        SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
        CONFIDENCE: [0-100]
        TYPE: [port_scan/ddos/c2_beacon/crypto_mining/tor_usage/lateral_movement/data_exfiltration/unknown]
        REASONING: [Your detailed analysis]
        """
        
        return prompt
    
    def _parse_ai_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured AI response"""
        
        # Extract response text
        response_text = response.get('completion', '')
        
        # Parse structured fields
        lines = response_text.split('\n')
        result = {}
        
        for line in lines:
            if line.startswith('THREAT:'):
                result['is_threat'] = 'true' in line.lower()
            elif line.startswith('SEVERITY:'):
                result['severity'] = line.split(':')[1].strip()
            elif line.startswith('CONFIDENCE:'):
                result['confidence'] = float(line.split(':')[1].strip()) / 100
            elif line.startswith('TYPE:'):
                result['threat_type'] = line.split(':')[1].strip()
            elif line.startswith('REASONING:'):
                result['reasoning'] = line.split(':', 1)[1].strip()
        
        result['evidence'] = {'ai_analysis': True, 'model': 'claude-3.5-sonnet'}
        return result
    
    def _merge_assessments(self, rule_based: Dict[str, Any], ai_based: Dict[str, Any]) -> Dict[str, Any]:
        """Merge rule-based and AI assessments"""
        
        # Use higher confidence assessment as primary
        if rule_based['confidence'] >= ai_based['confidence']:
            primary = rule_based
            secondary = ai_based
        else:
            primary = ai_based
            secondary = rule_based
        
        # Merge evidence
        merged_evidence = {**primary['evidence'], **secondary['evidence']}
        
        # Combine reasoning
        merged_reasoning = f"{primary['reasoning']} | AI Analysis: {secondary['reasoning']}"
        
        return {
            **primary,
            'evidence': merged_evidence,
            'reasoning': merged_reasoning,
            'confidence': max(primary['confidence'], secondary['confidence'] * 0.8)
        }
    
    def _map_to_mitre(self, threat_type: str, anomaly_data: Dict[str, Any]) -> List[str]:
        """Map threat type to MITRE ATT&CK techniques"""
        
        mappings = {
            'port_scan': ['T1046'],  # Network Service Scanning
            'ddos': ['T1498', 'T1499'],  # Network/Endpoint DoS
            'c2_beacon': ['T1071', 'T1573'],  # Application Layer Protocol, Encrypted Channel
            'crypto_mining': ['T1496'],  # Resource Hijacking
            'tor_usage': ['T1090'],  # Proxy
            'lateral_movement': ['T1021', 'T1210'],  # Remote Services, Exploitation of Remote Services
            'data_exfiltration': ['T1041', 'T1048']  # Exfiltration Over C2 Channel, Exfiltration Over Alternative Protocol
        }
        
        return mappings.get(threat_type, ['T1190'])  # Default: Exploit Public-Facing Application
    
    def _generate_recommendations(self, assessment: Dict[str, Any], context_data: Dict[str, Any]) -> List[str]:
        """Generate specific recommended actions"""
        
        threat_type = assessment['threat_type']
        severity = assessment['severity']
        
        base_recommendations = []
        
        if severity in ['CRITICAL', 'HIGH']:
            base_recommendations.extend([
                "Initiate immediate investigation",
                "Consider isolation of affected resources",
                "Alert security operations center"
            ])
        
        # Threat-specific recommendations
        if threat_type == 'port_scan':
            base_recommendations.extend([
                "Block source IP at firewall/WAF",
                "Review exposed services and ports",
                "Check for successful exploitation attempts"
            ])
        elif threat_type == 'ddos':
            base_recommendations.extend([
                "Activate DDoS mitigation (AWS Shield)",
                "Scale infrastructure if needed",
                "Implement rate limiting"
            ])
        elif threat_type == 'c2_beacon':
            base_recommendations.extend([
                "Block C2 domains/IPs",
                "Isolate infected systems",
                "Scan for malware and persistence mechanisms"
            ])
        elif threat_type == 'crypto_mining':
            base_recommendations.extend([
                "Terminate unauthorized mining processes",
                "Check for privilege escalation",
                "Review resource utilization patterns"
            ])
        
        return base_recommendations
    
    def _load_mitre_mappings(self) -> Dict[str, Any]:
        """Load MITRE ATT&CK framework mappings"""
        # In production, this would load from knowledge base
        return {
            "techniques": {},
            "tactics": {},
            "last_updated": datetime.now().isoformat()
        }