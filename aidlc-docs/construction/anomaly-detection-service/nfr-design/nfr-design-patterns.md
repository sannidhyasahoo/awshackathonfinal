# NFR Design Patterns - Anomaly Detection Service

## Resilience Patterns

### Fallback Pattern for ML Model Failures
```python
class ResilientAnomalyDetector:
    def __init__(self):
        self.ml_models = {
            'isolation_forest': IsolationForestModel(),
            'lstm': LSTMModel()
        }
        self.statistical_detectors = {
            'port_scanning': PortScanningDetector(),
            'ddos': DDoSDetector(),
            'c2_beaconing': C2BeaconingDetector()
        }
        self.circuit_breakers = {
            model_name: CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=60,
                expected_exception=ModelInferenceException
            ) for model_name in self.ml_models.keys()
        }
    
    def detect_anomalies(self, flow_logs):
        anomalies = []
        
        # Primary: Statistical detection (always available)
        for detector in self.statistical_detectors.values():
            try:
                result = detector.detect(flow_logs)
                if result:
                    anomalies.extend(result)
            except Exception as e:
                logger.warning(f"Statistical detector failed: {e}")
        
        # Secondary: ML-based detection (with fallback)
        for model_name, model in self.ml_models.items():
            circuit_breaker = self.circuit_breakers[model_name]
            
            try:
                if circuit_breaker.can_execute():
                    ml_anomalies = circuit_breaker.call(model.detect_anomalies, flow_logs)
                    anomalies.extend(ml_anomalies)
                else:
                    logger.info(f"ML model {model_name} circuit breaker open - using statistical fallback")
            except ModelInferenceException as e:
                logger.error(f"ML model {model_name} failed: {e}")
                # Graceful degradation - continue with statistical results
        
        return anomalies
```

