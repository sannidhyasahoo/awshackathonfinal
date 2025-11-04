# Units of Work - VPC Flow Log Anomaly Detection System

## Unit Architecture Overview

Based on service-oriented architecture with tiered cost optimization and hybrid integration patterns.

**Total Units**: 6 services organized by business capabilities and cost tiers
**Integration**: Hybrid approach with APIs for synchronous operations and events for asynchronous workflows
**Infrastructure**: Core shared services with service-specific concerns embedded

## Unit 1: Data Ingestion Service

### Purpose
Handle VPC Flow Log ingestion with cost-optimized filtering and enrichment

### Components Included
- **VPCFlowLogIngestionComponent** - Kinesis stream processing
- **LogEnrichmentComponent** - Metadata enrichment and geo-IP lookup
- **DataStorageComponent** - S3 Parquet storage and OpenSearch indexing

### Responsibilities
- Ingest 100M+ VPC Flow Logs daily from Kinesis Data Streams
- Apply Tier 1 filtering (health checks, AWS endpoints) - 99% reduction
- Enrich logs with geo-IP, EC2 metadata, DNS lookups
- Store processed logs in S3 Parquet format
- Index enriched logs in OpenSearch for fast queries
- Manage data lifecycle and retention policies

### Technology Stack
- **Compute**: Lambda functions for processing
- **Storage**: S3 (Parquet), OpenSearch Serverless
- **Streaming**: Kinesis Data Streams, Kinesis Data Firehose
- **External APIs**: GeoIP services, EC2 API, Route53

### Cost Tier
**Low-cost tier** - Optimized for high-volume, low-cost processing

### Deployment Model
Independent service with auto-scaling Lambda functions

### Key Interfaces
- **Input**: Kinesis Data Streams (VPC Flow Logs)
- **Output**: S3 (processed logs), OpenSearch (indexed logs), EventBridge (processing events)
- **APIs**: REST API for historical data queries

## Unit 2: Anomaly Detection Service

### Purpose
Real-time and ML-based anomaly detection with statistical analysis

### Components Included
- **StatisticalDetectionComponent** - Flink SQL real-time detection
- **MLDetectionComponent** - SageMaker ML models
- **AnomalyAggregationComponent** - Result aggregation and contextualization

### Responsibilities
- Tier 2 filtering: Statistical detection (port scans, DDoS, beaconing, crypto mining, Tor) - 90% reduction
- Tier 3 filtering: ML anomaly detection (Isolation Forest, LSTM) - 50% reduction
- Aggregate statistical and ML detection results
- Add enriched context to anomalies
- Filter duplicate and related anomalies
- Store anomalies in DynamoDB for agent processing

### Technology Stack
- **Real-time Processing**: Kinesis Data Analytics (Flink 1.15)
- **ML Platform**: SageMaker (scikit-learn, TensorFlow)
- **Compute**: Lambda functions for aggregation
- **Storage**: DynamoDB (anomalies), S3 (ML models)

### Cost Tier
**Medium-cost tier** - Balanced processing with ML inference

### Deployment Model
Hybrid: Kinesis Data Analytics for streaming, SageMaker endpoints for ML, Lambda for orchestration

### Key Interfaces
- **Input**: S3 (processed logs), OpenSearch (historical data)
- **Output**: DynamoDB (anomalies), EventBridge (anomaly events)
- **APIs**: REST API for anomaly queries and model management

## Unit 3: AI Agent Service

### Purpose
Bedrock agent orchestration for threat analysis and response

### Components Included
- **ThreatClassifierAgent** - Claude 3.5 Sonnet for threat classification
- **InvestigationAgent** - Claude 3.5 Sonnet for deep investigation
- **ResponseOrchestrationAgent** - Claude 3.5 Haiku for automated response
- **ThreatIntelligenceAgent** - Threat feed management and enrichment
- **RootCauseAnalysisAgent** - Claude 3.5 Sonnet for post-incident analysis

### Responsibilities
- Tier 4 filtering: AI-powered threat classification and analysis
- Classify anomalies with severity assessment and MITRE ATT&CK mapping
- Conduct deep investigations for CRITICAL/HIGH severity threats
- Execute automated responses (isolation, credential revocation, alerting)
- Manage threat intelligence feeds and knowledge base
- Perform post-incident root cause analysis
- Provide explainable AI reasoning for all decisions

### Technology Stack
- **AI Platform**: Amazon Bedrock (Claude 3.5 Sonnet/Haiku, Titan Embeddings)
- **Tools**: Lambda functions for all agent tool implementations
- **Knowledge Base**: OpenSearch with Bedrock embeddings
- **Storage**: DynamoDB (threat intel, incidents), OpenSearch (knowledge base)

### Cost Tier
**High-cost tier** - Expensive AI processing with token optimization

### Deployment Model
Bedrock agents with Lambda-based tool implementations

### Key Interfaces
- **Input**: DynamoDB (anomalies), EventBridge (workflow triggers)
- **Output**: DynamoDB (classifications, investigations), EventBridge (response events)
- **Tools**: Lambda proxy functions for AWS service access

## Unit 4: Workflow Orchestration Service

### Purpose
Coordinate system workflows and agent execution patterns

### Components Included
- **WorkflowOrchestrationComponent** - Step Functions state machines
- **AgentCoordinationComponent** - Agent execution coordination

### Responsibilities
- Orchestrate complete threat detection pipeline
- Route anomalies based on threat severity (sequential vs parallel execution)
- Coordinate agent execution order and dependencies
- Manage agent context sharing and state synchronization
- Handle workflow error handling and retries
- Implement graceful degradation during service outages

### Technology Stack
- **Orchestration**: AWS Step Functions
- **Compute**: Lambda functions for coordination logic
- **Storage**: DynamoDB (workflow state, agent context)
- **Events**: EventBridge for workflow triggers

