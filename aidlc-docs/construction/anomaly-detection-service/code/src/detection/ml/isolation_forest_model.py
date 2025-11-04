"""
Isolation Forest ML Model Integration
Provides wrapper for SageMaker-hosted Isolation Forest model for network anomaly detection.
"""

import json
import boto3
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

@dataclass
class MLAnomaly:
    anomaly_id: str
    flow_log: Dict
    anomaly_score: float
    model_type: str
    confidence: float
    threat_type: str
    detection_timestamp: datetime = None

    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()

class IsolationForestModel:
    def __init__(self, endpoint_name: str, region: str = 'us-east-1'):
        self.endpoint_name = endpoint_name
        self.sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=region)
        self.is_available = True
        self.logger = logging.getLogger(__name__)
        
    def detect_anomalies(self, flow_logs: List[Dict]) -> List[MLAnomaly]:
        """Detect anomalies using SageMaker Isolation Forest model"""
        if not self.is_available:
            self.logger.warning("Isolation Forest model not available")
            return []
        
        try:
            # Extract features from flow logs
            features = self._extract_features(flow_logs)
            if not features:
                return []
            
            # Prepare input for SageMaker endpoint
            input_data = {
                'instances': features
            }
            
            # Call SageMaker endpoint
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(input_data)
            )
            
            # Parse response
            result = json.loads(response['Body'].read().decode())
            predictions = result.get('predictions', [])
            
            # Convert predictions to anomalies
            anomalies = []
            for i, (prediction, log) in enumerate(zip(predictions, flow_logs)):
                if prediction['anomaly'] == -1:  # Anomaly detected
                    anomaly = MLAnomaly(
                        anomaly_id=f"iso_{log.get('source_ip', 'unknown')}_{int(datetime.utcnow().timestamp())}_{i}",
                        flow_log=log,
                        anomaly_score=abs(prediction['score']),
                        model_type="IsolationForest",
                        confidence=self._calculate_confidence(prediction['score']),
                        threat_type="ML_BEHAVIORAL_ANOMALY"
                    )
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Isolation Forest inference failed: {e}")
            self.is_available = False
            return []
    
    def _extract_features(self, flow_logs: List[Dict]) -> List[List[float]]:
        """Extract numerical features for ML model"""
        features = []
        
        for log in flow_logs:
            try:
                feature_vector = [
                    float(log.get('bytes', 0)),
                    float(log.get('packets', 0)),
                    float(log.get('bytes', 0)) / max(float(log.get('packets', 1)), 1),  # Bytes per packet
                    float(log.get('destination_port', 0)),
                    self._encode_protocol(log.get('protocol', 'TCP')),
                    self._encode_time_features(log.get('timestamp', datetime.utcnow())),
                    self._calculate_flow_duration(log),
                    self._encode_action(log.get('action', 'ACCEPT'))
                ]
                features.append(feature_vector)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Feature extraction failed for log: {e}")
                continue
        
        return features
    
    def _encode_protocol(self, protocol: str) -> float:
        """Encode protocol as numerical value"""
        protocol_map = {
            'TCP': 1.0,
            'UDP': 2.0,
            'ICMP': 3.0,
            'GRE': 4.0
        }
        return protocol_map.get(protocol.upper(), 0.0)
    
    def _encode_time_features(self, timestamp) -> float:
        """Encode timestamp as hour of day"""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.utcnow()
        
        return float(timestamp.hour)
    
    def _calculate_flow_duration(self, log: Dict) -> float:
        """Calculate flow duration (simplified)"""
        # In real implementation, this would use start/end timestamps
        return float(log.get('duration', 0))
    
    def _encode_action(self, action: str) -> float:
        """Encode action as numerical value"""
        action_map = {
            'ACCEPT': 1.0,
            'REJECT': 0.0
        }
        return action_map.get(action.upper(), 0.5)
    
    def _calculate_confidence(self, anomaly_score: float) -> float:
        """Calculate confidence score from anomaly score"""
        # Normalize anomaly score to confidence (0-1)
        return min(abs(anomaly_score) / 0.5, 1.0)
    
    def health_check(self) -> bool:
        """Check if model endpoint is healthy"""
        try:
            # Simple health check with minimal data
            test_features = [[100.0, 1.0, 100.0, 80.0, 1.0, 12.0, 0.0, 1.0]]
            input_data = {'instances': test_features}
            
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(input_data)
            )
            
            self.is_available = True
            return True
            
        except Exception as e:
            self.logger.error(f"Isolation Forest health check failed: {e}")
            self.is_available = False
            return False