# Logical Components - Anomaly Detection Service

## Component Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Anomaly Detection Service                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   API Gateway   │    │  Load Balancer  │    │ Security Layer  │              │
│  │   - Auth/Authz  │    │  - Traffic Dist │    │ - Encryption    │              │
│  │   - Rate Limit  │    │  - Health Check │    │ - Audit Logging │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│           │                       │                       │                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Processing Engine                                    │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │ │
│  │  │ Tier 1: Stats │  │ Tier 2: ML    │  │ Tier 3: Corr  │  │ Tier 4: Val │ │ │
│  │  │ - Port Scan   │  │ - Isolation F │  │ - Multi-Dim   │  │ - Multi-Stg │ │ │
│  │  │ - DDoS        │  │ - LSTM        │  │ - Time/Entity │  │ - Confidence│ │ │
│  │  │ - C2 Beacon   │  │ - Behavioral  │  │ - Threat Corr │  │ - Validation│ │ │
│  │  └───────────────┘  └───────────────┘  └───────────────┘  └─────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│           │                       │                       │                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │  Model Store    │    │ Correlation     │    │ Configuration   │              │
│  │  - ML Models    │    │ Engine State    │    │ Management      │              │
│  │  - Versioning   │    │ - Active Corr   │    │ - Thresholds    │              │
│  │  - A/B Testing  │    │ - Entity State  │    │ - Feature Flags │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Processing Components

### 1. Tiered Processing Engine

#### Tier 1: Statistical Analysis Component
```python
class StatisticalAnalysisComponent:
    """
    Fast statistical screening component for real-time threat detection
    """
    def __init__(self):
        self.detectors = {
            'port_scanning': PortScanningDetector(),
            'ddos': DDoSDetector(), 
            'c2_beaconing': C2BeaconingDetector(),
            'crypto_mining': CryptoMiningDetector(),
            'tor_usage': TorUsageDetector()
        }
        self.processing_timeout = 30  # seconds
        
    def process(self, flow_logs):
        """Process logs through statistical algorithms"""
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(detector.detect, flow_logs): threat_type
                for threat_type, detector in self.detectors.items()
            }
            
            for future in as_completed(futures, timeout=self.processing_timeout):
                threat_type = futures[future]
                try:
                    anomalies = future.result()
                    if anomalies:
                        results.extend(anomalies)
                except Exception as e:
                    logger.error(f"Statistical detection failed for {threat_type}: {e}")
        
        return results
```

#### Tier 2: ML Analysis Component
```python
class MLAnalysisComponent:
    """
    Machine learning analysis component for behavioral anomaly detection
    """
    def __init__(self):
        self.model_manager = MLModelManager()
        self.inference_cache = TTLCache(maxsize=100, ttl=300)
        self.processing_timeout = 120  # seconds
        
    def process(self, flow_logs, statistical_anomalies):
        """Process logs through ML models if statistical anomalies detected"""
        if not statistical_anomalies:
            return []
        
        ml_anomalies = []
        
        # Load models with caching
        isolation_forest = self.model_manager.get_model('isolation_forest')
        lstm_model = self.model_manager.get_model('lstm')
        
        try:
            # Isolation Forest analysis
            if isolation_forest.is_available():
                iso_anomalies = isolation_forest.detect_anomalies(flow_logs)
                ml_anomalies.extend(iso_anomalies)
            
            # LSTM behavioral analysis
            if lstm_model.is_available():
                lstm_anomalies = lstm_model.detect_baseline_deviations(flow_logs)
                ml_anomalies.extend(lstm_anomalies)
                
        except Exception as e:
            logger.error(f"ML analysis failed: {e}")
            # Graceful degradation - return statistical results only
        
        return ml_anomalies
```

