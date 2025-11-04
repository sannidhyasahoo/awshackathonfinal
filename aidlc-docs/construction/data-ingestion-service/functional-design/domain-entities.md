# Domain Entities - Data Ingestion Service

## Core Domain Entities

### FlowLogRecord
**Purpose**: Represents a raw VPC Flow Log record as received from Kinesis

```python
@dataclass
class FlowLogRecord:
    # Standard VPC Flow Log fields
    version: int
    account_id: str
    interface_id: str
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: int
    packets: int
    bytes: int
    window_start: datetime
    window_end: datetime
    action: str  # ACCEPT or REJECT
    flow_log_status: str  # OK, NODATA, SKIPDATA
    
    # Processing metadata
    ingestion_timestamp: datetime
    record_id: str
    source_stream: str
    
    def is_valid_schema(self) -> bool:
        """Validate against VPC Flow Log schema"""
        pass
    
    def get_flow_direction(self) -> str:
        """Determine if flow is inbound, outbound, or internal"""
        pass
```

### EnrichedFlowLog
**Purpose**: Represents a flow log after enrichment and validation processing

```python
@dataclass
class EnrichedFlowLog:
    # Original flow log data
    original_record: FlowLogRecord
    
    # Enrichment data
    source_geo: Optional[GeoIPInfo]
    destination_geo: Optional[GeoIPInfo]
    ec2_metadata: Optional[EC2Metadata]
    dns_info: Optional[DNSInfo]
    
    # Processing metadata
    enrichment_status: EnrichmentStatus
    validation_result: ValidationResult
    processing_timestamp: datetime
    partition_path: str
    quality_score: float
    
    # Derived fields
    flow_classification: str  # INTERNAL, INBOUND, OUTBOUND
    risk_indicators: List[str]
    
    def to_parquet_record(self) -> dict:
        """Convert to Parquet-compatible format"""
        pass
    
    def to_opensearch_document(self) -> dict:
        """Convert to OpenSearch document format"""
        pass
```

## Enrichment Entities

### GeoIPInfo
**Purpose**: Geographic information for IP addresses

```python
@dataclass
class GeoIPInfo:
    ip_address: str
    country_code: str
    country_name: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    isp: str
    organization: str
    
    # Threat intelligence flags
    is_tor_exit_node: bool
    is_known_malicious: bool
    reputation_score: float
    
    # Caching metadata
    cache_timestamp: datetime
    cache_ttl: int
    data_source: str  # "live", "cached", "default"
    
    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        return datetime.now() - self.cache_timestamp < timedelta(seconds=self.cache_ttl)
```

### EC2Metadata
**Purpose**: AWS EC2 instance metadata for source/destination IPs

```python
@dataclass
class EC2Metadata:
    ip_address: str
    instance_id: Optional[str]
    instance_type: Optional[str]
    vpc_id: Optional[str]
    subnet_id: Optional[str]
    availability_zone: Optional[str]
    
    # Security context
    security_groups: List[SecurityGroupInfo]
    iam_role: Optional[str]
    
    # Tagging information
    tags: Dict[str, str]
    
    # Metadata status
    lookup_timestamp: datetime
    data_source: str  # "live", "cached", "not_found"
    
    def get_environment(self) -> str:
        """Extract environment from tags (prod, staging, dev)"""
        return self.tags.get("Environment", "unknown")
    
    def get_application(self) -> str:
        """Extract application name from tags"""
        return self.tags.get("Application", "unknown")
```

### DNSInfo
**Purpose**: DNS resolution information for IP addresses

```python
@dataclass
class DNSInfo:
    ip_address: str
    hostname: Optional[str]
    domain: Optional[str]
    
    # DNS metadata
    record_type: str  # A, AAAA, PTR
    ttl: int
    lookup_timestamp: datetime
    
    # Domain classification
    is_aws_service: bool
    is_cdn: bool
    is_known_good: bool
    is_suspicious: bool
    
    # Threat intelligence
    domain_reputation: float
    threat_categories: List[str]
    
    def get_domain_classification(self) -> str:
        """Classify domain type (aws, cdn, corporate, suspicious, etc.)"""
        pass
```

## Filtering and Validation Entities

### FilteringRule
**Purpose**: Represents filtering rules for cost optimization

```python
@dataclass
class FilteringRule:
    rule_id: str
    rule_name: str
    rule_type: str  # "static", "dynamic", "ml_based"
    
    # Rule definition
    conditions: List[FilterCondition]
    action: str  # "filter_out", "flag", "continue"
    priority: int
    
    # Rule metadata
    created_date: datetime
    last_modified: datetime
    is_active: bool
    
    # Performance metrics
    match_count: int
    false_positive_count: int
    effectiveness_score: float
    
    def matches(self, flow_log: FlowLogRecord) -> bool:
        """Check if rule matches the flow log"""
        pass
    
    def update_metrics(self, matched: bool, false_positive: bool):
        """Update rule performance metrics"""
        pass
```

### FilterCondition
**Purpose**: Individual condition within a filtering rule

```python
@dataclass
class FilterCondition:
    field_name: str  # "source_ip", "destination_port", etc.
    operator: str    # "equals", "in", "matches", "range"
    value: Union[str, int, List, dict]
    
    def evaluate(self, flow_log: FlowLogRecord) -> bool:
        """Evaluate condition against flow log"""
        pass
```

