# Unit Dependency Matrix - VPC Flow Log Anomaly Detection System

## Dependency Overview

6 services with hybrid integration patterns and tiered cost optimization.

## Dependency Matrix

| Unit | Unit 1 (Ingestion) | Unit 2 (Detection) | Unit 3 (AI Agents) | Unit 4 (Orchestration) | Unit 5 (Dashboard) | Unit 6 (Infrastructure) |
|------|-------------------|-------------------|-------------------|----------------------|-------------------|----------------------|
| **Unit 1 (Ingestion)** | - | Provides data | - | - | - | Consumes config/monitoring |
| **Unit 2 (Detection)** | Consumes data | - | Provides anomalies | - | - | Consumes config/monitoring |
| **Unit 3 (AI Agents)** | - | Consumes anomalies | - | Coordinated by | - | Consumes state/config |
| **Unit 4 (Orchestration)** | - | - | Coordinates | - | Provides workflow data | Consumes state/config |
| **Unit 5 (Dashboard)** | Queries historical | Queries anomalies | Displays results | Displays workflows | - | Consumes all data |
| **Unit 6 (Infrastructure)** | Provides services | Provides services | Provides services | Provides services | Provides services | - |

## Detailed Dependencies

### Unit 1: Data Ingestion Service

#### Upstream Dependencies (What Unit 1 depends on)
- **External**: VPC Flow Logs via Kinesis Data Streams
- **Unit 6**: Configuration (enrichment settings, filtering rules)
- **Unit 6**: Monitoring (health checks, performance metrics)

#### Downstream Dependencies (What depends on Unit 1)
- **Unit 2**: Processed logs in S3 Parquet format
- **Unit 2**: Indexed logs in OpenSearch for ML training
- **Unit 5**: Historical log data for dashboard queries

#### Integration Patterns
- **Input**: Kinesis Data Streams (real-time)
- **Output**: S3 events (asynchronous), OpenSearch indexing (near real-time)
- **Configuration**: Parameter Store polling (periodic)
- **Monitoring**: CloudWatch metrics (continuous)

#### Failure Handling
- **Graceful Degradation**: Process logs without enrichment if external APIs fail
- **Circuit Breaker**: Disable enrichment after 5 consecutive failures
- **Retry Strategy**: Exponential backoff for transient failures
- **Fallback**: Store raw logs if processing fails

### Unit 2: Anomaly Detection Service

#### Upstream Dependencies (What Unit 2 depends on)
- **Unit 1**: Processed logs from S3 (batch processing)
- **Unit 1**: Real-time logs from OpenSearch (streaming)
- **Unit 6**: ML model configurations and thresholds
- **Unit 6**: Detection rule configurations

#### Downstream Dependencies (What depends on Unit 2)
- **Unit 3**: Anomaly records in DynamoDB
- **Unit 4**: Anomaly events via EventBridge
- **Unit 5**: Anomaly statistics for dashboard

#### Integration Patterns
- **Input**: S3 events trigger batch processing, Kinesis for real-time
- **Output**: DynamoDB streams trigger agent workflows
- **ML Models**: SageMaker endpoints for inference
- **Configuration**: Parameter Store for detection thresholds

#### Failure Handling
- **Graceful Degradation**: Statistical detection only if ML models fail
- **Circuit Breaker**: Disable ML processing after 10 failures
- **Retry Strategy**: 3 retries for SageMaker endpoint calls
- **Fallback**: Rule-based detection with predefined patterns

### Unit 3: AI Agent Service

#### Upstream Dependencies (What Unit 3 depends on)
- **Unit 2**: Anomaly records from DynamoDB
- **Unit 4**: Orchestration triggers via Step Functions
- **Unit 6**: Agent configurations and prompts
- **Unit 6**: Threat intelligence data and knowledge base

#### Downstream Dependencies (What depends on Unit 3)
- **Unit 4**: Agent execution results and status
- **Unit 5**: Investigation reports and classifications
- **Unit 6**: Incident records and audit trails

#### Integration Patterns
- **Input**: DynamoDB streams (anomalies), Step Functions (orchestration)
- **Output**: DynamoDB (results), EventBridge (completion events)
- **Tools**: Lambda proxy pattern for all AWS service access
- **Knowledge Base**: OpenSearch with Bedrock embeddings

#### Failure Handling
- **Graceful Degradation**: Rule-based classification if Bedrock unavailable
- **Circuit Breaker**: Disable AI processing after 10 consecutive failures
- **Retry Strategy**: 3 retries with exponential backoff for Bedrock calls
- **Fallback**: Manual investigation workflow with predefined templates

### Unit 4: Workflow Orchestration Service

#### Upstream Dependencies (What Unit 4 depends on)
- **Unit 2**: Anomaly events via EventBridge
- **Unit 3**: Agent availability and execution capabilities
- **Unit 6**: Workflow configurations and state management

#### Downstream Dependencies (What depends on Unit 4)
- **Unit 3**: Agent execution coordination and context sharing
- **Unit 5**: Workflow status and execution history
- **Unit 6**: Workflow metrics and audit logs

#### Integration Patterns
- **Input**: EventBridge events (anomaly triggers)
- **Output**: Step Functions executions, DynamoDB state updates
- **Coordination**: Synchronous agent calls, asynchronous result handling
- **State**: DynamoDB for workflow state and agent context

#### Failure Handling
- **Graceful Degradation**: Sequential execution if parallel coordination fails
- **Circuit Breaker**: Disable complex workflows after repeated failures
- **Retry Strategy**: Step Functions built-in retry with exponential backoff
- **Fallback**: Manual workflow execution with analyst intervention