#### Tier 3: Correlation Engine Component
```python
class CorrelationEngineComponent:
    """
    Multi-dimensional correlation component for anomaly relationship analysis
    """
    def __init__(self):
        self.correlation_state = CorrelationStateManager()
        self.correlation_algorithms = {
            'temporal': TemporalCorrelationAlgorithm(),
            'entity': EntityCorrelationAlgorithm(),
            'threat': ThreatTypeCorrelationAlgorithm()
        }
        self.processing_timeout = 180  # seconds
        
    def process(self, anomalies):
        """Correlate anomalies across multiple dimensions"""
        if len(anomalies) < 2:
            return anomalies  # No correlation needed
        
        correlation_groups = []
        processed_anomalies = set()
        
        for i, anomaly in enumerate(anomalies):
            if i in processed_anomalies:
                continue
                
            # Create new correlation group
            group = CorrelationGroup(primary_anomaly=anomaly)
            processed_anomalies.add(i)
            
            # Find related anomalies
            for j, other_anomaly in enumerate(anomalies[i+1:], i+1):
                if j in processed_anomalies:
                    continue
                
                correlation_score = self.calculate_correlation_score(anomaly, other_anomaly)
                
                if correlation_score > 0.7:  # High correlation threshold
                    group.add_related_anomaly(other_anomaly, correlation_score)
                    processed_anomalies.add(j)
            
            correlation_groups.append(group)
        
        return correlation_groups
```

#### Tier 4: Validation Component
```python
class ValidationComponent:
    """
    Multi-stage validation component for final anomaly confirmation
    """
    def __init__(self):
        self.validation_rules = ValidationRuleEngine()
        self.confidence_calculator = ConfidenceCalculator()
        self.false_positive_filter = FalsePositiveFilter()
        
    def process(self, correlation_groups):
        """Apply multi-stage validation to correlation groups"""
        validated_anomalies = []
        
        for group in correlation_groups:
            # Stage 1: Rule-based validation
            rule_validation = self.validation_rules.validate(group)
            if not rule_validation.is_valid:
                continue
            
            # Stage 2: Confidence scoring
            confidence_score = self.confidence_calculator.calculate(group)
            if confidence_score < 0.8:  # High confidence threshold
                continue
            
            # Stage 3: False positive filtering
            if self.false_positive_filter.is_false_positive(group):
                continue
            
            # Stage 4: Final threat assessment
            threat_assessment = self.assess_threat_level(group, confidence_score)
            
            validated_anomalies.append(ValidatedAnomaly(
                correlation_group=group,
                confidence_score=confidence_score,
                threat_assessment=threat_assessment,
                validation_timestamp=datetime.utcnow()
            ))
        
        return validated_anomalies
```

## Infrastructure Components

### 2. ML Model Management Component

```python
class MLModelManager:
    """
    Manages ML model lifecycle, versioning, and deployment
    """
    def __init__(self):
        self.sagemaker_client = boto3.client('sagemaker')
        self.model_registry = SageMakerModelRegistry()
        self.model_cache = {}
        self.deployment_strategy = CanaryDeploymentStrategy()
        
    def get_model(self, model_type):
        """Get model instance with caching and version management"""
        if model_type in self.model_cache:
            cached_model = self.model_cache[model_type]
            if not cached_model.is_expired():
                return cached_model
        
        # Load latest approved model version
        model_version = self.model_registry.get_latest_approved_version(model_type)
        model_endpoint = self.get_or_create_endpoint(model_type, model_version)
        
        model_instance = MLModelProxy(
            model_type=model_type,
            version=model_version,
            endpoint=model_endpoint
        )
        
        self.model_cache[model_type] = model_instance
        return model_instance
    
    def deploy_new_model_version(self, model_type, new_version):
        """Deploy new model version using canary strategy"""
        return self.deployment_strategy.deploy(
            model_type=model_type,
            new_version=new_version,
            traffic_percentage=10  # Start with 10% traffic
        )
```

### 3. Correlation State Manager Component

