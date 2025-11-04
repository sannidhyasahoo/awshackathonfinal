# VPC Flow Log Anomaly Detection System - Requirements

## Intent Analysis Summary
- **User Request**: Build a multi-agent security system for VPC Flow Log threat detection
- **Request Type**: New Project (Greenfield)
- **Scope Estimate**: System-wide (Multi-service architecture)
- **Complexity Estimate**: Complex (Real-time processing, AI agents, ML models)

## Functional Requirements

### FR1: Data Ingestion Pipeline
- **FR1.1**: Ingest VPC Flow Logs via Kinesis Data Streams
- **FR1.2**: Enrich logs with geo-IP, resource metadata (EC2 tags, security groups), DNS lookups
- **FR1.3**: Filter out health checks, AWS service endpoints, sample benign traffic at 1%
- **FR1.4**: Store processed data in S3 (Parquet format) and OpenSearch

### FR2: Real-Time Anomaly Detection (Pre-LLM Layer)
- **FR2.1**: Port Scanning Detection - Source connecting to >20 unique ports in 60s
- **FR2.2**: DDoS Detection - High packet rate to single destination (SYN floods, UDP floods)
- **FR2.3**: C2 Beaconing Detection - Regular periodic connections (coefficient of variation <10%)
- **FR2.4**: Crypto Mining Detection - Connections to mining pool IPs, ports 3333/4444/9999
- **FR2.5**: Tor Usage Detection - Match against Tor exit node list (updated hourly)
- **FR2.6**: ML-based Behavioral Analysis - Isolation Forest and LSTM for baseline deviations
- **FR2.7**: Output anomalies to DynamoDB with enriched context (NOT raw logs)

### FR3: Bedrock Agent System (5 Agents)

#### FR3.1: Threat Classifier Agent
- **Model**: Claude 3.5 Sonnet
- **Input**: Pre-filtered anomaly summary with context
- **Output**: Classification decision (is_threat, severity, confidence, threat_type, mitre_attack_techniques, reasoning, recommended_actions)
- **Tools**: get_resource_baseline(), check_threat_intel(), get_recent_cloudtrail()

#### FR3.2: Investigation Agent
- **Trigger**: CRITICAL/HIGH severity threats
- **Model**: Claude 3.5 Sonnet
- **Output**: Investigation report with attack timeline, entry vector, lateral movement, data risk assessment
- **Tools**: query_cloudtrail(), query_flow_logs_history(), get_iam_permissions(), check_vulnerabilities(), query_guardduty(), get_network_topology()

#### FR3.3: Response Orchestration Agent
- **Model**: Claude 3.5 Haiku (faster decisions)
- **Actions**: Automated response based on severity (isolation, credential revocation, alerting)
- **Human-in-the-loop**: Require approval for destructive production actions
- **Tools**: isolate_instance(), snapshot_for_forensics(), revoke_credentials(), block_ip_at_waf(), notify_team(), create_incident_ticket()

#### FR3.4: Threat Intelligence Enrichment Agent
- **Function**: Fetch threat feeds hourly from AlienVault OTX, AbuseIPDB, Tor exit nodes, mining pools
- **Storage**: DynamoDB with TTL
- **Knowledge Base**: Index MITRE ATT&CK + historical incidents in OpenSearch with Bedrock embeddings

#### FR3.5: Root Cause Analysis Agent
- **Trigger**: Post-incident analysis
- **Output**: Root cause, contributing factors, preventive recommendations with effort estimates
- **Analysis**: Security groups, patch status, IAM policies, monitoring gaps

### FR4: Orchestration Workflow (Step Functions)
- **FR4.1**: State machine: DetectAnomaly → EnrichThreatIntel → ClassifyThreat
- **FR4.2**: Branch logic: FALSE POSITIVE → LogAndUpdateModel
- **FR4.3**: Branch logic: CRITICAL/HIGH → Parallel{Investigation + Containment + Notify} → RootCauseAnalysis
- **FR4.4**: Branch logic: MEDIUM/LOW → QueueForAnalystReview

### FR5: State Management (DynamoDB)
- **FR5.1**: Incidents table: incident_id (PK), timestamp (SK), anomaly_type, classification, investigation_status, agent_findings, containment_actions
- **FR5.2**: ThreatIntel table: ioc_value (PK), ioc_type, threat_category, confidence, source, ttl
- **FR5.3**: AnalystFeedback table: incident_id (PK), agent_verdict, analyst_verdict, reason (for retraining)

