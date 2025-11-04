# System Components - VPC Flow Log Anomaly Detection System

## Component Architecture Overview

Based on hybrid organization strategy combining layer and domain approaches with clear service boundaries.

## Layer 1: Data Ingestion Components

### VPCFlowLogIngestionComponent
- **Purpose**: Ingest and initially process VPC Flow Logs
- **Responsibilities**:
  - Receive VPC Flow Logs from Kinesis Data Streams
  - Perform initial data validation and formatting
  - Route logs to enrichment pipeline
- **AWS Services**: Kinesis Data Streams, Lambda
- **Interfaces**: KinesisEventHandler, DataValidator

### LogEnrichmentComponent  
- **Purpose**: Enrich flow logs with contextual metadata
- **Responsibilities**:
  - Add geo-IP information using external services
  - Enrich with EC2 instance metadata (tags, security groups)
  - Perform DNS lookups for IP addresses
  - Filter out health checks and AWS service endpoints
- **AWS Services**: Lambda, EC2 API, Route53
- **Interfaces**: EnrichmentProcessor, MetadataProvider

### DataStorageComponent
- **Purpose**: Store processed logs for analysis and historical queries
- **Responsibilities**:
  - Store enriched logs in S3 Parquet format
  - Index logs in OpenSearch for fast queries
  - Manage data lifecycle and retention policies
- **AWS Services**: S3, OpenSearch, Kinesis Data Firehose
- **Interfaces**: StorageManager, IndexManager

## Layer 2: Anomaly Detection Components

### StatisticalDetectionComponent
- **Purpose**: Real-time statistical anomaly detection using Flink SQL
- **Responsibilities**:
  - Port scanning detection (>20 ports in 60s)
  - DDoS detection (high packet rates)
  - C2 beaconing detection (periodic connections)
  - Crypto mining detection (mining pool connections)
  - Tor usage detection (exit node matching)
- **AWS Services**: Kinesis Data Analytics (Flink)
- **Interfaces**: FlinkSQLProcessor, AnomalyDetector

### MLDetectionComponent
- **Purpose**: Machine learning-based behavioral analysis
- **Responsibilities**:
  - Isolation Forest anomaly detection
  - LSTM-based behavioral baseline analysis
  - Model training and inference
  - Baseline establishment and drift detection
- **AWS Services**: SageMaker, Lambda
- **Interfaces**: MLModelManager, BaselineAnalyzer

### AnomalyAggregationComponent
- **Purpose**: Aggregate and contextualize detected anomalies
- **Responsibilities**:
  - Combine statistical and ML detection results
  - Add enriched context to anomalies
  - Filter duplicate and related anomalies
  - Store anomalies in DynamoDB for agent processing
- **AWS Services**: Lambda, DynamoDB
- **Interfaces**: AnomalyAggregator, ContextEnricher

## Layer 3: AI Agent Components

### ThreatClassifierAgent
- **Purpose**: Classify anomalies as threats with severity assessment
- **Responsibilities**:
  - Analyze anomaly summaries using Claude 3.5 Sonnet
  - Determine threat status, severity, and confidence
  - Identify MITRE ATT&CK techniques
  - Provide reasoning and recommended actions
- **AWS Services**: Bedrock (Claude 3.5 Sonnet), Lambda (tools)
- **Interfaces**: BedrockAgent, ThreatAnalyzer

### InvestigationAgent
- **Purpose**: Deep investigation of high-severity threats
- **Responsibilities**:
  - Build attack timelines and identify entry vectors
  - Map lateral movement and assess data risk
  - Find persistence mechanisms
  - Generate comprehensive investigation reports
- **AWS Services**: Bedrock (Claude 3.5 Sonnet), Lambda (tools)
- **Interfaces**: BedrockAgent, InvestigationAnalyzer

### ResponseOrchestrationAgent
- **Purpose**: Execute automated responses based on threat severity
- **Responsibilities**:
  - Determine appropriate response actions
  - Execute isolation, credential revocation, alerting
  - Manage human-in-the-loop approvals
  - Coordinate incident response workflow
