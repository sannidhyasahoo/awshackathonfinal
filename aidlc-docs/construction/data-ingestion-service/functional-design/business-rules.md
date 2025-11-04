# Business Rules - Data Ingestion Service

## Validation Rules

### Schema Validation Rules (CRITICAL - Reject if Failed)

#### VR-001: VPC Flow Log Schema Compliance
- **Rule**: All flow logs must conform to AWS VPC Flow Log format version 2, 3, or 4
- **Validation**: 
  - Required fields: version, account-id, interface-id, srcaddr, dstaddr, srcport, dstport, protocol, packets, bytes, windowstart, windowend, action, flowlogstatus
  - Field data types must match specification
  - Timestamp fields must be valid Unix timestamps
- **Action on Failure**: REJECT record, log error, increment schema_validation_failures metric
- **Business Justification**: Invalid schema indicates corrupted data that cannot be reliably processed

#### VR-002: Critical Field Presence
- **Rule**: Source IP, destination IP, and timestamp fields must be present and non-null
- **Validation**: srcaddr != null AND dstaddr != null AND windowstart != null
- **Action on Failure**: REJECT record
- **Business Justification**: These fields are essential for threat detection and cannot be inferred

### Content Validation Rules (WARNING - Flag but Continue)

#### VR-003: IP Address Format Validation
- **Rule**: IP addresses must be valid IPv4 or IPv6 format
- **Validation**: 
  - IPv4: 0.0.0.0 to 255.255.255.255 format
  - IPv6: Valid hexadecimal notation
  - No reserved or invalid ranges (0.0.0.0, 255.255.255.255)
- **Action on Failure**: FLAG as content_validation_warning, reduce quality_score by 0.1
- **Business Justification**: Invalid IPs may indicate data corruption but record may still have analytical value

#### VR-004: Port Range Validation
- **Rule**: Port numbers must be in valid range (0-65535)
- **Validation**: 0 <= port <= 65535
- **Action on Failure**: FLAG as invalid_port, continue processing
- **Business Justification**: Invalid ports may be legitimate in some network configurations

#### VR-005: Protocol Validation
- **Rule**: Protocol numbers must be valid IANA protocol numbers
- **Validation**: Protocol number exists in IANA registry (1=ICMP, 6=TCP, 17=UDP, etc.)
- **Action on Failure**: FLAG as unknown_protocol, continue processing
- **Business Justification**: Unknown protocols may be legitimate custom protocols

### Statistical Validation Rules (INFO - Monitor Patterns)

#### VR-006: Traffic Volume Anomaly Detection
- **Rule**: Detect unusual traffic patterns that may indicate data quality issues
- **Validation**: 
  - Bytes/packets ratio within expected range (40-1500 bytes/packet for TCP)
  - Packet count > 0 when bytes > 0
  - Flow duration reasonable (windowend > windowstart)
- **Action on Failure**: FLAG as statistical_anomaly, monitor pattern
- **Business Justification**: Statistical anomalies may indicate legitimate unusual traffic or data quality issues

#### VR-007: Temporal Consistency
- **Rule**: Flow timestamps should be recent and in logical order
- **Validation**: 
  - windowstart <= windowend
  - Flow timestamp within last 24 hours (configurable)
  - No future timestamps
- **Action on Failure**: FLAG as temporal_anomaly
- **Business Justification**: Temporal inconsistencies may indicate clock skew or replay attacks

## Filtering Rules

### Static Filtering Rules (99% Reduction Target)

#### FR-001: AWS Service Endpoint Filtering
- **Rule**: Filter out traffic to/from known AWS service endpoints
- **Conditions**:
  - Destination IP in AWS service IP ranges (S3, EC2, Lambda endpoints)
  - Source IP in AWS service IP ranges for internal AWS traffic
  - DNS names matching *.amazonaws.com, *.aws.amazon.com
- **Action**: FILTER_OUT
- **Business Justification**: AWS service traffic is generally benign and creates noise in threat detection

#### FR-002: Health Check Traffic Filtering
- **Rule**: Filter out application health check traffic
- **Conditions**:
  - Source/destination ports in health check port list (8080, 9000, /health endpoints)
  - Regular periodic patterns with small payload sizes
  - Traffic between load balancers and application instances
- **Action**: FILTER_OUT
- **Business Justification**: Health checks are operational traffic with no security relevance