```python
class CorrelationStateManager:
    """
    Manages correlation state across detection instances
    """
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.environ['REDIS_CLUSTER_ENDPOINT'],
            port=6379,
            decode_responses=True
        )
        self.state_ttl = 1800  # 30 minutes
        
    def get_entity_correlation_state(self, entity_key):
        """Get correlation state for specific entity (IP, subnet, etc.)"""
        state_key = f"correlation:entity:{entity_key}"
        state_data = self.redis_client.get(state_key)
        
        if state_data:
            return CorrelationState.from_json(state_data)
        
        return CorrelationState(entity_key=entity_key)
    
    def update_entity_correlation_state(self, entity_key, state):
        """Update correlation state with TTL"""
        state_key = f"correlation:entity:{entity_key}"
        self.redis_client.setex(
            state_key,
            self.state_ttl,
            state.to_json()
        )
    
    def get_active_correlations(self):
        """Get all active correlation states"""
        pattern = "correlation:entity:*"
        keys = self.redis_client.keys(pattern)
        
        correlations = []
        for key in keys:
            state_data = self.redis_client.get(key)
            if state_data:
                correlations.append(CorrelationState.from_json(state_data))
        
        return correlations
```

### 4. Configuration Management Component

```python
class ConfigurationManager:
    """
    Manages dynamic configuration for detection thresholds and feature flags
    """
    def __init__(self):
        self.ssm_client = boto3.client('ssm')
        self.config_cache = TTLCache(maxsize=100, ttl=60)  # 1-minute cache
        self.parameter_prefix = '/anomaly-detection/'
        
    def get_detection_threshold(self, threat_type):
        """Get detection threshold for specific threat type"""
        param_name = f"{self.parameter_prefix}thresholds/{threat_type}"
        
        if param_name in self.config_cache:
            return self.config_cache[param_name]
        
        try:
            response = self.ssm_client.get_parameter(Name=param_name)
            threshold = float(response['Parameter']['Value'])
            self.config_cache[param_name] = threshold
            return threshold
        except Exception as e:
            logger.warning(f"Failed to get threshold for {threat_type}: {e}")
            return self.get_default_threshold(threat_type)
    
    def is_feature_enabled(self, feature_name):
        """Check if feature flag is enabled"""
        param_name = f"{self.parameter_prefix}features/{feature_name}"
        
        try:
            response = self.ssm_client.get_parameter(Name=param_name)
            return response['Parameter']['Value'].lower() == 'true'
        except Exception:
            return False  # Default to disabled
    
    def update_threshold(self, threat_type, new_threshold):
        """Update detection threshold with validation"""
        param_name = f"{self.parameter_prefix}thresholds/{threat_type}"
        
        # Validate threshold range
        if not (0.0 <= new_threshold <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        self.ssm_client.put_parameter(
            Name=param_name,
            Value=str(new_threshold),
            Type='String',
            Overwrite=True
        )
        
        # Invalidate cache
        if param_name in self.config_cache:
            del self.config_cache[param_name]
```

## Integration Components

### 5. API Gateway Component

```python
class AnomalyDetectionAPIGateway:
    """
    API gateway for anomaly detection service integration
    """
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=100)
        self.auth_manager = AuthenticationManager()
        self.request_validator = RequestValidator()
        
    def handle_anomaly_query(self, request):
        """Handle anomaly query requests"""
        # Authentication and authorization
        auth_context = self.auth_manager.authenticate(request)
        
        # Rate limiting
        if not self.rate_limiter.allow_request(auth_context.client_id):
            raise RateLimitExceededException("Rate limit exceeded")
        
        # Request validation
        validated_request = self.request_validator.validate(request)
        
        # Process query
        query_processor = AnomalyQueryProcessor()
        results = query_processor.process(validated_request)
        
        return APIResponse(
            status_code=200,
            data=results,
            request_id=request.request_id
        )
    
    def handle_anomaly_subscription(self, request):
        """Handle real-time anomaly subscription requests"""
        auth_context = self.auth_manager.authenticate(request)
        
        subscription_manager = AnomalySubscriptionManager()
        subscription = subscription_manager.create_subscription(
            client_id=auth_context.client_id,
            filters=request.filters,
            callback_url=request.callback_url
        )
        
        return APIResponse(
            status_code=201,
            data={'subscription_id': subscription.id}
        )
```

