"""
SageMaker Model Management Component
Manages ML model lifecycle, deployment, and canary releases.
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

@dataclass
class ModelDeployment:
    model_name: str
    endpoint_name: str
    endpoint_config_name: str
    model_version: str
    deployment_status: str
    traffic_percentage: int
    deployment_timestamp: datetime
    health_status: str

@dataclass
class CanaryDeployment:
    primary_model: ModelDeployment
    canary_model: Optional[ModelDeployment]
    canary_start_time: datetime
    canary_duration: int
    success_criteria: Dict[str, float]
    current_metrics: Dict[str, float]
    status: str  # STARTING, MONITORING, PROMOTING, ROLLING_BACK, COMPLETED

class SageMakerModelManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # AWS clients
        self.sagemaker = boto3.client('sagemaker', region_name=config.get('region', 'us-east-1'))
        self.sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=config.get('region', 'us-east-1'))
        self.cloudwatch = boto3.client('cloudwatch', region_name=config.get('region', 'us-east-1'))
        
        # Model configuration
        self.model_registry_name = config.get('model_registry_name', 'anomaly-detection-models')
        self.execution_role = config.get('execution_role')
        self.instance_type = config.get('instance_type', 'ml.m5.large')
        
        # Canary deployment configuration
        self.canary_config = config.get('canary_config', {
            'initial_traffic_percentage': 10,
            'monitoring_duration': 3600,  # 1 hour
            'success_criteria': {
                'error_rate_threshold': 0.05,
                'latency_threshold': 500,
                'throughput_threshold': 0.8
            }
        })
        
        # Active deployments tracking
        self.active_deployments = {}
        self.canary_deployments = {}
    
    def deploy_model(self, model_name: str, model_uri: str, 
                    endpoint_name: str, deployment_type: str = 'canary') -> bool:
        """Deploy new model version with specified strategy"""
        try:
            if deployment_type == 'canary':
                return self._deploy_canary_model(model_name, model_uri, endpoint_name)
            elif deployment_type == 'blue_green':
                return self._deploy_blue_green_model(model_name, model_uri, endpoint_name)
            else:
                return self._deploy_direct_model(model_name, model_uri, endpoint_name)
                
        except Exception as e:
            self.logger.error(f"Model deployment failed for {model_name}: {e}")
            return False
    
    def _deploy_canary_model(self, model_name: str, model_uri: str, endpoint_name: str) -> bool:
        """Deploy model using canary strategy"""
        try:
            # Create new model
            model_timestamp = int(datetime.utcnow().timestamp())
            new_model_name = f"{model_name}-{model_timestamp}"
            
            self.sagemaker.create_model(
                ModelName=new_model_name,
                PrimaryContainer={
                    'Image': self._get_inference_image_uri(model_name),
                    'ModelDataUrl': model_uri,
                    'Environment': {
                        'SAGEMAKER_PROGRAM': 'inference.py',
                        'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/code'
                    }
                },
                ExecutionRoleArn=self.execution_role
            )
            
            # Check if endpoint exists
            try:
                endpoint_desc = self.sagemaker.describe_endpoint(EndpointName=endpoint_name)
                current_config = endpoint_desc['EndpointConfigName']
                
                # Create canary endpoint configuration
                canary_config_name = f"{endpoint_name}-canary-{model_timestamp}"
                
                # Get current production variant
                current_config_desc = self.sagemaker.describe_endpoint_config(
                    EndpointConfigName=current_config
                )
                
                production_variants = current_config_desc['ProductionVariants'].copy()
                
                # Update production variant traffic
                for variant in production_variants:
                    variant['InitialVariantWeight'] = 100 - self.canary_config['initial_traffic_percentage']
                
                # Add canary variant
                canary_variant = {
                    'VariantName': 'canary',
                    'ModelName': new_model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': self.instance_type,
                    'InitialVariantWeight': self.canary_config['initial_traffic_percentage']
                }
                production_variants.append(canary_variant)
                
                # Create new endpoint configuration
                self.sagemaker.create_endpoint_config(
                    EndpointConfigName=canary_config_name,
                    ProductionVariants=production_variants
                )
                
                # Update endpoint
                self.sagemaker.update_endpoint(
                    EndpointName=endpoint_name,
                    EndpointConfigName=canary_config_name
                )
                
            except self.sagemaker.exceptions.ClientError as e:
                if 'ValidationException' in str(e):
                    # Endpoint doesn't exist, create new one
                    return self._create_new_endpoint(model_name, new_model_name, endpoint_name)
                else:
                    raise e
            
            # Track canary deployment
            canary_deployment = CanaryDeployment(
                primary_model=self._get_current_primary_model(endpoint_name),
                canary_model=ModelDeployment(
                    model_name=new_model_name,
                    endpoint_name=endpoint_name,
                    endpoint_config_name=canary_config_name,
                    model_version=model_timestamp,
                    deployment_status='DEPLOYING',
                    traffic_percentage=self.canary_config['initial_traffic_percentage'],
                    deployment_timestamp=datetime.utcnow(),
                    health_status='UNKNOWN'
                ),
                canary_start_time=datetime.utcnow(),
                canary_duration=self.canary_config['monitoring_duration'],
                success_criteria=self.canary_config['success_criteria'],
                current_metrics={},
                status='STARTING'
            )
            
            self.canary_deployments[endpoint_name] = canary_deployment
            
            # Wait for deployment to complete
            self._wait_for_endpoint_update(endpoint_name)
            
            # Start monitoring
            canary_deployment.status = 'MONITORING'
            
            self.logger.info(f"Canary deployment started for {model_name} on {endpoint_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Canary deployment failed: {e}")
            return False
    
    def monitor_canary_deployments(self) -> Dict[str, str]:
        """Monitor active canary deployments and make promotion/rollback decisions"""
        results = {}
        
        for endpoint_name, canary in list(self.canary_deployments.items()):
            if canary.status not in ['MONITORING']:
                continue
            
            try:
                # Check if monitoring period is complete
                elapsed_time = (datetime.utcnow() - canary.canary_start_time).total_seconds()
                
                if elapsed_time >= canary.canary_duration:
                    # Monitoring period complete, make decision
                    decision = self._evaluate_canary_performance(endpoint_name, canary)
                    results[endpoint_name] = decision
                else:
                    # Continue monitoring
                    self._update_canary_metrics(endpoint_name, canary)
                    results[endpoint_name] = 'MONITORING'
                    
            except Exception as e:
                self.logger.error(f"Canary monitoring failed for {endpoint_name}: {e}")
                # Rollback on monitoring failure
                self._rollback_canary(endpoint_name, canary)
                results[endpoint_name] = 'ROLLED_BACK'
        
        return results
    
    def _evaluate_canary_performance(self, endpoint_name: str, canary: CanaryDeployment) -> str:
        """Evaluate canary performance and decide promotion or rollback"""
        try:
            # Get latest metrics
            self._update_canary_metrics(endpoint_name, canary)
            
            # Check success criteria
            criteria = canary.success_criteria
            metrics = canary.current_metrics
            
            # Error rate check
            if metrics.get('error_rate', 1.0) > criteria['error_rate_threshold']:
                self.logger.warning(f"Canary error rate too high: {metrics['error_rate']}")
                self._rollback_canary(endpoint_name, canary)
                return 'ROLLED_BACK'
            
            # Latency check
            if metrics.get('latency_p99', 1000) > criteria['latency_threshold']:
                self.logger.warning(f"Canary latency too high: {metrics['latency_p99']}")
                self._rollback_canary(endpoint_name, canary)
                return 'ROLLED_BACK'
            
            # Throughput check
            expected_throughput = metrics.get('expected_throughput', 1.0)
            actual_throughput = metrics.get('actual_throughput', 0.0)
            throughput_ratio = actual_throughput / expected_throughput if expected_throughput > 0 else 0
            
            if throughput_ratio < criteria['throughput_threshold']:
                self.logger.warning(f"Canary throughput too low: {throughput_ratio}")
                self._rollback_canary(endpoint_name, canary)
                return 'ROLLED_BACK'
            
            # All criteria passed, promote canary
            self._promote_canary(endpoint_name, canary)
            return 'PROMOTED'
            
        except Exception as e:
            self.logger.error(f"Canary evaluation failed: {e}")
            self._rollback_canary(endpoint_name, canary)
            return 'ROLLED_BACK'
    
    def _promote_canary(self, endpoint_name: str, canary: CanaryDeployment):
        """Promote canary to receive 100% traffic"""
        try:
            canary.status = 'PROMOTING'
            
            # Update endpoint configuration to give canary 100% traffic
            current_config = self.sagemaker.describe_endpoint(EndpointName=endpoint_name)['EndpointConfigName']
            config_desc = self.sagemaker.describe_endpoint_config(EndpointConfigName=current_config)
            
            # Create new config with canary as primary
            promotion_timestamp = int(datetime.utcnow().timestamp())
            promoted_config_name = f"{endpoint_name}-promoted-{promotion_timestamp}"
            
            promoted_variants = []
            for variant in config_desc['ProductionVariants']:
                if variant['VariantName'] == 'canary':
                    variant['InitialVariantWeight'] = 100
                    variant['VariantName'] = 'primary'
                    promoted_variants.append(variant)
            
            self.sagemaker.create_endpoint_config(
                EndpointConfigName=promoted_config_name,
                ProductionVariants=promoted_variants
            )
            
            self.sagemaker.update_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=promoted_config_name
            )
            
            # Wait for update to complete
            self._wait_for_endpoint_update(endpoint_name)
            
            canary.status = 'COMPLETED'
            
            # Clean up old model and configuration
            self._cleanup_old_deployment(endpoint_name, canary.primary_model)
            
            self.logger.info(f"Canary promoted successfully for {endpoint_name}")
            
        except Exception as e:
            self.logger.error(f"Canary promotion failed: {e}")
            canary.status = 'PROMOTION_FAILED'
    
    def _rollback_canary(self, endpoint_name: str, canary: CanaryDeployment):
        """Rollback canary deployment to previous version"""
        try:
            canary.status = 'ROLLING_BACK'
            
            # Revert to previous endpoint configuration
            if canary.primary_model and canary.primary_model.endpoint_config_name:
                self.sagemaker.update_endpoint(
                    EndpointName=endpoint_name,
                    EndpointConfigName=canary.primary_model.endpoint_config_name
                )
                
                # Wait for rollback to complete
                self._wait_for_endpoint_update(endpoint_name)
            
            # Clean up canary model and configuration
            if canary.canary_model:
                self._cleanup_canary_deployment(canary.canary_model)
            
            canary.status = 'ROLLED_BACK'
            
            self.logger.info(f"Canary rolled back successfully for {endpoint_name}")
            
        except Exception as e:
            self.logger.error(f"Canary rollback failed: {e}")
            canary.status = 'ROLLBACK_FAILED'
    
    def _update_canary_metrics(self, endpoint_name: str, canary: CanaryDeployment):
        """Update canary performance metrics from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=10)  # Last 10 minutes
            
            # Get error rate
            error_rate = self._get_cloudwatch_metric(
                'AWS/SageMaker',
                'ModelLatency',
                [{'Name': 'EndpointName', 'Value': endpoint_name},
                 {'Name': 'VariantName', 'Value': 'canary'}],
                start_time, end_time, 'Average'
            )
            
            # Get latency metrics
            latency_p99 = self._get_cloudwatch_metric(
                'AWS/SageMaker',
                'ModelLatency',
                [{'Name': 'EndpointName', 'Value': endpoint_name},
                 {'Name': 'VariantName', 'Value': 'canary'}],
                start_time, end_time, 'Maximum'
            )
            
            # Get invocation count for throughput
            invocation_count = self._get_cloudwatch_metric(
                'AWS/SageMaker',
                'Invocations',
                [{'Name': 'EndpointName', 'Value': endpoint_name},
                 {'Name': 'VariantName', 'Value': 'canary'}],
                start_time, end_time, 'Sum'
            )
            
            canary.current_metrics = {
                'error_rate': error_rate or 0.0,
                'latency_p99': latency_p99 or 0.0,
                'actual_throughput': (invocation_count or 0.0) / 600,  # Per second
                'expected_throughput': 10.0,  # Expected baseline
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update canary metrics: {e}")
    
    def _get_cloudwatch_metric(self, namespace: str, metric_name: str, 
                              dimensions: List[Dict], start_time: datetime, 
                              end_time: datetime, statistic: str) -> Optional[float]:
        """Get CloudWatch metric value"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=[statistic]
            )
            
            if response['Datapoints']:
                return response['Datapoints'][-1][statistic]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get CloudWatch metric: {e}")
            return None
    
    def _wait_for_endpoint_update(self, endpoint_name: str, timeout: int = 600):
        """Wait for endpoint update to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.sagemaker.describe_endpoint(EndpointName=endpoint_name)
                status = response['EndpointStatus']
                
                if status == 'InService':
                    return True
                elif status in ['Failed', 'RollingBack']:
                    raise Exception(f"Endpoint update failed with status: {status}")
                
                time.sleep(30)  # Wait 30 seconds before checking again
                
            except Exception as e:
                self.logger.error(f"Error checking endpoint status: {e}")
                raise e
        
        raise TimeoutError(f"Endpoint update timeout after {timeout} seconds")
    
    def _get_inference_image_uri(self, model_name: str) -> str:
        """Get inference container image URI"""
        # Return appropriate container image based on model type
        region = self.config.get('region', 'us-east-1')
        
        if 'isolation-forest' in model_name.lower():
            return f"246618743249.dkr.ecr.{region}.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
        elif 'lstm' in model_name.lower():
            return f"763104351884.dkr.ecr.{region}.amazonaws.com/tensorflow-inference:2.8-cpu"
        else:
            return f"246618743249.dkr.ecr.{region}.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get status of all deployments"""
        return {
            'active_deployments': len(self.active_deployments),
            'canary_deployments': {
                endpoint: {
                    'status': canary.status,
                    'traffic_percentage': canary.canary_model.traffic_percentage if canary.canary_model else 0,
                    'elapsed_time': (datetime.utcnow() - canary.canary_start_time).total_seconds(),
                    'current_metrics': canary.current_metrics
                }
                for endpoint, canary in self.canary_deployments.items()
            }
        }