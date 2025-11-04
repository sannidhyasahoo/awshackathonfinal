# Component Dependencies - VPC Flow Log Anomaly Detection System

## Dependency Architecture Overview

Based on hybrid organization with clear service boundaries and graceful degradation capabilities.

## Data Flow Architecture

```
VPC Flow Logs → Kinesis → Ingestion → Enrichment → Storage
                                    ↓
Statistical Detection ← Aggregation ← ML Detection
        ↓
    DynamoDB Anomalies
        ↓
Threat Classifier Agent → {Investigation Agent + Response Agent + ThreatIntel Agent} → Root Cause Agent
        ↓                                    ↓
Step Functions Orchestration → Dashboard API → React Dashboard
```

## Layer Dependencies

### Layer 1: Data Ingestion Dependencies
```
VPCFlowLogIngestionComponent
├── Depends on: Kinesis Data Streams (external)
├── Calls: LogEnrichmentComponent
└── Error handling: DataStorageComponent (for failed records)

LogEnrichmentComponent  
├── Depends on: EC2 API, Route53, External GeoIP services
├── Calls: DataStorageComponent
├── Fallback: Basic processing without enrichment
└── Caching: ElastiCache for metadata lookups

DataStorageComponent
├── Depends on: S3, OpenSearch, Kinesis Data Firehose
├── Called by: LogEnrichmentComponent, AnomalyAggregationComponent
└── Provides: Historical data access for ML and agents
```

### Layer 2: Anomaly Detection Dependencies
```
StatisticalDetectionComponent
├── Depends on: Kinesis Data Analytics (Flink)
├── Input: Real-time flow logs from DataStorageComponent
├── Calls: AnomalyAggregationComponent
└── Fallback: Lambda-based detection if Flink unavailable

MLDetectionComponent
├── Depends on: SageMaker endpoints, S3 model storage
├── Input: Historical data from DataStorageComponent
├── Calls: AnomalyAggregationComponent
├── Training: Batch processing from S3 data
└── Fallback: Statistical detection only if ML unavailable

AnomalyAggregationComponent
├── Input: StatisticalDetectionComponent + MLDetectionComponent
├── Depends on: DynamoDB (anomalies table)
├── Calls: WorkflowOrchestrationComponent (triggers agents)
└── Provides: Enriched anomalies for agent processing
```

### Layer 3: AI Agent Dependencies
```
ThreatClassifierAgent
├── Depends on: Bedrock (Claude 3.5 Sonnet), Lambda tools
├── Input: Anomalies from AnomalyAggregationComponent
├── Tools: get_resource_baseline(), check_threat_intel(), get_recent_cloudtrail()
├── Calls: AgentCoordinationComponent (triggers other agents)
└── Fallback: Rule-based classification if Bedrock unavailable

InvestigationAgent
├── Depends on: Bedrock (Claude 3.5 Sonnet), Lambda tools
├── Triggered by: ThreatClassifierAgent (CRITICAL/HIGH threats)
├── Tools: query_cloudtrail(), query_flow_logs_history(), get_iam_permissions()
├── Parallel execution: With ResponseOrchestrationAgent for high-severity
└── Fallback: Basic investigation template if Bedrock unavailable

ResponseOrchestrationAgent
├── Depends on: Bedrock (Claude 3.5 Haiku), Lambda tools
├── Triggered by: ThreatClassifierAgent (all threats)
├── Tools: isolate_instance(), revoke_credentials(), notify_team()
├── Human approval: Required for destructive production actions
└── Fallback: Manual response procedures if automation unavailable

ThreatIntelligenceAgent
├── Depends on: Lambda, DynamoDB, OpenSearch, External APIs
├── Scheduled: Hourly threat feed updates
├── Provides: Threat context for all other agents
├── Knowledge Base: MITRE ATT&CK + historical incidents
└── Fallback: Cached threat intelligence if external sources unavailable

RootCauseAnalysisAgent
├── Depends on: Bedrock (Claude 3.5 Sonnet), Lambda tools
├── Triggered by: Post-incident (after resolution)
├── Input: Complete incident data from StateManagementComponent
├── Tools: Security assessment tools, configuration analysis
└── Fallback: Manual root cause analysis if agent unavailable
```

### Layer 4: Orchestration Dependencies
```
WorkflowOrchestrationComponent
├── Depends on: Step Functions, Lambda
├── Triggered by: AnomalyAggregationComponent
├── Coordinates: All AI agents based on threat severity
├── State management: DynamoDB for workflow state
└── Error handling: Retry logic with exponential backoff

AgentCoordinationComponent
├── Depends on: Step Functions, DynamoDB
├── Manages: Agent execution order and context sharing
├── Parallel coordination: For CRITICAL/HIGH severity threats
├── Sequential coordination: For MEDIUM/LOW severity threats
└── Context sharing: Shared DynamoDB table for agent communication
```

