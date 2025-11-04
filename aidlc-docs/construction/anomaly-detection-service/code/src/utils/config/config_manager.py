"""
Configuration Management Component
Dynamic configuration with AWS Systems Manager Parameter Store
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)

@dataclass
class DetectionThresholds:
    """Detection algorithm thresholds"""
    port_scan_threshold: int = 50
    ddos_pps_threshold: int = 10000
    c2_beacon_interval_variance: float = 0.1
    crypto_mining_connection_threshold: int = 100
    tor_exit_node_confidence: float = 0.8

@dataclass
class MLModelConfig:
    """ML model configuration"""
    isolation_forest_contamination: float = 0.1
    lstm_sequence_length: int = 10
    model_update_interval_hours: int = 24
    confidence_threshold: float = 0.7
    canary_traffic_percentage: int = 10

@dataclass
class ValidationConfig:
    """Validation engine configuration"""
    whitelist_check_enabled: bool = True
    contextual_validation_enabled: bool = True
    threat_specific_validation_enabled: bool = True
    historical_validation_enabled: bool = True
    false_positive_threshold: float = 0.05

@dataclass
class ProcessingConfig:
    """Processing tier configuration"""
    statistical_timeout_seconds: int = 30
    ml_timeout_seconds: int = 120
    correlation_timeout_seconds: int = 60
    validation_timeout_seconds: int = 30
    max_concurrent_processing: int = 100

@dataclass
class InfrastructureConfig:
    """Infrastructure service configuration"""
    sagemaker_endpoint_name: str = ""
    elasticache_cluster_endpoint: str = ""
    eventbridge_bus_name: str = ""
    s3_model_bucket: str = ""
    dynamodb_table_name: str = ""

@dataclass
class ServiceConfig:
    """Complete service configuration"""
    detection_thresholds: DetectionThresholds = field(default_factory=DetectionThresholds)
    ml_model_config: MLModelConfig = field(default_factory=MLModelConfig)
    validation_config: ValidationConfig = field(default_factory=ValidationConfig)
    processing_config: ProcessingConfig = field(default_factory=ProcessingConfig)
    infrastructure_config: InfrastructureConfig = field(default_factory=InfrastructureConfig)
    
    # Service metadata
    service_name: str = "anomaly-detection-service"
    environment: str = "production"
    version: str = "1.0.0"
    log_level: str = "INFO"

class ConfigManager:
    """AWS Systems Manager Parameter Store configuration manager"""
    
    def __init__(self, parameter_prefix: str = "/anomaly-detection-service"):
        self.parameter_prefix = parameter_prefix
        self.ssm_client = boto3.client('ssm')
        self._config_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)
        
    async def load_config(self) -> ServiceConfig:
        """Load complete service configuration"""
        try:
            # Load all parameters with prefix
            parameters = await self._get_parameters_by_path(self.parameter_prefix)
            
            # Parse configuration sections
            config_dict = self._parse_parameters(parameters)
            
            # Create configuration object
            config = ServiceConfig()
            
            # Update detection thresholds
            if 'detection_thresholds' in config_dict:
                config.detection_thresholds = DetectionThresholds(**config_dict['detection_thresholds'])
            
            # Update ML model config
            if 'ml_model_config' in config_dict:
                config.ml_model_config = MLModelConfig(**config_dict['ml_model_config'])
            
            # Update validation config
            if 'validation_config' in config_dict:
                config.validation_config = ValidationConfig(**config_dict['validation_config'])
            
            # Update processing config
            if 'processing_config' in config_dict:
                config.processing_config = ProcessingConfig(**config_dict['processing_config'])
            
            # Update infrastructure config
            if 'infrastructure_config' in config_dict:
                config.infrastructure_config = InfrastructureConfig(**config_dict['infrastructure_config'])
            
            # Update service metadata
            for key in ['service_name', 'environment', 'version', 'log_level']:
                if key in config_dict:
                    setattr(config, key, config_dict[key])
            
            logger.info("Configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Return default configuration on error
            return ServiceConfig()
    
    async def get_parameter(self, parameter_name: str, use_cache: bool = True) -> Optional[str]:
        """Get single parameter value"""
        full_name = f"{self.parameter_prefix}/{parameter_name}"
        
        # Check cache first
        if use_cache and self._is_cached_and_valid(full_name):
            return self._config_cache[full_name]
        
        try:
            response = self.ssm_client.get_parameter(
                Name=full_name,
                WithDecryption=True
            )
            
            value = response['Parameter']['Value']
            
            # Update cache
            if use_cache:
                self._config_cache[full_name] = value
                self._cache_expiry[full_name] = datetime.utcnow() + self._cache_ttl
            
            return value
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning(f"Parameter not found: {full_name}")
                return None
            else:
                logger.error(f"Error getting parameter {full_name}: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error getting parameter {full_name}: {e}")
            return None
    
    async def set_parameter(self, parameter_name: str, value: str, parameter_type: str = "String") -> bool:
        """Set parameter value"""
        full_name = f"{self.parameter_prefix}/{parameter_name}"
        
        try:
            self.ssm_client.put_parameter(
                Name=full_name,
                Value=value,
                Type=parameter_type,
                Overwrite=True
            )
            
            # Update cache
            self._config_cache[full_name] = value
            self._cache_expiry[full_name] = datetime.utcnow() + self._cache_ttl
            
            logger.info(f"Parameter set successfully: {full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting parameter {full_name}: {e}")
            return False
    
    async def _get_parameters_by_path(self, path: str) -> Dict[str, str]:
        """Get all parameters under a path"""
        parameters = {}
        next_token = None
        
        try:
            while True:
                kwargs = {
                    'Path': path,
                    'Recursive': True,
                    'WithDecryption': True,
                    'MaxResults': 10
                }
                
                if next_token:
                    kwargs['NextToken'] = next_token
                
                response = self.ssm_client.get_parameters_by_path(**kwargs)
                
                for param in response['Parameters']:
                    # Remove prefix from parameter name
                    key = param['Name'][len(path):].lstrip('/')
                    parameters[key] = param['Value']
                
                next_token = response.get('NextToken')
                if not next_token:
                    break
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error getting parameters by path {path}: {e}")
            return {}
    
    def _parse_parameters(self, parameters: Dict[str, str]) -> Dict[str, Any]:
        """Parse flat parameter structure into nested configuration"""
        config_dict = {}
        
        for key, value in parameters.items():
            # Parse JSON values
            try:
                parsed_value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Keep as string if not valid JSON
                parsed_value = value
            
            # Handle nested keys (e.g., "detection_thresholds/port_scan_threshold")
            if '/' in key:
                parts = key.split('/')
                current = config_dict
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                current[parts[-1]] = parsed_value
            else:
                config_dict[key] = parsed_value
        
        return config_dict
    
    def _is_cached_and_valid(self, parameter_name: str) -> bool:
        """Check if parameter is cached and not expired"""
        if parameter_name not in self._config_cache:
            return False
        
        if parameter_name not in self._cache_expiry:
            return False
        
        return datetime.utcnow() < self._cache_expiry[parameter_name]
    
    def clear_cache(self):
        """Clear configuration cache"""
        self._config_cache.clear()
        self._cache_expiry.clear()
        logger.info("Configuration cache cleared")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get configuration manager health status"""
        try:
            # Test SSM connectivity
            self.ssm_client.describe_parameters(MaxResults=1)
            
            return {
                'status': 'healthy',
                'parameter_prefix': self.parameter_prefix,
                'cache_size': len(self._config_cache),
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'parameter_prefix': self.parameter_prefix,
                'last_check': datetime.utcnow().isoformat()
            }

class ConfigWatcher:
    """Watches for configuration changes and triggers reloads"""
    
    def __init__(self, config_manager: ConfigManager, reload_callback=None):
        self.config_manager = config_manager
        self.reload_callback = reload_callback
        self._watching = False
        self._last_check = datetime.utcnow()
    
    async def start_watching(self, check_interval_seconds: int = 300):
        """Start watching for configuration changes"""
        self._watching = True
        logger.info(f"Started configuration watching with {check_interval_seconds}s interval")
        
        # In a real implementation, this would use CloudWatch Events
        # or Parameter Store notifications for real-time updates
        # For now, it's a placeholder for the polling mechanism
    
    def stop_watching(self):
        """Stop watching for configuration changes"""
        self._watching = False
        logger.info("Stopped configuration watching")
    
    async def check_for_changes(self) -> bool:
        """Check if configuration has changed"""
        # Placeholder for change detection logic
        # In real implementation, would compare parameter versions
        # or use CloudWatch Events for notifications
        return False