- **AWS Services**: Bedrock (Claude 3.5 Haiku), Lambda (tools)
- **Interfaces**: BedrockAgent, ResponseExecutor

### ThreatIntelligenceAgent
- **Purpose**: Enrich threats with external intelligence
- **Responsibilities**:
  - Fetch threat feeds from external sources
  - Maintain threat intelligence database
  - Provide contextual threat information
  - Update knowledge base with new intelligence
- **AWS Services**: Lambda, DynamoDB, OpenSearch, Bedrock (embeddings)
- **Interfaces**: ThreatIntelProvider, KnowledgeBaseManager

### RootCauseAnalysisAgent
- **Purpose**: Post-incident analysis and prevention recommendations
- **Responsibilities**:
  - Analyze resolved incidents for root causes
  - Identify contributing factors and control failures
  - Generate preventive recommendations
  - Assess implementation effort estimates
- **AWS Services**: Bedrock (Claude 3.5 Sonnet), Lambda (tools)
- **Interfaces**: BedrockAgent, RootCauseAnalyzer

## Layer 4: Orchestration Components

### WorkflowOrchestrationComponent
- **Purpose**: Orchestrate the overall threat detection and response workflow
- **Responsibilities**:
  - Manage state machine execution
  - Route anomalies through appropriate processing paths
  - Handle parallel and sequential agent execution
  - Manage workflow error handling and retries
- **AWS Services**: Step Functions, Lambda
- **Interfaces**: WorkflowManager, StateManager

### AgentCoordinationComponent
- **Purpose**: Coordinate interactions between Bedrock agents
- **Responsibilities**:
  - Manage agent execution order and dependencies
  - Handle agent context sharing and state management
  - Coordinate parallel agent execution for high-severity threats
  - Manage agent tool access and permissions
- **AWS Services**: Step Functions, Lambda, DynamoDB
- **Interfaces**: AgentCoordinator, ContextManager

## Layer 5: Interface Components

### AnalystDashboardComponent
- **Purpose**: Provide real-time security operations interface
- **Responsibilities**:
  - Display real-time threat map visualization
  - Show incident timeline and investigation workspace
  - Provide agent chat interface for analyst interaction
  - Handle user authentication and authorization
- **AWS Services**: CloudFront, S3, API Gateway, Lambda
- **Interfaces**: DashboardAPI, WebSocketHandler

### APIGatewayComponent
- **Purpose**: Provide unified API access to system functionality
- **Responsibilities**:
  - Expose REST APIs for dashboard and external integrations
  - Handle authentication and rate limiting
  - Route requests to appropriate backend services
  - Provide WebSocket support for real-time updates
- **AWS Services**: API Gateway, Lambda Authorizer
- **Interfaces**: APIHandler, AuthenticationManager

## Cross-Cutting Components

### StateManagementComponent
- **Purpose**: Manage system state across multiple data stores
- **Responsibilities**:
  - Manage incident lifecycle and status tracking
  - Store threat intelligence with TTL management
  - Handle analyst feedback and model retraining data
  - Provide consistent state access patterns
- **AWS Services**: DynamoDB, OpenSearch
- **Interfaces**: StateManager, DataAccessLayer

### MonitoringComponent
- **Purpose**: Provide comprehensive system observability
- **Responsibilities**:
  - Monitor system health and performance metrics
  - Track cost optimization and funnel effectiveness
  - Provide alerting for system anomalies
  - Generate operational dashboards and reports
- **AWS Services**: CloudWatch, X-Ray, SNS
- **Interfaces**: MetricsCollector, AlertManager

### ConfigurationComponent
- **Purpose**: Manage system configuration and deployment
- **Responsibilities**:
  - Manage environment-specific configurations
  - Handle feature flags and operational parameters
  - Provide configuration validation and rollback
  - Support dynamic configuration updates
- **AWS Services**: Systems Manager Parameter Store, Lambda
- **Interfaces**: ConfigManager, ParameterProvider