### Layer 5: Interface Dependencies
```
AnalystDashboardComponent
├── Depends on: CloudFront, S3, API Gateway
├── Data sources: APIGatewayComponent, WebSocket connections
├── Authentication: Cognito or IAM-based
└── Real-time updates: WebSocket for alerts, REST for detailed data

APIGatewayComponent
├── Depends on: API Gateway, Lambda
├── Data sources: StateManagementComponent, MonitoringComponent
├── WebSocket: Real-time threat updates
├── REST APIs: Historical data, configuration management
└── Rate limiting: Per-user and per-endpoint limits
```

## Cross-Cutting Dependencies

### StateManagementComponent Dependencies
```
StateManagementComponent
├── Storage: DynamoDB (incidents, threat intel, feedback)
├── Search: OpenSearch (full-text search, analytics)
├── Used by: All agents, orchestration, dashboard
├── Consistency: Eventually consistent with strong consistency for critical operations
└── Backup: Point-in-time recovery enabled
```

### MonitoringComponent Dependencies
```
MonitoringComponent
├── Metrics: CloudWatch, X-Ray, custom metrics
├── Alerting: SNS, CloudWatch Alarms
├── Observes: All system components
├── Cost tracking: Bedrock token usage, processing funnel metrics
└── Dashboards: Operational health, security metrics, cost optimization
```

### ConfigurationComponent Dependencies
```
ConfigurationComponent
├── Storage: Systems Manager Parameter Store
├── Used by: All components for runtime configuration
├── Feature flags: Dynamic behavior control
├── Validation: Configuration schema validation
└── Rollback: Version control for configuration changes
```

## Communication Patterns

### Synchronous Dependencies (Request-Response)
```
Dashboard → API Gateway → Lambda → DynamoDB/OpenSearch
Agent Tools → Lambda Proxy → AWS Services
Configuration → Parameter Store → Components
```

### Asynchronous Dependencies (Event-Driven)
```
Kinesis → Lambda (Ingestion) → EventBridge → Processing Pipeline
Anomaly Detection → EventBridge → Step Functions → Agents
Agent Results → EventBridge → Dashboard Updates
```

### Real-time Dependencies (Streaming)
```
Kinesis Data Analytics → Real-time Detection
WebSocket → Dashboard Updates
Agent Chat → Bedrock Streaming
```

## Failure Dependencies and Fallbacks

### Critical Path Dependencies
```
VPC Logs → Kinesis → Basic Detection → DynamoDB → Manual Review
(Minimum viable system during outages)
```

### Graceful Degradation Chain
```
Level 1: Full system operational
├── All enrichment, ML detection, AI agents active
└── Real-time dashboard with full functionality

Level 2: Enrichment degraded
├── Basic flow log processing without geo-IP/DNS
├── Statistical detection active, ML detection cached
└── AI agents operational with reduced context

Level 3: ML detection degraded  
├── Statistical detection only
├── AI agents operational with basic context
└── Dashboard shows statistical alerts only

Level 4: AI agents degraded
├── Statistical detection with rule-based classification
├── Manual investigation required
└── Dashboard shows raw alerts for analyst review

Level 5: Emergency mode
├── Basic anomaly detection only
├── All alerts require manual investigation
└── Minimal dashboard functionality
```

## Dependency Management Strategies

### Circuit Breaker Implementation
```python
# External service dependencies
- Threat Intelligence APIs: 5 failures → 30s circuit open
- Enrichment services: 3 failures → 60s circuit open  
- Bedrock agents: 10 failures → 120s circuit open
- Dashboard APIs: 5 failures → 15s circuit open
```

### Retry Strategies
```python
# Transient failure handling
- DynamoDB operations: 3 retries with exponential backoff
- Lambda invocations: 2 retries with jitter
- External API calls: 5 retries with exponential backoff
- Agent tool calls: 3 retries with circuit breaker
```

### Caching Dependencies
```python
# Performance and resilience caching
- Threat intelligence: 1-hour TTL with stale-while-revalidate
- EC2 metadata: 15-minute TTL with background refresh
- Configuration: 5-minute TTL with immediate invalidation
- Agent prompts: 24-hour TTL with version control
```

## Data Consistency Requirements

### Strong Consistency Required
- Incident state transitions (DynamoDB with consistent reads)
- Agent coordination state (DynamoDB transactions)
- Configuration updates (Parameter Store with immediate propagation)

### Eventual Consistency Acceptable
- Threat intelligence updates (DynamoDB with TTL)
- Historical analytics (OpenSearch with refresh intervals)
- Dashboard metrics (CloudWatch with 1-minute delays)
- Audit logs (S3 with eventual consistency)

## Security Dependencies

### IAM Role Dependencies
```
- Agent execution roles: Bedrock + specific tool permissions
- Lambda execution roles: Service-specific least privilege
- Dashboard roles: Read-only access to operational data
- Admin roles: Full system access with MFA requirement
```

### Network Dependencies
```
- VPC endpoints: For private AWS service access
- Security groups: Restrictive ingress, specific egress
- NACLs: Additional network-level protection
- WAF: API Gateway protection with rate limiting
```

### Encryption Dependencies
```
- Data in transit: TLS 1.2+ for all communications
- Data at rest: KMS encryption for DynamoDB, S3, OpenSearch
- Agent communications: Bedrock native encryption
- Dashboard: CloudFront with HTTPS enforcement
```