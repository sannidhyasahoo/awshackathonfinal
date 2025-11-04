# Unit-Story Mapping - VPC Flow Log Anomaly Detection System

## Story Mapping Overview

Since User Stories stage was skipped for this internal security system, this document maps functional requirements to units of work for development planning.

## Functional Requirement to Unit Mapping

### Unit 1: Data Ingestion Service

#### Mapped Functional Requirements
- **FR1.1**: Ingest VPC Flow Logs via Kinesis Data Streams
- **FR1.2**: Enrich logs with geo-IP, resource metadata (EC2 tags, security groups), DNS lookups
- **FR1.3**: Filter out health checks, AWS service endpoints, sample benign traffic at 1%
- **FR1.4**: Store processed data in S3 (Parquet format) and OpenSearch

#### Development Stories (Derived from Requirements)
1. **As a system**, I need to receive VPC Flow Logs from Kinesis Data Streams at 100M+ logs/day
2. **As a system**, I need to enrich flow logs with geo-IP information for threat analysis
3. **As a system**, I need to add EC2 metadata (tags, security groups) to flow logs
4. **As a system**, I need to perform DNS lookups for IP addresses in flow logs
5. **As a system**, I need to filter out health checks and AWS service endpoints (99% reduction)
6. **As a system**, I need to store enriched logs in S3 Parquet format for analysis
7. **As a system**, I need to index logs in OpenSearch for fast historical queries
8. **As a system**, I need to manage data lifecycle and retention policies

#### Acceptance Criteria Summary
- Process 100M+ logs daily without data loss
- Achieve 99% filtering of benign traffic
- Enrich logs with contextual metadata within 30 seconds
- Store logs in queryable format with <5 minute latency

### Unit 2: Anomaly Detection Service

#### Mapped Functional Requirements
- **FR2.1**: Port Scanning Detection - Source connecting to >20 unique ports in 60s
- **FR2.2**: DDoS Detection - High packet rate to single destination (SYN floods, UDP floods)
- **FR2.3**: C2 Beaconing Detection - Regular periodic connections (coefficient of variation <10%)
- **FR2.4**: Crypto Mining Detection - Connections to mining pool IPs, ports 3333/4444/9999
- **FR2.5**: Tor Usage Detection - Match against Tor exit node list (updated hourly)
- **FR2.6**: ML-based Behavioral Analysis - Isolation Forest and LSTM for baseline deviations
- **FR2.7**: Output anomalies to DynamoDB with enriched context (NOT raw logs)

#### Development Stories (Derived from Requirements)
1. **As a system**, I need to detect port scanning (>20 ports in 60s) using Flink SQL
2. **As a system**, I need to detect DDoS patterns (high packet rates) in real-time
3. **As a system**, I need to detect C2 beaconing using coefficient of variation analysis
4. **As a system**, I need to detect crypto mining connections to known mining pools
5. **As a system**, I need to detect Tor usage by matching against exit node lists
6. **As a system**, I need to train Isolation Forest models for anomaly detection
7. **As a system**, I need to train LSTM models for behavioral baseline analysis
8. **As a system**, I need to aggregate statistical and ML detection results
9. **As a system**, I need to store anomalies in DynamoDB with enriched context

#### Acceptance Criteria Summary
- Detect all 5 threat types with <5% false positive rate
- Process anomalies within 5 minutes of log ingestion
- Reduce data volume by 95% through intelligent filtering
- Provide enriched context for AI agent processing

### Unit 3: AI Agent Service

#### Mapped Functional Requirements
- **FR3.1**: Threat Classifier Agent with Claude 3.5 Sonnet
- **FR3.2**: Investigation Agent for CRITICAL/HIGH severity threats
- **FR3.3**: Response Orchestration Agent with Claude 3.5 Haiku
- **FR3.4**: Threat Intelligence Enrichment Agent
- **FR3.5**: Root Cause Analysis Agent for post-incident analysis