### Unit 5: Dashboard and API Service

#### Upstream Dependencies (What Unit 5 depends on)
- **Unit 1**: Historical log data via OpenSearch
- **Unit 2**: Anomaly data via DynamoDB
- **Unit 3**: Investigation results and classifications
- **Unit 4**: Workflow status and execution history
- **Unit 6**: All system state and configuration data

#### Downstream Dependencies (What depends on Unit 5)
- **External Systems**: JIRA (ticket creation), Slack (notifications), PagerDuty (alerting)
- **Analysts**: Real-time threat monitoring and investigation

#### Integration Patterns
- **Real-time**: WebSocket connections for live threat updates
- **Batch**: REST API calls for detailed data retrieval
- **Authentication**: Cognito/IAM for user management
- **External**: REST API calls to JIRA, Slack, PagerDuty

#### Failure Handling
- **Graceful Degradation**: Cached data display if real-time feeds fail
- **Circuit Breaker**: Disable external integrations after 5 failures
- **Retry Strategy**: 3 retries for external API calls
- **Fallback**: Read-only mode with historical data only

### Unit 6: Shared Infrastructure Service

#### Upstream Dependencies (What Unit 6 depends on)
- **AWS Services**: DynamoDB, OpenSearch, CloudWatch, Parameter Store
- **All Units**: Metrics, logs, and state information

#### Downstream Dependencies (What depends on Unit 6)
- **All Units**: Configuration, state management, monitoring services

#### Integration Patterns
- **Configuration**: Parameter Store with caching and change notifications
- **State**: DynamoDB with consistent reads for critical operations
- **Monitoring**: CloudWatch metrics with custom dashboards
- **Deployment**: CDK with automated rollback capabilities

#### Failure Handling
- **High Availability**: Multi-AZ deployment for critical components
- **Circuit Breaker**: Not applicable (core infrastructure)
- **Retry Strategy**: Built into AWS SDK clients
- **Fallback**: Cached configuration and degraded monitoring

## Cross-Unit Communication Patterns

### Synchronous Communication (Request-Response)
```
Unit 5 (Dashboard) → Unit 6 (Infrastructure) → DynamoDB/OpenSearch
Unit 4 (Orchestration) → Unit 3 (AI Agents) → Bedrock
Unit 3 (AI Agents) → Lambda Tools → AWS Services
```

### Asynchronous Communication (Event-Driven)
```
Unit 1 (Ingestion) → S3 Events → Unit 2 (Detection)
Unit 2 (Detection) → DynamoDB Streams → Unit 4 (Orchestration)
Unit 4 (Orchestration) → EventBridge → Unit 5 (Dashboard)
```

### Real-time Communication (Streaming)
```
VPC Logs → Kinesis → Unit 1 (Ingestion)
Unit 1 → Kinesis Data Analytics → Unit 2 (Detection)
Unit 5 (Dashboard) → WebSocket → Analysts
```

## Dependency Criticality Levels

### Critical Dependencies (System fails without these)
- **Unit 1 → VPC Flow Logs**: Core data source
- **Unit 6 → AWS Services**: Infrastructure foundation
- **Unit 2 → Unit 1**: Anomaly detection requires processed logs

### Important Dependencies (Degraded functionality without these)
- **Unit 3 → Unit 2**: AI agents need anomalies to process
- **Unit 4 → Unit 3**: Orchestration coordinates agent execution
- **Unit 5 → All Units**: Dashboard displays system state

### Optional Dependencies (Enhanced functionality)
- **Unit 1 → External APIs**: Enrichment improves detection quality
- **Unit 3 → Threat Intel**: External feeds enhance analysis
- **Unit 5 → External Systems**: Integrations improve workflow

## Deployment Sequence

### Phase 1: Foundation (Unit 6)
1. Deploy shared infrastructure components
2. Set up monitoring and configuration services
3. Validate core AWS service connectivity

### Phase 2: Data Pipeline (Units 1-2)
1. Deploy Unit 1 (Data Ingestion Service)
2. Validate log processing and storage
3. Deploy Unit 2 (Anomaly Detection Service)
4. Validate anomaly detection pipeline

### Phase 3: Intelligence Layer (Units 3-4)
1. Deploy Unit 3 (AI Agent Service)
2. Configure Bedrock agents and tools
3. Deploy Unit 4 (Workflow Orchestration Service)
4. Validate agent coordination and workflows

### Phase 4: Interface Layer (Unit 5)
1. Deploy Unit 5 (Dashboard and API Service)
2. Configure authentication and external integrations
3. Validate end-to-end system functionality

## Integration Testing Strategy

### Unit-Level Testing
- Each unit tested independently with mocked dependencies
- Contract testing for API interfaces
- Performance testing for throughput requirements

### Integration Testing
- Pairwise integration testing between dependent units
- End-to-end workflow testing with real data
- Failure scenario testing with circuit breaker validation

### System Testing
- Full system testing with production-like data volumes
- Cost optimization validation (funnel effectiveness)
- Security testing with threat simulation

## Monitoring and Observability

### Per-Unit Monitoring
- Each unit reports health, performance, and business metrics
- Custom CloudWatch dashboards per unit
- Unit-specific alerting thresholds

### Cross-Unit Monitoring
- End-to-end transaction tracing with X-Ray
- Dependency health monitoring
- Cost tracking across the processing funnel

### System-Level Monitoring
- Overall system health and SLA compliance
- Security metrics and threat detection effectiveness
- Operational dashboards for analysts and administrators