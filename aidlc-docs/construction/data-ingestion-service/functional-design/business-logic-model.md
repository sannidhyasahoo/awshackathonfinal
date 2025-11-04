# Business Logic Model - Data Ingestion Service

## Processing Workflow Overview

Based on tiered processing with multiple filtering stages and graceful degradation patterns.

## Core Processing Algorithms

### Tiered Processing Pipeline

```
VPC Flow Logs (100M/day)
    ↓
Tier 1: Schema & Basic Validation (99% reduction)
    ↓ (1M logs/day)
Tier 2: Static Rule Filtering (Health checks, AWS endpoints)
    ↓ (800K logs/day)
Tier 3: Dynamic Pattern Recognition (ML-based benign detection)
    ↓ (500K logs/day)
Tier 4: Best Effort Enrichment (Geo-IP, EC2, DNS)
    ↓ (500K enriched logs/day)
Storage: Partitioned S3 + OpenSearch Indexing
```

### Tier 1: Schema & Basic Validation Algorithm

```python
def validate_flow_log_schema(log_record):
    """
    Multi-level validation with different actions based on failure type
    """
    validation_result = ValidationResult()
    
    # Schema validation (CRITICAL - reject if fails)
    if not validate_vpc_flow_log_schema(log_record):
        validation_result.action = "REJECT"
        validation_result.reason = "SCHEMA_INVALID"
        return validation_result
    
    # Content validation (WARNING - flag but continue)
    content_issues = validate_content_correctness(log_record)
    if content_issues:
        validation_result.warnings.extend(content_issues)
        validation_result.quality_score -= len(content_issues) * 0.1
    
    # Statistical validation (INFO - monitor patterns)
    statistical_anomalies = detect_statistical_anomalies(log_record)
    if statistical_anomalies:
        validation_result.flags.extend(statistical_anomalies)
    
    validation_result.action = "ACCEPT"
    return validation_result
```

### Tier 2: Static Rule Filtering Algorithm

```python
def apply_static_filtering_rules(log_record):
    """
    Hybrid approach: Static base rules with dynamic pattern recognition
    """
    # Static rule evaluation
    for rule in get_static_filtering_rules():
        if rule.matches(log_record):
            return FilterResult(
                action="FILTER_OUT",
                rule_id=rule.id,
                confidence=1.0,
                reason=rule.description
            )
    
    # Dynamic pattern recognition
    pattern_score = evaluate_dynamic_patterns(log_record)
    if pattern_score > BENIGN_THRESHOLD:
        return FilterResult(
            action="FILTER_OUT",
            rule_id="DYNAMIC_PATTERN",
            confidence=pattern_score,
            reason="Benign pattern detected"
        )
    
    return FilterResult(action="CONTINUE", confidence=1.0)
```

### Tier 3: Dynamic Pattern Recognition Algorithm

```python
def evaluate_dynamic_patterns(log_record):
    """
    Machine learning-based benign pattern detection
    """
    # Extract features for ML model
    features = extract_flow_log_features(log_record)
    
    # Get benign probability from trained model
    benign_probability = benign_classifier_model.predict_proba(features)[0][1]
    
    # Update pattern cache for future use
    update_pattern_cache(log_record, benign_probability)
    
    return benign_probability
```

### Tier 4: Best Effort Enrichment Algorithm

```python
def enrich_flow_log(log_record):
    """
    Best effort enrichment with graceful degradation
    """
    enriched_log = EnrichedFlowLog(log_record)
    enrichment_status = EnrichmentStatus()
    
    # Geo-IP enrichment with fallback
    try:
        geo_info = get_geo_ip_info(log_record.source_ip)
        enriched_log.source_geo = geo_info
        enrichment_status.geo_ip = "SUCCESS"
    except Exception as e:
        # Use cached data if available
        cached_geo = get_cached_geo_info(log_record.source_ip)
        if cached_geo:
            enriched_log.source_geo = cached_geo
            enrichment_status.geo_ip = "CACHED"
        else:
            enrichment_status.geo_ip = "FAILED"
            enrichment_status.failures.append(f"GeoIP: {str(e)}")
    
    # EC2 metadata enrichment with fallback
    try:
        ec2_metadata = get_ec2_metadata(log_record.source_ip)
        enriched_log.ec2_metadata = ec2_metadata
        enrichment_status.ec2_metadata = "SUCCESS"
    except Exception as e:
        cached_metadata = get_cached_ec2_metadata(log_record.source_ip)
        if cached_metadata:
            enriched_log.ec2_metadata = cached_metadata
            enrichment_status.ec2_metadata = "CACHED"
        else:
            enrichment_status.ec2_metadata = "FAILED"
            enrichment_status.failures.append(f"EC2: {str(e)}")
    
    # DNS enrichment with fallback
    try:
        dns_info = perform_dns_lookup(log_record.destination_ip)
        enriched_log.dns_info = dns_info
        enrichment_status.dns_lookup = "SUCCESS"
    except Exception as e:
        cached_dns = get_cached_dns_info(log_record.destination_ip)
        if cached_dns:
            enriched_log.dns_info = cached_dns
            enrichment_status.dns_lookup = "CACHED"
        else:
            enrichment_status.dns_lookup = "FAILED"
            enrichment_status.failures.append(f"DNS: {str(e)}")
    
    # Calculate overall enrichment quality
    enrichment_status.overall_quality = calculate_enrichment_quality(enrichment_status)
    enriched_log.enrichment_status = enrichment_status
    
    return enriched_log
```

## Storage Optimization Algorithms

### Partitioned Storage Strategy