#### Development Stories (Derived from Requirements)
1. **As a security analyst**, I need threats classified with severity and confidence scores
2. **As a security analyst**, I need MITRE ATT&CK techniques identified for threats
3. **As a security analyst**, I need explainable reasoning for all threat classifications
4. **As a security analyst**, I need deep investigations for high-severity threats
5. **As a security analyst**, I need attack timelines and entry vector analysis
6. **As a security analyst**, I need automated response actions based on threat severity
7. **As a security analyst**, I need human approval for destructive production actions
8. **As a security analyst**, I need threat intelligence enrichment from external feeds
9. **As a security analyst**, I need root cause analysis for resolved incidents
10. **As a security analyst**, I need preventive recommendations with effort estimates

#### Acceptance Criteria Summary
- Classify threats with explainable AI reasoning
- Generate actionable investigation reports for CRITICAL/HIGH threats
- Execute appropriate automated responses based on severity
- Maintain threat intelligence knowledge base with hourly updates

### Unit 4: Workflow Orchestration Service

#### Mapped Functional Requirements
- **FR4.1**: State machine: DetectAnomaly → EnrichThreatIntel → ClassifyThreat
- **FR4.2**: Branch logic: FALSE POSITIVE → LogAndUpdateModel
- **FR4.3**: Branch logic: CRITICAL/HIGH → Parallel{Investigation + Containment + Notify} → RootCauseAnalysis
- **FR4.4**: Branch logic: MEDIUM/LOW → QueueForAnalystReview

#### Development Stories (Derived from Requirements)
1. **As a system**, I need to orchestrate the complete threat detection pipeline
2. **As a system**, I need to route anomalies based on threat classification results
3. **As a system**, I need to execute parallel workflows for high-severity threats
4. **As a system**, I need to coordinate agent execution order and dependencies
5. **As a system**, I need to manage agent context sharing and state synchronization
6. **As a system**, I need to handle workflow errors with retry and fallback logic
7. **As a system**, I need to implement graceful degradation during service outages

#### Acceptance Criteria Summary
- Orchestrate workflows with <30 second latency
- Handle parallel execution for CRITICAL/HIGH threats
- Maintain workflow state consistency across failures
- Provide workflow visibility and debugging capabilities

### Unit 5: Dashboard and API Service

#### Mapped Functional Requirements
- **FR6.1**: Real-time threats map visualization
- **FR6.2**: Incident timeline display
- **FR6.3**: Investigation workspace interface
- **FR6.4**: Agent chat interface for interaction

#### Development Stories (Derived from Requirements)
1. **As a security analyst**, I need a real-time threat map showing current threats
2. **As a security analyst**, I need an incident timeline showing threat progression
3. **As a security analyst**, I need an investigation workspace for threat analysis
4. **As a security analyst**, I need to chat with AI agents for additional investigation
5. **As a security analyst**, I need to authenticate and access the dashboard securely
6. **As an external system**, I need REST APIs for integration with JIRA, Slack, PagerDuty
7. **As a security analyst**, I need real-time notifications of critical threats
8. **As a security analyst**, I need to export investigation reports and evidence

#### Acceptance Criteria Summary
- Display real-time threat data with <10 second latency
- Provide intuitive investigation workspace interface
- Support multi-user collaboration and role-based access
- Integrate with external systems for incident management

### Unit 6: Shared Infrastructure Service

#### Mapped Functional Requirements
- **FR5.1**: Incidents table with incident lifecycle management
- **FR5.2**: ThreatIntel table with TTL management
- **FR5.3**: AnalystFeedback table for model retraining
- **NFR3**: Security requirements (IAM, audit trail, encryption)
- **NFR4**: Reliability requirements (error handling, monitoring, backup)

#### Development Stories (Derived from Requirements)
1. **As a system**, I need to manage incident lifecycle and status tracking
2. **As a system**, I need to store threat intelligence with TTL management
3. **As a system**, I need to collect analyst feedback for model improvement
4. **As a system**, I need comprehensive monitoring and alerting
5. **As a system**, I need configuration management with validation and rollback
6. **As a system**, I need audit trails for all system interactions
7. **As a system**, I need cost tracking and optimization monitoring
8. **As a system**, I need backup and recovery procedures