#### FR-003: Internal Management Traffic Filtering
- **Rule**: Filter out internal management and monitoring traffic
- **Conditions**:
  - Traffic to/from monitoring systems (Prometheus, Grafana ports)
  - SNMP traffic (port 161/162)
  - NTP traffic (port 123)
  - Internal DNS traffic (port 53 between internal servers)
- **Action**: FILTER_OUT
- **Business Justification**: Management traffic is expected and creates false positives in threat detection

### Dynamic Filtering Rules (Pattern Recognition)

#### FR-004: Benign Pattern Recognition
- **Rule**: Use ML model to identify benign traffic patterns
- **Conditions**:
  - ML model confidence > 0.85 for benign classification
  - Traffic pattern matches known good application behavior
  - Source/destination in whitelist of known good entities
- **Action**: FILTER_OUT if confidence > threshold
- **Business Justification**: ML can identify complex benign patterns that static rules cannot capture

#### FR-005: Adaptive Threshold Adjustment
- **Rule**: Dynamically adjust filtering thresholds based on cost and quality metrics
- **Conditions**:
  - If daily cost > $0.82 (110% of target), increase filtering aggressiveness
  - If false positive rate < 3%, allow more aggressive filtering
  - If false positive rate > 7%, reduce filtering aggressiveness
- **Action**: Adjust BENIGN_THRESHOLD parameter
- **Business Justification**: Maintain cost targets while preserving detection quality

## Enrichment Rules

### Enrichment Validation Rules (Best Effort with Fallback)

#### ER-001: Geo-IP Enrichment Rules
- **Rule**: Enrich with geographic information using best available source
- **Priority Order**:
  1. Live GeoIP service (MaxMind, IPInfo)
  2. Cached GeoIP data (if < 24 hours old)
  3. Default values for private IP ranges
- **Validation**: 
  - Country code must be valid ISO 3166-1 alpha-2
  - Coordinates must be valid latitude/longitude
- **Fallback**: Use "Unknown" values if all sources fail
- **Business Justification**: Geographic context helps identify suspicious cross-border traffic

#### ER-002: EC2 Metadata Enrichment Rules
- **Rule**: Enrich with AWS EC2 instance metadata when available
- **Conditions**:
  - IP address belongs to EC2 instance in same account
  - Instance metadata is accessible via AWS API
- **Enrichment Data**:
  - Instance ID, type, VPC, subnet, security groups
  - IAM role, tags (Environment, Application, Owner)
- **Fallback**: Mark as "external" if not EC2 instance
- **Business Justification**: Instance context helps classify internal vs external traffic

#### ER-003: DNS Resolution Rules
- **Rule**: Perform reverse DNS lookup for IP addresses
- **Conditions**:
  - Attempt PTR record lookup for all IP addresses
  - Cache results for 1 hour to reduce API calls
- **Validation**:
  - Hostname must resolve back to same IP (forward confirmation)
  - Domain must not be in suspicious domain list
- **Fallback**: Use IP address as identifier if DNS fails
- **Business Justification**: Domain names provide context for threat classification

### Enrichment Quality Rules

#### ER-004: Enrichment Completeness Scoring
- **Rule**: Calculate enrichment quality score based on successful enrichments
- **Scoring**:
  - Geo-IP success: +0.4 points
  - EC2 metadata success: +0.3 points
  - DNS resolution success: +0.3 points
  - Maximum score: 1.0
- **Quality Thresholds**:
  - High quality: >= 0.8
  - Medium quality: >= 0.5
  - Low quality: < 0.5
- **Business Justification**: Quality scoring helps prioritize high-confidence data for analysis

#### ER-005: Cache Management Rules
- **Rule**: Manage enrichment data caching for performance and cost optimization
- **Cache TTL**:
  - Geo-IP data: 24 hours
  - EC2 metadata: 1 hour (instances can change)
  - DNS data: 1 hour (DNS can change frequently)
- **Cache Invalidation**:
  - Force refresh if data is flagged as stale
  - Invalidate on known infrastructure changes
- **Business Justification**: Caching reduces external API costs while maintaining data freshness

## Storage Rules

### Partitioning Rules

#### SR-001: Time-Based Partitioning
- **Rule**: Partition data by time for efficient querying and lifecycle management
- **Partition Structure**: year=YYYY/month=MM/day=DD/hour=HH/source_type=TYPE
- **Partition Keys**:
  - Year, month, day, hour from flow timestamp
  - Source type: internal, external, aws_service, unknown