```python
def determine_storage_partition(enriched_log):
    """
    Partition by time/source for query optimization
    """
    # Time-based partitioning (primary)
    partition_date = enriched_log.timestamp.strftime("%Y/%m/%d")
    partition_hour = enriched_log.timestamp.strftime("%H")
    
    # Source-based sub-partitioning (secondary)
    source_type = classify_source_type(enriched_log.source_ip)
    
    # Generate partition path
    partition_path = f"year={partition_date.split('/')[0]}/month={partition_date.split('/')[1]}/day={partition_date.split('/')[2]}/hour={partition_hour}/source_type={source_type}"
    
    return partition_path

def optimize_batch_storage(log_batch):
    """
    Accumulate logs and store in optimized batches
    """
    # Group by partition for efficient storage
    partitioned_batches = group_by_partition(log_batch)
    
    storage_results = []
    for partition, logs in partitioned_batches.items():
        # Convert to Parquet format
        parquet_data = convert_to_parquet(logs)
        
        # Store in S3 with partition path
        s3_result = store_to_s3(parquet_data, partition)
        
        # Index in OpenSearch for fast queries
        opensearch_result = index_to_opensearch(logs, partition)
        
        storage_results.append(StorageResult(
            partition=partition,
            s3_result=s3_result,
            opensearch_result=opensearch_result,
            log_count=len(logs)
        ))
    
    return storage_results
```

## Data Quality Monitoring Algorithms

### Multi-Level Validation Implementation

```python
def perform_multi_level_validation(log_record):
    """
    Schema + content + statistical validation with different actions
    """
    validation_results = []
    
    # Level 1: Schema Validation (CRITICAL)
    schema_result = validate_schema(log_record)
    if not schema_result.valid:
        return ValidationDecision(
            action="REJECT",
            level="CRITICAL",
            reason="Schema validation failed",
            details=schema_result.errors
        )
    validation_results.append(schema_result)
    
    # Level 2: Content Validation (WARNING)
    content_result = validate_content(log_record)
    if not content_result.valid:
        validation_results.append(content_result)
        # Continue processing but flag issues
    
    # Level 3: Statistical Validation (INFO)
    statistical_result = validate_statistical_patterns(log_record)
    if statistical_result.anomalies_detected:
        validation_results.append(statistical_result)
        # Continue processing but monitor patterns
    
    # Determine overall action based on validation levels
    overall_quality = calculate_overall_quality(validation_results)
    
    if overall_quality >= QUALITY_THRESHOLD_HIGH:
        action = "ACCEPT_HIGH_QUALITY"
    elif overall_quality >= QUALITY_THRESHOLD_MEDIUM:
        action = "ACCEPT_MEDIUM_QUALITY"
    else:
        action = "ACCEPT_LOW_QUALITY"
    
    return ValidationDecision(
        action=action,
        quality_score=overall_quality,
        validation_results=validation_results
    )
```

## Error Handling and Recovery Algorithms

### Circuit Breaker Pattern for External Services

```python
class EnrichmentCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call_external_service(self, service_func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenException("Service unavailable")
        
        try:
            result = service_func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e
```

## Performance Optimization Algorithms

### Adaptive Batch Sizing

```python
def calculate_optimal_batch_size(current_throughput, target_latency):
    """
    Dynamically adjust batch size based on performance metrics
    """
    if current_throughput < TARGET_THROUGHPUT * 0.8:
        # Increase batch size to improve throughput
        return min(current_batch_size * 1.2, MAX_BATCH_SIZE)
    elif average_latency > target_latency:
        # Decrease batch size to reduce latency
        return max(current_batch_size * 0.8, MIN_BATCH_SIZE)
    else:
        # Maintain current batch size
        return current_batch_size

def adaptive_processing_control(processing_metrics):
    """
    Adjust processing parameters based on system performance
    """
    # Monitor key metrics
    throughput = processing_metrics.logs_per_second
    latency = processing_metrics.average_processing_time
    error_rate = processing_metrics.error_rate
    
    # Adjust batch size
    optimal_batch_size = calculate_optimal_batch_size(throughput, TARGET_LATENCY)
    
    # Adjust concurrency
    if error_rate > ERROR_RATE_THRESHOLD:
        # Reduce concurrency to improve stability
        concurrency = max(current_concurrency * 0.8, MIN_CONCURRENCY)
    elif throughput < TARGET_THROUGHPUT and latency < TARGET_LATENCY:
        # Increase concurrency to improve throughput
        concurrency = min(current_concurrency * 1.1, MAX_CONCURRENCY)
    else:
        concurrency = current_concurrency
    
    return ProcessingConfiguration(
        batch_size=optimal_batch_size,
        concurrency=concurrency,
        timeout=calculate_timeout(latency)
    )
```

## Cost Optimization Algorithms

### Dynamic Filtering Threshold Adjustment

```python
def adjust_filtering_thresholds(cost_metrics, quality_metrics):
    """
    Dynamically adjust filtering thresholds to maintain cost targets
    """
    current_cost_per_day = cost_metrics.daily_processing_cost
    target_cost_per_day = 0.75  # $0.75/day target
    
    if current_cost_per_day > target_cost_per_day * 1.1:
        # Increase filtering aggressiveness
        new_threshold = min(BENIGN_THRESHOLD * 1.05, MAX_THRESHOLD)
        
        # Ensure quality doesn't degrade too much
        if quality_metrics.false_positive_rate < 0.03:  # Well below 5% target
            return new_threshold
    elif current_cost_per_day < target_cost_per_day * 0.9:
        # Decrease filtering to improve quality
        new_threshold = max(BENIGN_THRESHOLD * 0.95, MIN_THRESHOLD)
        
        return new_threshold
    
    return BENIGN_THRESHOLD  # No change needed
```