#### Acceptance Criteria Summary
- Maintain 99.9% system availability
- Provide comprehensive audit trails for compliance
- Track and optimize costs to ~$0.75/day target
- Enable rapid deployment and rollback capabilities

## Cross-Unit Story Dependencies

### Sequential Dependencies
```
Unit 1 Stories → Unit 2 Stories → Unit 3 Stories → Unit 4 Stories → Unit 5 Stories
(Data must flow through processing pipeline)
```

### Parallel Development Opportunities
```
Unit 1 (Ingestion) ∥ Unit 6 (Infrastructure) - Can develop simultaneously
Unit 2 (Detection) ∥ Unit 3 (AI Agents) - Can develop with mocked interfaces
Unit 4 (Orchestration) ∥ Unit 5 (Dashboard) - Can develop with test workflows
```

### Integration Story Points
1. **Unit 1 → Unit 2 Integration**: S3 event processing and OpenSearch indexing
2. **Unit 2 → Unit 3 Integration**: DynamoDB anomaly records and agent triggers
3. **Unit 3 → Unit 4 Integration**: Agent coordination and workflow state management
4. **Unit 4 → Unit 5 Integration**: Real-time workflow updates and dashboard display
5. **All Units → Unit 6 Integration**: State management, monitoring, and configuration

## Development Priority Matrix

### Phase 1: Foundation (Weeks 1-2)
- **Unit 6**: Core infrastructure and monitoring
- **Unit 1**: Basic log ingestion without enrichment

### Phase 2: Detection Pipeline (Weeks 3-4)
- **Unit 1**: Complete enrichment capabilities
- **Unit 2**: Statistical detection algorithms

### Phase 3: Intelligence Layer (Weeks 5-6)
- **Unit 2**: ML model integration
- **Unit 3**: Basic agent implementations

### Phase 4: Orchestration (Weeks 7-8)
- **Unit 3**: Complete agent tool implementations
- **Unit 4**: Workflow orchestration and coordination

### Phase 5: Interface (Weeks 9-10)
- **Unit 5**: Dashboard and API development
- **Integration**: End-to-end system testing

### Phase 6: Optimization (Weeks 11-12)
- **Cost optimization**: Funnel effectiveness validation
- **Performance tuning**: Latency and throughput optimization
- **Security hardening**: Penetration testing and compliance

## Story Estimation Guidelines

### Small Stories (1-2 days)
- Individual detection algorithms
- Basic API endpoints
- Simple agent tools
- Configuration management features

### Medium Stories (3-5 days)
- Complex enrichment logic
- ML model training and deployment
- Agent prompt engineering and testing
- Dashboard component development

### Large Stories (1-2 weeks)
- End-to-end workflow implementation
- Real-time processing pipeline
- Complete agent implementations
- Integration testing and validation

### Epic Stories (2-4 weeks)
- Complete unit implementation
- Cross-unit integration
- Performance optimization
- Security and compliance implementation

## Quality Gates by Unit

### Unit 1: Data Ingestion Service
- Process 100M+ logs/day without data loss
- Achieve target filtering rates (99% benign traffic)
- Maintain enrichment SLA (<30 seconds)
- Pass data quality validation tests

### Unit 2: Anomaly Detection Service
- Achieve <5% false positive rate for all detection types
- Process anomalies within 5-minute SLA
- Demonstrate ML model accuracy improvements
- Validate cost funnel effectiveness

### Unit 3: AI Agent Service
- Generate explainable reasoning for all classifications
- Achieve target accuracy for threat classification
- Demonstrate tool functionality for all agent types
- Validate cost optimization (token usage)

### Unit 4: Workflow Orchestration Service
- Orchestrate workflows within latency SLA
- Handle failure scenarios with graceful degradation
- Maintain workflow state consistency
- Demonstrate parallel execution capabilities

### Unit 5: Dashboard and API Service
- Display real-time data within 10-second latency
- Support concurrent user sessions
- Integrate successfully with external systems
- Pass security and authentication testing

### Unit 6: Shared Infrastructure Service
- Maintain 99.9% availability SLA
- Provide complete audit trails
- Achieve cost optimization targets
- Support rapid deployment and rollback