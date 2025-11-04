"""
LSTM Model Integration
Provides wrapper for SageMaker-hosted LSTM model for behavioral baseline analysis.
"""

import json
import boto3
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

@dataclass
class BaselineDeviation:
    anomaly_id: str
    flow_log: Dict
    deviation_score: float
    baseline_value: float
    current_value: float
    model_type: str
    confidence: float
    threat_type: str = "BEHAVIORAL_DEVIATION"
    detection_timestamp: datetime = None

    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()

class LSTMModel:
    def __init__(self, endpoint_name: str, sequence_length: int = 50, region: str = 'us-east-1'):
        self.endpoint_name = endpoint_name
        self.sequence_length = sequence_length
        self.sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=region)
        self.is_available = True
        self.logger = logging.getLogger(__name__)
        
    def detect_baseline_deviations(self, flow_logs: List[Dict]) -> List[BaselineDeviation]:
        """Detect deviations from learned baseline behavior"""
        if not self.is_available:
            self.logger.warning("LSTM model not available")
            return []
        
        try:
            # Prepare sequences for LSTM
            sequences = self._prepare_sequences(flow_logs)
            if not sequences:
                return []
            
            # Prepare input for SageMaker endpoint
            input_data = {
                'instances': sequences
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
            
            # Calculate reconstruction errors and detect anomalies
            anomalies = []
            threshold = self._calculate_threshold(predictions)
            
            for i, (prediction, original_sequence) in enumerate(zip(predictions, sequences)):
                reconstruction_error = self._calculate_reconstruction_error(
                    original_sequence, prediction['reconstruction']
                )
                
                if reconstruction_error > threshold:
                    # Map back to original flow log
                    log_index = i + self.sequence_length
                    if log_index < len(flow_logs):
                        deviation = BaselineDeviation(
                            anomaly_id=f"lstm_{flow_logs[log_index].get('source_ip', 'unknown')}_{int(datetime.utcnow().timestamp())}_{i}",
                            flow_log=flow_logs[log_index],
                            deviation_score=reconstruction_error,
                            baseline_value=prediction.get('baseline', 0.0),
                            current_value=prediction.get('current', 0.0),
                            model_type="LSTM",
                            confidence=min(reconstruction_error / threshold, 1.0)
                        )
                        anomalies.append(deviation)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"LSTM inference failed: {e}")
            self.is_available = False
            return []
    
    def _prepare_sequences(self, flow_logs: List[Dict]) -> List[List[List[float]]]:
        """Prepare time series sequences for LSTM"""
        if len(flow_logs) < self.sequence_length:
            return []
        
        # Extract temporal features
        features = self._extract_temporal_features(flow_logs)
        if len(features) < self.sequence_length:
            return []
        
        # Create sequences
        sequences = []
        for i in range(len(features) - self.sequence_length + 1):
            sequence = features[i:i + self.sequence_length]
            sequences.append(sequence)
        
        return sequences
    
    def _extract_temporal_features(self, flow_logs: List[Dict]) -> List[List[float]]:
        """Extract temporal features for LSTM"""
        features = []
        
        # Sort logs by timestamp
        sorted_logs = sorted(flow_logs, key=lambda x: x.get('timestamp', datetime.utcnow()))
        
        for log in sorted_logs:
            try:
                timestamp = log.get('timestamp', datetime.utcnow())
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                feature_vector = [
                    float(log.get('bytes', 0)),
                    float(log.get('packets', 0)),
                    float(log.get('destination_port', 0)),
                    self._encode_protocol(log.get('protocol', 'TCP')),
                    float(timestamp.hour),  # Hour of day
                    float(timestamp.weekday()),  # Day of week
                    self._encode_action(log.get('action', 'ACCEPT')),
                    self._calculate_rate_features(log, sorted_logs)
                ]
                features.append(feature_vector)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Temporal feature extraction failed: {e}")
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
    
    def _encode_action(self, action: str) -> float:
        """Encode action as numerical value"""
        action_map = {
            'ACCEPT': 1.0,
            'REJECT': 0.0
        }
        return action_map.get(action.upper(), 0.5)
    
    def _calculate_rate_features(self, current_log: Dict, all_logs: List[Dict]) -> float:
        """Calculate rate-based features"""
        # Simple rate calculation based on recent activity
        current_time = current_log.get('timestamp', datetime.utcnow())
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        
        # Count logs in last minute
        recent_count = 0
        for log in all_logs:
            log_time = log.get('timestamp', datetime.utcnow())
            if isinstance(log_time, str):
                log_time = datetime.fromisoformat(log_time.replace('Z', '+00:00'))
            
            if (current_time - log_time).total_seconds() <= 60:
                recent_count += 1
        
        return float(recent_count)
    
    def _calculate_reconstruction_error(self, original: List[List[float]], 
                                     reconstruction: List[List[float]]) -> float:
        """Calculate reconstruction error between original and reconstructed sequences"""
        try:
            original_array = np.array(original)
            reconstruction_array = np.array(reconstruction)
            
            # Mean squared error
            mse = np.mean(np.square(original_array - reconstruction_array))
            return float(mse)
            
        except Exception as e:
            self.logger.warning(f"Reconstruction error calculation failed: {e}")
            return 0.0
    
    def _calculate_threshold(self, predictions: List[Dict]) -> float:
        """Calculate threshold for anomaly detection"""
        if not predictions:
            return 1.0
        
        # Use 95th percentile as threshold
        errors = []
        for pred in predictions:
            if 'reconstruction_error' in pred:
                errors.append(pred['reconstruction_error'])
        
        if errors:
            return float(np.percentile(errors, 95))
        else:
            return 1.0
    
    def health_check(self) -> bool:
        """Check if LSTM model endpoint is healthy"""
        try:
            # Create test sequence
            test_sequence = [
                [[100.0, 1.0, 80.0, 1.0, 12.0, 1.0, 1.0, 5.0] for _ in range(self.sequence_length)]
            ]
            
            input_data = {'instances': test_sequence}
            
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(input_data)
            )
            
            self.is_available = True
            return True
            
        except Exception as e:
            self.logger.error(f"LSTM health check failed: {e}")
            self.is_available = False
            return False