### ValidationResult
**Purpose**: Results of multi-level validation process

```python
@dataclass
class ValidationResult:
    # Validation levels
    schema_validation: ValidationLevel
    content_validation: ValidationLevel
    statistical_validation: ValidationLevel
    
    # Overall result
    overall_action: str  # "ACCEPT", "REJECT", "FLAG"
    quality_score: float
    
    # Issues and warnings
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    flags: List[ValidationFlag]
    
    def is_acceptable(self) -> bool:
        """Determine if record should be accepted"""
        return self.overall_action in ["ACCEPT"]
```

### ValidationLevel
**Purpose**: Results for each validation level

```python
@dataclass
class ValidationLevel:
    level_name: str  # "schema", "content", "statistical"
    is_valid: bool
    confidence: float
    issues: List[str]
    
    def add_issue(self, issue: str, severity: str):
        """Add validation issue"""
        pass
```

## Storage Entities

### S3Object
**Purpose**: Represents stored object in S3

```python
@dataclass
class S3Object:
    bucket_name: str
    object_key: str
    partition_path: str
    
    # Object metadata
    size_bytes: int
    record_count: int
    compression_type: str
    format_type: str  # "parquet"
    
    # Timestamps
    created_timestamp: datetime
    last_modified: datetime
    
    # Partitioning information
    year: int
    month: int
    day: int
    hour: int
    source_type: str
    
    def get_s3_uri(self) -> str:
        """Get full S3 URI"""
        return f"s3://{self.bucket_name}/{self.object_key}"
```

### OpenSearchDocument
**Purpose**: Represents indexed document in OpenSearch

```python
@dataclass
class OpenSearchDocument:
    document_id: str
    index_name: str
    
    # Document content (flattened for search)
    timestamp: datetime
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    action: str
    
    # Enriched fields for search
    source_country: str
    destination_country: str
    source_organization: str
    destination_organization: str
    
    # Search metadata
    indexed_timestamp: datetime
    partition_date: str
    
    def to_elasticsearch_doc(self) -> dict:
        """Convert to Elasticsearch document format"""
        pass
```

## Processing Status Entities

### EnrichmentStatus
**Purpose**: Tracks enrichment process status and quality

```python
@dataclass
class EnrichmentStatus:
    # Individual enrichment results
    geo_ip: str          # "SUCCESS", "CACHED", "FAILED"
    ec2_metadata: str    # "SUCCESS", "CACHED", "FAILED", "NOT_FOUND"
    dns_lookup: str      # "SUCCESS", "CACHED", "FAILED"
    
    # Overall status
    overall_quality: float  # 0.0 to 1.0
    enrichment_completeness: float  # Percentage of successful enrichments
    
    # Error tracking
    failures: List[str]
    warnings: List[str]
    
    # Performance metrics
    processing_time_ms: int
    cache_hit_rate: float
    
    def calculate_quality_score(self) -> float:
        """Calculate overall enrichment quality"""
        pass
```

### ProcessingMetrics
**Purpose**: System performance and cost metrics

```python
@dataclass
class ProcessingMetrics:
    # Throughput metrics
    logs_per_second: float
    logs_processed_total: int
    logs_filtered_total: int
    
    # Quality metrics
    average_processing_time: float
    error_rate: float
    false_positive_rate: float
    
    # Cost metrics
    daily_processing_cost: float
    cost_per_million_logs: float
    
    # Resource utilization
    cpu_utilization: float
    memory_utilization: float
    
    # Timestamp
    measurement_timestamp: datetime
    measurement_period: timedelta
```

## Lifecycle and Retention Entities

### RetentionPolicy
**Purpose**: Data lifecycle and retention management

```python
@dataclass
class RetentionPolicy:
    policy_name: str
    
    # Retention periods
    hot_storage_days: int      # OpenSearch + S3 Standard
    warm_storage_days: int     # S3 Infrequent Access
    cold_storage_days: int     # S3 Glacier
    archive_storage_days: int  # S3 Deep Archive
    deletion_days: int         # Permanent deletion
    
    # Policy conditions
    applies_to_source_types: List[str]
    applies_to_quality_scores: Optional[float]  # Only retain high-quality logs longer
    
    # Compliance requirements
    compliance_hold: bool
    legal_hold_expiry: Optional[datetime]
    
    def get_storage_class(self, age_days: int) -> str:
        """Determine appropriate storage class based on age"""
        pass
```

## Entity Relationships

### Primary Relationships
- **FlowLogRecord** → **EnrichedFlowLog** (1:1 transformation)
- **EnrichedFlowLog** → **S3Object** (many:1 batching)
- **EnrichedFlowLog** → **OpenSearchDocument** (1:1 indexing)
- **FilteringRule** → **FilterCondition** (1:many composition)

### Enrichment Relationships
- **EnrichedFlowLog** → **GeoIPInfo** (1:2 for source/destination)
- **EnrichedFlowLog** → **EC2Metadata** (1:1 optional)
- **EnrichedFlowLog** → **DNSInfo** (1:2 for source/destination)

### Processing Relationships
- **EnrichedFlowLog** → **ValidationResult** (1:1)
- **EnrichedFlowLog** → **EnrichmentStatus** (1:1)
- **ProcessingMetrics** → **RetentionPolicy** (many:many application)