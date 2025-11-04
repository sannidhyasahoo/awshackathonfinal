"""
ML Model Manager
Manages ML model lifecycle, health monitoring, and fallback strategies.
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from .isolation_forest_model import IsolationForestModel
from .lstm_model import LSTMModel

@dataclass
class ModelHealth:
    model_name: str
    is_healthy: bool
    last_check: datetime
    error_count: int
    response_time: float

class MLModelManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.models = {}
        self.model_health = {}
        
        # Initialize Isolation Forest
        if config.get('isolation_forest', {}).get('enabled', True):
            self.models['isolation_forest'] = IsolationForestModel(
                endpoint_name=config['isolation_forest']['endpoint_name'],
                region=config.get('region', 'us-east-1')
            )
            self.model_health['isolation_forest'] = ModelHealth(
                model_name='isolation_forest',
                is_healthy=True,
                last_check=datetime.utcnow(),
                error_count=0,
                response_time=0.0
            )
        
        # Initialize LSTM
        if config.get('lstm', {}).get('enabled', True):
            self.models['lstm'] = LSTMModel(
                endpoint_name=config['lstm']['endpoint_name'],
                sequence_length=config['lstm'].get('sequence_length', 50),
                region=config.get('region', 'us-east-1')
            )
            self.model_health['lstm'] = ModelHealth(
                model_name='lstm',
                is_healthy=True,
                last_check=datetime.utcnow(),
                error_count=0,
                response_time=0.0
            )
        
        # Health check interval
        self.health_check_interval = config.get('health_check_interval', 300)  # 5 minutes
        self.max_error_count = config.get('max_error_count', 5)
        
    def get_model(self, model_type: str):
        """Get model instance with health checking"""
        if model_type not in self.models:
            self.logger.warning(f"Model type {model_type} not available")
            return None
        
        model = self.models[model_type]
        health = self.model_health[model_type]
        
        # Check if health check is needed
        time_since_check = (datetime.utcnow() - health.last_check).total_seconds()
        if time_since_check > self.health_check_interval:
            self._perform_health_check(model_type)
        
        # Return model if healthy
        if health.is_healthy and health.error_count < self.max_error_count:
            return model
        else:
            self.logger.warning(f"Model {model_type} is unhealthy (errors: {health.error_count})")
            return None
    
    def detect_ml_anomalies(self, flow_logs: List[Dict]) -> List[Any]:
        """Detect anomalies using available ML models"""
        all_anomalies = []
        
        # Try Isolation Forest
        isolation_forest = self.get_model('isolation_forest')
        if isolation_forest:
            try:
                start_time = time.time()
                iso_anomalies = isolation_forest.detect_anomalies(flow_logs)
                response_time = time.time() - start_time
                
                all_anomalies.extend(iso_anomalies)
                self._update_model_metrics('isolation_forest', True, response_time)
                
            except Exception as e:
                self.logger.error(f"Isolation Forest detection failed: {e}")
                self._update_model_metrics('isolation_forest', False, 0.0)
        
        # Try LSTM
        lstm_model = self.get_model('lstm')
        if lstm_model:
            try:
                start_time = time.time()
                lstm_anomalies = lstm_model.detect_baseline_deviations(flow_logs)
                response_time = time.time() - start_time
                
                all_anomalies.extend(lstm_anomalies)
                self._update_model_metrics('lstm', True, response_time)
                
            except Exception as e:
                self.logger.error(f"LSTM detection failed: {e}")
                self._update_model_metrics('lstm', False, 0.0)
        
        return all_anomalies
    
    def _perform_health_check(self, model_type: str):
        """Perform health check on specific model"""
        if model_type not in self.models:
            return
        
        model = self.models[model_type]
        health = self.model_health[model_type]
        
        try:
            start_time = time.time()
            is_healthy = model.health_check()
            response_time = time.time() - start_time
            
            health.is_healthy = is_healthy
            health.last_check = datetime.utcnow()
            health.response_time = response_time
            
            if is_healthy:
                health.error_count = max(0, health.error_count - 1)  # Reduce error count on success
            else:
                health.error_count += 1
                
            self.logger.info(f"Health check for {model_type}: {'PASS' if is_healthy else 'FAIL'} "
                           f"(response_time: {response_time:.2f}s, errors: {health.error_count})")
            
        except Exception as e:
            health.is_healthy = False
            health.last_check = datetime.utcnow()
            health.error_count += 1
            self.logger.error(f"Health check failed for {model_type}: {e}")
    
    def _update_model_metrics(self, model_type: str, success: bool, response_time: float):
        """Update model performance metrics"""
        if model_type not in self.model_health:
            return
        
        health = self.model_health[model_type]
        health.response_time = response_time
        
        if success:
            health.error_count = max(0, health.error_count - 1)
        else:
            health.error_count += 1
            health.is_healthy = False
    
    def get_model_status(self) -> Dict[str, Dict]:
        """Get status of all models"""
        status = {}
        
        for model_type, health in self.model_health.items():
            status[model_type] = {
                'is_healthy': health.is_healthy,
                'last_check': health.last_check.isoformat(),
                'error_count': health.error_count,
                'response_time': health.response_time,
                'is_available': model_type in self.models and self.models[model_type].is_available
            }
        
        return status
    
    def perform_all_health_checks(self):
        """Perform health checks on all models"""
        for model_type in self.models.keys():
            self._perform_health_check(model_type)
    
    def reset_model_errors(self, model_type: str):
        """Reset error count for specific model"""
        if model_type in self.model_health:
            self.model_health[model_type].error_count = 0
            self.model_health[model_type].is_healthy = True
            self.logger.info(f"Reset error count for {model_type}")
    
    def disable_model(self, model_type: str):
        """Temporarily disable a model"""
        if model_type in self.models:
            self.models[model_type].is_available = False
            self.model_health[model_type].is_healthy = False
            self.logger.warning(f"Disabled model {model_type}")
    
    def enable_model(self, model_type: str):
        """Re-enable a model"""
        if model_type in self.models:
            self.models[model_type].is_available = True
            self.reset_model_errors(model_type)
            self._perform_health_check(model_type)
            self.logger.info(f"Enabled model {model_type}")