- **Business Justification**: Time-based partitioning enables efficient historical queries and automated lifecycle management

#### SR-002: Source Type Classification
- **Rule**: Classify and partition flows by source type for optimized storage
- **Classification Logic**:
  - internal: Both IPs in private RFC 1918 ranges
  - external: At least one public IP
  - aws_service: Traffic to/from AWS service endpoints
  - unknown: Cannot determine source type
- **Business Justification**: Source type partitioning enables targeted analysis and different retention policies

### Data Quality Rules

#### SR-003: Storage Quality Thresholds
- **Rule**: Apply different storage strategies based on data quality
- **Quality-Based Actions**:
  - High quality (>= 0.8): Store in both S3 and OpenSearch with full indexing
  - Medium quality (>= 0.5): Store in S3, limited OpenSearch indexing
  - Low quality (< 0.5): Store in S3 only, flag for review
- **Business Justification**: Optimize storage costs by indexing only high-quality data

#### SR-004: Compression and Format Rules
- **Rule**: Use optimal compression and format for cost and performance
- **Format Requirements**:
  - S3 storage: Parquet format with Snappy compression
  - Batch size: 1000-10000 records per file
  - File size target: 100-500 MB per file
- **Business Justification**: Parquet format provides optimal compression and query performance for analytical workloads

## Retention and Lifecycle Rules

### Data Retention Rules

#### RR-001: Tiered Storage Lifecycle
- **Rule**: Implement tiered storage based on data age and access patterns
- **Lifecycle Transitions**:
  - 0-30 days: S3 Standard + OpenSearch (hot storage)
  - 31-90 days: S3 Infrequent Access (warm storage)
  - 91-365 days: S3 Glacier (cold storage)
  - 366-2555 days: S3 Deep Archive (archive storage)
  - >2555 days: Delete (7-year retention for compliance)
- **Business Justification**: Tiered storage reduces costs while maintaining compliance requirements

#### RR-002: Quality-Based Retention
- **Rule**: Retain high-quality data longer than low-quality data
- **Retention Periods**:
  - High quality data: Full 7-year retention
  - Medium quality data: 3-year retention
  - Low quality data: 1-year retention
- **Exception**: Security incidents extend retention to full 7 years regardless of quality
- **Business Justification**: Focus long-term storage costs on highest-value data

### Compliance Rules

#### RR-003: Regulatory Compliance
- **Rule**: Ensure data retention meets regulatory requirements
- **Compliance Requirements**:
  - SOX: 7-year retention for financial systems
  - GDPR: Right to deletion for EU personal data
  - HIPAA: 6-year retention for healthcare systems
- **Implementation**: Tag data with compliance requirements, apply appropriate retention
- **Business Justification**: Avoid regulatory violations while optimizing storage costs

## Error Handling Rules

### Circuit Breaker Rules

#### EH-001: External Service Circuit Breaker
- **Rule**: Implement circuit breaker pattern for external enrichment services
- **Thresholds**:
  - Failure threshold: 5 consecutive failures
  - Recovery timeout: 60 seconds
  - Half-open test: Single request to test recovery
- **Actions**:
  - CLOSED: Normal operation
  - OPEN: Use cached data only
  - HALF_OPEN: Test single request
- **Business Justification**: Prevent cascade failures and maintain system stability

#### EH-002: Graceful Degradation Rules
- **Rule**: Maintain core functionality when non-critical services fail
- **Degradation Levels**:
  - Level 1: Disable geo-IP enrichment, continue with other enrichments
  - Level 2: Disable all enrichment, store raw logs only
  - Level 3: Basic validation only, store all logs
- **Recovery**: Automatically restore functionality when services recover
- **Business Justification**: Ensure continuous data ingestion even during partial system failures

### Data Quality Recovery Rules

#### EH-003: Failed Record Recovery
- **Rule**: Attempt recovery of failed records through alternative processing
- **Recovery Strategies**:
  - Schema failures: Attempt parsing with relaxed validation
  - Enrichment failures: Retry with cached data
  - Storage failures: Retry with exponential backoff
- **Retry Limits**: Maximum 3 retry attempts with exponential backoff
- **Dead Letter Queue**: Store permanently failed records for manual review
- **Business Justification**: Maximize data recovery while preventing infinite retry loops