### 6. Event Publishing Component

```python
class AnomalyEventPublisher:
    """
    Publishes anomaly events to external systems
    """
    def __init__(self):
        self.eventbridge_client = boto3.client('events')
        self.event_bus_name = 'anomaly-detection-events'
        self.retry_handler = RetryHandler(max_retries=3)
        
    def publish_anomaly_detected(self, validated_anomaly):
        """Publish anomaly detection event"""
        event = {
            'Source': 'anomaly-detection-service',
            'DetailType': 'Anomaly Detected',
            'Detail': {
                'anomaly_id': validated_anomaly.id,
                'threat_type': validated_anomaly.threat_type,
                'confidence_score': validated_anomaly.confidence_score,
                'affected_entities': validated_anomaly.affected_entities,
                'detection_timestamp': validated_anomaly.detection_timestamp.isoformat(),
                'severity': validated_anomaly.threat_assessment.severity
            },
            'EventBusName': self.event_bus_name
        }
        
        self.retry_handler.execute_with_retry(
            self.eventbridge_client.put_events,
            Entries=[event]
        )
    
    def publish_model_update(self, model_type, old_version, new_version):
        """Publish ML model update event"""
        event = {
            'Source': 'anomaly-detection-service',
            'DetailType': 'ML Model Updated',
            'Detail': {
                'model_type': model_type,
                'old_version': old_version,
                'new_version': new_version,
                'update_timestamp': datetime.utcnow().isoformat()
            },
            'EventBusName': self.event_bus_name
        }
        
        self.eventbridge_client.put_events(Entries=[event])
```

## Monitoring Components

### 7. Performance Monitor Component

```python
class PerformanceMonitor:
    """
    Monitors system performance and SLA compliance
    """
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.metrics_namespace = 'AnomalyDetection/Service'
        self.sla_threshold = 300  # 5 minutes
        
    def track_processing_performance(self, processing_result):
        """Track processing performance metrics"""
        metrics = [
            {
                'MetricName': 'ProcessingLatency',
                'Value': processing_result.total_processing_time,
                'Unit': 'Seconds',
                'Dimensions': [
                    {'Name': 'ProcessingTier', 'Value': 'All'}
                ]
            },
            {
                'MetricName': 'AnomaliesDetected',
                'Value': len(processing_result.anomalies),
                'Unit': 'Count'
            },
            {
                'MetricName': 'SLACompliance',
                'Value': 1 if processing_result.total_processing_time <= self.sla_threshold else 0,
                'Unit': 'None'
            }
        ]
        
        # Track per-tier performance
        for tier, timing in processing_result.tier_timings.items():
            metrics.append({
                'MetricName': 'TierProcessingLatency',
                'Value': timing,
                'Unit': 'Seconds',
                'Dimensions': [
                    {'Name': 'ProcessingTier', 'Value': tier}
                ]
            })
        
        self.publish_metrics(metrics)
    
    def track_ml_model_performance(self, model_type, inference_metrics):
        """Track ML model performance metrics"""
        metrics = [
            {
                'MetricName': 'ModelInferenceLatency',
                'Value': inference_metrics.inference_time,
                'Unit': 'Milliseconds',
                'Dimensions': [
                    {'Name': 'ModelType', 'Value': model_type}
                ]
            },
            {
                'MetricName': 'ModelConfidenceScore',
                'Value': inference_metrics.average_confidence,
                'Unit': 'None',
                'Dimensions': [
                    {'Name': 'ModelType', 'Value': model_type}
                ]
            }
        ]
        
        self.publish_metrics(metrics)
```