### Circuit Breaker Pattern for External Dependencies
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self):
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def call(self, func, *args, **kwargs):
        if not self.can_execute():
            raise CircuitBreakerOpenException("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

### Retry Pattern with Exponential Backoff
```python
class RetryHandler:
    def __init__(self, max_retries=3, base_delay=1, max_delay=60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except TransientException as e:
                if attempt == self.max_retries:
                    raise e
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s")
                time.sleep(delay)
            except PermanentException as e:
                logger.error(f"Permanent failure: {e}")
                raise e
```

## Scalability Patterns

### Event-Driven Auto-Scaling Pattern
```python
class EventDrivenScaler:
    def __init__(self):
        self.scaling_metrics = {
            'queue_depth_threshold': 1000,
            'processing_latency_threshold': 240,  # 4 minutes (80% of 5min SLA)
            'cpu_threshold': 70,
            'memory_threshold': 80
        }
        self.scaling_cooldown = 300  # 5 minutes
        self.last_scale_time = 0
    
    def evaluate_scaling_decision(self, metrics):
        current_time = time.time()
        if current_time - self.last_scale_time < self.scaling_cooldown:
            return None
        
        scaling_decision = {
            'action': None,
            'reason': [],
            'target_instances': None
        }
        
        # Queue depth scaling trigger
        if metrics['queue_depth'] > self.scaling_metrics['queue_depth_threshold']:
            scaling_decision['action'] = 'SCALE_OUT'
            scaling_decision['reason'].append(f"Queue depth {metrics['queue_depth']} exceeds threshold")
        
        # Processing latency scaling trigger
        if metrics['avg_processing_latency'] > self.scaling_metrics['processing_latency_threshold']:
            scaling_decision['action'] = 'SCALE_OUT'
            scaling_decision['reason'].append(f"Processing latency {metrics['avg_processing_latency']}s exceeds threshold")
        
        # Resource utilization scaling
        if (metrics['cpu_utilization'] > self.scaling_metrics['cpu_threshold'] or 
            metrics['memory_utilization'] > self.scaling_metrics['memory_threshold']):
            scaling_decision['action'] = 'SCALE_OUT'
            scaling_decision['reason'].append("Resource utilization exceeds thresholds")
        
        # Scale in conditions
        if (metrics['queue_depth'] < 100 and 
            metrics['avg_processing_latency'] < 60 and
            metrics['cpu_utilization'] < 30):
            scaling_decision['action'] = 'SCALE_IN'
            scaling_decision['reason'].append("Low utilization detected")
        
        if scaling_decision['action']:
            scaling_decision['target_instances'] = self.calculate_target_instances(metrics)
            self.last_scale_time = current_time
        
        return scaling_decision
```

### Load Balancing Pattern for ML Model Inference
```python
class MLModelLoadBalancer:
    def __init__(self):
        self.model_instances = {}
        self.health_checker = ModelHealthChecker()
        self.load_balancing_strategy = 'WEIGHTED_ROUND_ROBIN'
    
    def register_model_instance(self, model_type, instance_id, endpoint, weight=1):
        if model_type not in self.model_instances:
            self.model_instances[model_type] = []
        
        self.model_instances[model_type].append({
            'instance_id': instance_id,
            'endpoint': endpoint,
            'weight': weight,
            'current_load': 0,
            'health_status': 'HEALTHY',
            'last_health_check': time.time()
        })
    
    def select_model_instance(self, model_type):
        if model_type not in self.model_instances:
            raise ModelNotAvailableException(f"No instances available for {model_type}")
        
        healthy_instances = [
            instance for instance in self.model_instances[model_type]
            if instance['health_status'] == 'HEALTHY'
        ]
        
        if not healthy_instances:
            raise ModelNotAvailableException(f"No healthy instances for {model_type}")
        
        # Weighted round-robin selection
        total_weight = sum(instance['weight'] for instance in healthy_instances)
        selection_point = random.uniform(0, total_weight)
        
        current_weight = 0
        for instance in healthy_instances:
            current_weight += instance['weight']
            if selection_point <= current_weight:
                return instance
        
        return healthy_instances[0]  # Fallback
```

## Performance Patterns

### Hybrid Caching Pattern
```python
class HybridCacheManager:
    def __init__(self):
        # Local cache for frequently accessed data
        self.local_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes TTL
        
        # Distributed cache for shared state
        self.distributed_cache = redis.Redis(
            host='elasticache-cluster-endpoint',
            port=6379,
            decode_responses=True
        )
        
        # Cache warming scheduler
        self.cache_warmer = CacheWarmer()
    
    def get_ml_model(self, model_type, version):
        cache_key = f"model:{model_type}:{version}"
        
        # Try local cache first (fastest)
        model = self.local_cache.get(cache_key)
        if model:
            return model
        
        # Try distributed cache (shared across instances)
        model_data = self.distributed_cache.get(cache_key)
        if model_data:
            model = self.deserialize_model(model_data)
            self.local_cache[cache_key] = model  # Warm local cache
            return model
        
        # Load from persistent storage (slowest)
        model = self.load_model_from_storage(model_type, version)
        
        # Cache in both layers
        self.local_cache[cache_key] = model
        self.distributed_cache.setex(
            cache_key, 
            3600,  # 1 hour TTL
            self.serialize_model(model)
        )
        
        return model
    
    def get_correlation_state(self, entity_key):
        # Correlation state always from distributed cache for consistency
        state_key = f"correlation:{entity_key}"
        state_data = self.distributed_cache.get(state_key)
        
        if state_data:
            return json.loads(state_data)
        
        return None
    
    def update_correlation_state(self, entity_key, state):
        state_key = f"correlation:{entity_key}"
        self.distributed_cache.setex(
            state_key,
            1800,  # 30 minutes TTL
            json.dumps(state)
        )
```

### Tiered Processing Pattern
```python
class TieredProcessor:
    def __init__(self):
        self.tier1_queue = Queue(maxsize=10000)  # Fast statistical processing
        self.tier2_queue = Queue(maxsize=1000)   # ML-based analysis
        self.tier3_queue = Queue(maxsize=100)    # Correlation analysis
        
        self.processing_pools = {
            'tier1': ThreadPoolExecutor(max_workers=10),
            'tier2': ThreadPoolExecutor(max_workers=5),
            'tier3': ThreadPoolExecutor(max_workers=2)
        }
    
    def process_flow_logs(self, flow_logs):
        # Tier 1: Fast statistical screening
        tier1_future = self.processing_pools['tier1'].submit(
            self.tier1_statistical_analysis, flow_logs
        )
        
        # Wait for Tier 1 results
        tier1_anomalies = tier1_future.result(timeout=30)
        
        if not tier1_anomalies:
            return []  # No anomalies found, skip further processing
        
        # Tier 2: ML-based analysis (only if Tier 1 found potential threats)
        tier2_future = self.processing_pools['tier2'].submit(
            self.tier2_ml_analysis, flow_logs, tier1_anomalies
        )
        
        # Tier 3: Correlation analysis (parallel with Tier 2)
        tier3_future = self.processing_pools['tier3'].submit(
            self.tier3_correlation_analysis, tier1_anomalies
        )
        
        # Combine results
        tier2_anomalies = tier2_future.result(timeout=120)
        correlated_anomalies = tier3_future.result(timeout=180)
        
        return self.merge_and_validate_anomalies(
            tier1_anomalies, tier2_anomalies, correlated_anomalies
        )
```

## Security Patterns

### Layered Security Pattern
```python
class LayeredSecurityManager:
    def __init__(self):
        self.layers = [
            NetworkSecurityLayer(),
            APIGatewaySecurityLayer(),
            ApplicationSecurityLayer(),
            DataSecurityLayer()
        ]
        self.audit_logger = SecurityAuditLogger()
    
    def authenticate_request(self, request):
        security_context = SecurityContext()
        
        for layer in self.layers:
            try:
                layer_result = layer.authenticate(request, security_context)
                security_context.add_layer_result(layer.name, layer_result)
                
                if not layer_result.is_authenticated:
                    self.audit_logger.log_authentication_failure(
                        request, layer.name, layer_result.failure_reason
                    )
                    raise AuthenticationException(f"Authentication failed at {layer.name}")
                    
            except SecurityException as e:
                self.audit_logger.log_security_exception(request, layer.name, e)
                raise e
        
        self.audit_logger.log_successful_authentication(request, security_context)
        return security_context
    
    def authorize_request(self, request, security_context):
        for layer in self.layers:
            if hasattr(layer, 'authorize'):
                authorization_result = layer.authorize(request, security_context)
                
                if not authorization_result.is_authorized:
                    self.audit_logger.log_authorization_failure(
                        request, layer.name, authorization_result.failure_reason
                    )
                    raise AuthorizationException(f"Authorization failed at {layer.name}")
        
        return True
```

### Encryption Pattern for Data Protection
```python
class DataEncryptionManager:
    def __init__(self):
        self.kms_client = boto3.client('kms')
        self.encryption_key_id = os.environ['ANOMALY_DETECTION_KMS_KEY_ID']
        self.field_encryption_keys = {}
    
    def encrypt_flow_log_data(self, flow_log):
        encrypted_log = flow_log.copy()
        
        # Encrypt sensitive fields
        sensitive_fields = ['source_ip', 'destination_ip']
        for field in sensitive_fields:
            if field in encrypted_log:
                encrypted_log[field] = self.encrypt_field(encrypted_log[field], field)
        
        # Add encryption metadata
        encrypted_log['encryption_metadata'] = {
            'encrypted_fields': sensitive_fields,
            'encryption_timestamp': datetime.utcnow().isoformat(),
            'key_id': self.encryption_key_id
        }
        
        return encrypted_log
    
    def encrypt_field(self, value, field_name):
        # Use field-specific encryption key
        if field_name not in self.field_encryption_keys:
            self.field_encryption_keys[field_name] = self.generate_data_key(field_name)
        
        field_key = self.field_encryption_keys[field_name]
        
        # Encrypt using AES-256-GCM
        cipher = AES.new(field_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(value.encode('utf-8'))
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'nonce': base64.b64encode(cipher.nonce).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8')
        }
```

## Monitoring and Observability Patterns

### Comprehensive Monitoring Pattern
```python
class AnomalyDetectionMonitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.metrics_buffer = []
        self.alert_manager = AlertManager()
    
    def track_detection_performance(self, detection_result):
        metrics = [
            {
                'MetricName': 'AnomaliesDetected',
                'Value': len(detection_result.anomalies),
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'ThreatType', 'Value': anomaly.threat_type}
                    for anomaly in detection_result.anomalies
                ]
            },
            {
                'MetricName': 'ProcessingLatency',
                'Value': detection_result.processing_time,
                'Unit': 'Seconds'
            },
            {
                'MetricName': 'FalsePositiveRate',
                'Value': detection_result.estimated_false_positive_rate,
                'Unit': 'Percent'
            }
        ]
        
        self.publish_metrics(metrics)
        
        # Check SLA compliance
        if detection_result.processing_time > 300:  # 5 minutes
            self.alert_manager.trigger_alert(
                'SLA_BREACH',
                f"Processing time {detection_result.processing_time}s exceeds 5-minute SLA"
            )
    
    def track_ml_model_performance(self, model_type, inference_time, confidence_score):
        self.publish_metrics([
            {
                'MetricName': 'MLModelInferenceTime',
                'Value': inference_time,
                'Unit': 'Milliseconds',
                'Dimensions': [{'Name': 'ModelType', 'Value': model_type}]
            },
            {
                'MetricName': 'MLModelConfidence',
                'Value': confidence_score,
                'Unit': 'None',
                'Dimensions': [{'Name': 'ModelType', 'Value': model_type}]
            }
        ])
```