### FR6: Analyst Dashboard (React)
- **FR6.1**: Real-time threats map visualization
- **FR6.2**: Incident timeline display
- **FR6.3**: Investigation workspace interface
- **FR6.4**: Agent chat interface for interaction

## Non-Functional Requirements

### NFR1: Performance Requirements
- **NFR1.1**: Handle 100M+ flow logs per day efficiently
- **NFR1.2**: Detection time < 5 minutes from log ingestion
- **NFR1.3**: False positive rate < 5%
- **NFR1.4**: System availability 99.9%

### NFR2: Cost Optimization
- **NFR2.1**: Funnel approach: 100M flows/day → 10K anomalies → 1K threats → 500K tokens → 250K tokens (caching)
- **NFR2.2**: Target cost: ~$0.75/day vs $60K/day naive approach
- **NFR2.3**: Use Claude Haiku for simple classification, Sonnet for complex investigation
- **NFR2.4**: Cache system prompts and threat intel context
- **NFR2.5**: Batch low-priority analysis
- **NFR2.6**: CRITICAL: Never send raw flow logs to Bedrock

### NFR3: Security Requirements
- **NFR3.1**: IAM roles with least privilege principles
- **NFR3.2**: Audit trail for all agent interactions
- **NFR3.3**: Secure storage of threat intelligence data
- **NFR3.4**: Encrypted data in transit and at rest

### NFR4: Reliability Requirements
- **NFR4.1**: Proper error handling and retries for all components
- **NFR4.2**: Graceful degradation when services are unavailable
- **NFR4.3**: Monitoring and alerting for system health
- **NFR4.4**: Backup and recovery procedures

### NFR5: Explainability Requirements
- **NFR5.1**: All agent reasoning must be explained in outputs
- **NFR5.2**: Decision audit trail for compliance
- **NFR5.3**: Human-readable investigation reports

## Technical Stack Requirements

### TSR1: Core Technologies
- **Programming Language**: Python 3.12
- **AWS SDK**: boto3
- **Infrastructure**: AWS CDK for Infrastructure-as-Code

### TSR2: AI/ML Services
- **Bedrock Models**: Claude 3.5 Sonnet/Haiku, Titan Embeddings
- **ML Platform**: SageMaker with scikit-learn, TensorFlow
- **Knowledge Base**: OpenSearch Serverless for RAG

### TSR3: Data Processing
- **Streaming**: Kinesis Data Streams, Kinesis Data Analytics (Flink 1.15)
- **Storage**: S3 (Parquet), DynamoDB, OpenSearch
- **Analytics**: Athena for historical queries

### TSR4: Orchestration & Monitoring
- **Workflow**: Step Functions for orchestration
- **Scheduling**: EventBridge rules
- **Monitoring**: CloudWatch dashboards and alarms
- **Notifications**: SNS, Slack, PagerDuty integration

## Deliverables Requirements

### DR1: Infrastructure-as-Code
- Kinesis streams + Firehose + Data Analytics applications
- Lambda functions for enrichment, tool implementations, threat feed updates
- SageMaker training jobs and endpoints
- Bedrock Agents with action groups and knowledge bases
- Step Functions state machines
- DynamoDB tables with GSIs
- OpenSearch indexes
- IAM roles and policies
- EventBridge rules
- CloudWatch resources

### DR2: Documentation & Operations
- Deployment automation scripts
- System monitoring setup
- Cost control mechanisms
- Operational runbooks
- API documentation
- User guides for analyst dashboard

## Acceptance Criteria

### AC1: System Performance
- Successfully process 100M+ flow logs daily without data loss
- Achieve <5 minute detection time for all threat types
- Maintain <5% false positive rate across all detection algorithms
- Demonstrate cost efficiency within $1/day operational target

### AC2: Threat Detection Capabilities
- Accurately detect all 5 specified threat types (port scanning, DDoS, C2 beaconing, crypto mining, Tor usage)
- Generate actionable investigation reports for CRITICAL/HIGH threats
- Execute appropriate automated responses based on threat severity
- Provide explainable AI reasoning for all classifications

### AC3: Operational Readiness
- Complete Infrastructure-as-Code deployment
- Functional analyst dashboard with all specified features
- Comprehensive monitoring and alerting
- Documented incident response procedures