### Cost Tier
**Low-cost tier** - Orchestration logic with minimal compute

### Deployment Model
Step Functions state machines with Lambda integrations

### Key Interfaces
- **Input**: EventBridge (anomaly events, agent triggers)
- **Output**: EventBridge (workflow events), DynamoDB (state updates)
- **Integration**: Bedrock agents, Lambda functions, external services

## Unit 5: Dashboard and API Service

### Purpose
Analyst interface and external system integration

### Components Included
- **AnalystDashboardComponent** - React-based security operations interface
- **APIGatewayComponent** - Unified API access and WebSocket support

### Responsibilities
- Provide real-time threat map visualization
- Display incident timeline and investigation workspace
- Enable agent chat interface for analyst interaction
- Serve REST APIs for dashboard and external integrations
- Handle WebSocket connections for real-time updates
- Manage user authentication and authorization
- Integrate with external systems (JIRA, Slack, PagerDuty)

### Technology Stack
- **Frontend**: React application hosted on S3/CloudFront
- **API**: API Gateway (REST + WebSocket)
- **Compute**: Lambda functions for API logic
- **Authentication**: Cognito or IAM-based authentication

### Cost Tier
**Low-cost tier** - Static hosting with serverless APIs

### Deployment Model
Static website with serverless API backend

### Key Interfaces
- **Input**: DynamoDB (incidents, threat intel), OpenSearch (analytics)
- **Output**: WebSocket (real-time updates), REST APIs (data access)
- **External**: JIRA API, Slack API, PagerDuty API

## Unit 6: Shared Infrastructure Service

### Purpose
Core infrastructure and cross-cutting concerns

### Components Included
- **StateManagementComponent** - Centralized state management
- **MonitoringComponent** - System observability and alerting
- **ConfigurationComponent** - Configuration and deployment management

### Responsibilities
- Manage system state across DynamoDB tables and OpenSearch indexes
- Provide comprehensive system monitoring and cost tracking
- Handle configuration management and feature flags
- Generate operational dashboards and alerts
- Manage deployment orchestration and rollback procedures
- Implement circuit breakers and resilience patterns

### Technology Stack
- **Storage**: DynamoDB (state), OpenSearch (analytics)
- **Monitoring**: CloudWatch, X-Ray, SNS
- **Configuration**: Systems Manager Parameter Store
- **Deployment**: CDK, CodePipeline

### Cost Tier
**Low-cost tier** - Infrastructure services with minimal overhead

### Deployment Model
Shared services consumed by all other units

### Key Interfaces
- **Provides**: State management APIs, monitoring dashboards, configuration services
- **Consumes**: Metrics from all services, configuration requests
- **External**: AWS services, deployment pipelines

## Unit Integration Architecture

### Data Flow Between Units
```
VPC Logs → Unit 1 (Ingestion) → Unit 2 (Detection) → Unit 3 (AI Agents)
                                                    ↓
Unit 4 (Orchestration) ← Unit 5 (Dashboard) ← Unit 6 (Infrastructure)
```

### Cost Optimization Funnel
```
100M logs/day → Unit 1 (99% reduction) → Unit 2 (95% reduction) → Unit 3 (AI processing)
                1M logs/day              50K anomalies/day        250K tokens/day
```

### Integration Patterns by Unit Pair

#### Unit 1 → Unit 2 (Ingestion to Detection)
- **Pattern**: Event-driven (asynchronous)
- **Mechanism**: S3 events trigger detection processing
- **Data**: Processed logs in S3, metadata in OpenSearch

#### Unit 2 → Unit 3 (Detection to AI Agents)
- **Pattern**: Event-driven (asynchronous)
- **Mechanism**: DynamoDB streams trigger agent workflows
- **Data**: Anomaly records with enriched context

#### Unit 3 → Unit 4 (Agents to Orchestration)
- **Pattern**: Synchronous coordination
- **Mechanism**: Step Functions orchestrate agent execution
- **Data**: Agent results and workflow state

#### Unit 4 → Unit 5 (Orchestration to Dashboard)
- **Pattern**: Hybrid (WebSocket + REST)
- **Mechanism**: Real-time events via WebSocket, detailed data via REST
- **Data**: Incident updates, investigation results

#### All Units → Unit 6 (Infrastructure)
- **Pattern**: Service consumption
- **Mechanism**: Direct API calls for state, configuration, monitoring
- **Data**: Metrics, configuration, state management

## Deployment Independence

### Unit 1: Data Ingestion Service
- **Dependencies**: VPC Flow Logs (external), Unit 6 (configuration)
- **Independence**: Can process and store logs without other units
- **Fallback**: Basic storage without enrichment

### Unit 2: Anomaly Detection Service
- **Dependencies**: Unit 1 (processed logs), Unit 6 (configuration)
- **Independence**: Can detect anomalies from stored data
- **Fallback**: Statistical detection only (no ML)

### Unit 3: AI Agent Service
- **Dependencies**: Unit 2 (anomalies), Unit 6 (state management)
- **Independence**: Can process anomalies independently
- **Fallback**: Rule-based classification without AI

### Unit 4: Workflow Orchestration Service
- **Dependencies**: Unit 3 (agents), Unit 6 (state management)
- **Independence**: Can orchestrate available services
- **Fallback**: Manual workflow execution

### Unit 5: Dashboard and API Service
- **Dependencies**: Unit 6 (data access), authentication service
- **Independence**: Can display cached/historical data
- **Fallback**: Read-only mode with basic functionality

### Unit 6: Shared Infrastructure Service
- **Dependencies**: AWS services only
- **Independence**: Fully independent core infrastructure
- **Fallback**: Essential services only (state, basic monitoring)