# Infrastructure Design - AI Agent Service

## AWS Infrastructure Architecture Overview

Based on infrastructure design decisions, the AI Agent Service implements a **fully managed AWS-native architecture** with hybrid storage, comprehensive monitoring, and multi-region disaster recovery.

### Core Infrastructure Principles

1. **Managed Bedrock Platform**: Fully managed AI agents with AWS-native integration
2. **Hybrid Storage Strategy**: Combine DynamoDB for real-time context with S3 for historical data
3. **AWS Native Security**: Comprehensive security using IAM, KMS, VPC, and AWS security services
4. **CloudWatch Native Monitoring**: Complete observability using AWS native monitoring tools
5. **Multi-Region Active-Passive DR**: Primary region with warm standby for 99.9% availability

## AI Platform Infrastructure

### Amazon Bedrock Agent Platform
**Managed AI Agent Infrastructure**:
```
Bedrock Agent Configuration:
├── Agent Runtime: Fully managed by AWS
├── Model Access: Claude 3.5 Sonnet/Haiku, Titan Embeddings
├── Agent Aliases: Version management and canary deployment
├── Action Groups: Lambda function integration for tools
└── Knowledge Bases: OpenSearch integration for threat intelligence

Agent Deployment Model:
- ThreatClassifierAgent: us-east-1 (primary), us-west-2 (DR)
- InvestigationAgent: us-east-1 (primary), us-west-2 (DR)
- ResponseOrchestrationAgent: us-east-1 (primary), us-west-2 (DR)
- ThreatIntelligenceAgent: us-east-1 (primary), us-west-2 (DR)
- RootCauseAnalysisAgent: us-east-1 (primary), us-west-2 (DR)
```

### Lambda Tool Infrastructure
**Serverless Compute for Agent Tools**:
```yaml
Lambda Configuration:
  Runtime: Python 3.11
  Architecture: arm64 (Graviton2 for cost optimization)
  Memory: 1GB-3GB based on tool complexity
  Timeout: 5 minutes maximum
  Reserved Concurrency: Per tool type
  VPC Configuration: Private subnets with VPC endpoints

Tool Categories and Scaling:
├── Data Access Tools (DynamoDB, S3, OpenSearch)
│   ├── Memory: 1GB
│   ├── Reserved Concurrency: 50
│   └── Timeout: 2 minutes
├── External API Tools (Threat Intelligence)
│   ├── Memory: 2GB
│   ├── Reserved Concurrency: 20
│   └── Timeout: 3 minutes
├── AWS Service Tools (EC2, VPC, IAM)
│   ├── Memory: 1.5GB
│   ├── Reserved Concurrency: 30
│   └── Timeout: 4 minutes
└── Notification Tools (SNS, EventBridge)
    ├── Memory: 1GB
    ├── Reserved Concurrency: 100
    └── Timeout: 1 minute
```

### Agent Coordination Infrastructure
**Step Functions for Workflow Orchestration**:
```json
{
  "StateMachine": {
    "Type": "EXPRESS",
    "LoggingConfiguration": {
      "Level": "ALL",
      "IncludeExecutionData": true,
      "Destinations": ["CloudWatch Logs"]
    },
    "TracingConfiguration": {
      "Enabled": true
    }
  },
  "Workflows": {
    "ThreatAnalysisPipeline": "Sequential agent execution",
    "ParallelClassification": "Concurrent agent processing",
    "EmergencyResponse": "Priority workflow for CRITICAL threats",
    "BatchProcessing": "Cost-optimized batch workflows"
  }
}
```

## Data and Context Infrastructure

### Hybrid Context Storage Architecture
**Primary Storage - Amazon DynamoDB**:
```yaml
Context Tables:
  GlobalContextTable:
    PartitionKey: "context_type"
    SortKey: "timestamp"
    TTL: "7 days"
    Capacity: "On-demand with auto-scaling"
    GlobalSecondaryIndexes:
      - "threat_type-timestamp-index"
      - "severity-timestamp-index"
    
  InvestigationContextTable:
    PartitionKey: "investigation_id"
    SortKey: "context_level#timestamp"
    TTL: "30 days"
    Capacity: "Provisioned with auto-scaling"
    LocalSecondaryIndexes:
      - "agent_id-timestamp-index"
    
  AgentContextTable:
    PartitionKey: "agent_id"
    SortKey: "session_id#timestamp"
    TTL: "24 hours"
    Capacity: "On-demand"
    StreamSpecification:
      StreamViewType: "NEW_AND_OLD_IMAGES"
```

**Historical Storage - Amazon S3**:
```yaml
S3 Bucket Configuration:
  ContextArchiveBucket:
    StorageClass: "Intelligent Tiering"
    Lifecycle:
      - Transition to IA after 30 days
      - Transition to Glacier after 90 days
      - Transition to Deep Archive after 365 days
    Versioning: "Enabled"
    Encryption: "SSE-KMS with customer managed keys"
    
  InvestigationEvidenceBucket:
    StorageClass: "Standard"
    Lifecycle:
      - Transition to IA after 7 days
      - Transition to Glacier after 30 days
    CrossRegionReplication: "us-west-2"
    ObjectLock: "Governance mode, 7 years retention"
```

### Multi-Level Caching Infrastructure
**Level 1: Local Caching (Lambda)**:
```python
# In-memory caching within Lambda functions
import functools
from datetime import datetime, timedelta

@functools.lru_cache(maxsize=100)
def cache_ai_response(input_hash, ttl_minutes=5):
    # Local Lambda memory caching
    pass
```

**Level 2: Distributed Caching (ElastiCache)**:
```yaml
ElastiCache Configuration:
  RedisCluster:
    NodeType: "r6g.large"
    NumCacheNodes: 3
    Engine: "Redis 7.0"
    MultiAZ: true
    AutomaticFailover: true
    BackupRetentionPeriod: 5
    SnapshotWindow: "03:00-05:00"
    MaintenanceWindow: "sun:05:00-sun:07:00"
    
  CacheSubnetGroup:
    Subnets: ["private-subnet-1a", "private-subnet-1b", "private-subnet-1c"]
    
  SecurityGroup:
    InboundRules:
      - Port: 6379
        Source: "Lambda security group"
        Protocol: "TCP"
```

**Level 3: Persistent Caching (DynamoDB DAX)**:
```yaml
DAX Configuration:
  ClusterName: "ai-agent-context-cache"
  NodeType: "dax.r4.large"
  ReplicationFactor: 3
  SubnetGroup: "private-subnets"
  SecurityGroup: "dax-security-group"
  ParameterGroup: "default.dax1.0"
  MaintenanceWindow: "sun:05:00-sun:06:00"
```

### Knowledge Base Infrastructure
**Amazon OpenSearch Service**:
```yaml
OpenSearch Configuration:
  DomainName: "ai-agent-knowledge-base"
  EngineVersion: "OpenSearch_2.3"
  ClusterConfig:
    InstanceType: "r6g.large.search"
    InstanceCount: 3
    DedicatedMasterEnabled: true
    MasterInstanceType: "r6g.medium.search"
    MasterInstanceCount: 3
  
  EBSOptions:
    EBSEnabled: true
    VolumeType: "gp3"
    VolumeSize: 100
    IOPS: 3000
  
  VPCOptions:
    SecurityGroupIds: ["opensearch-sg"]
    SubnetIds: ["private-subnet-1a", "private-subnet-1b", "private-subnet-1c"]
  
  EncryptionAtRestOptions:
    Enabled: true
    KmsKeyId: "alias/opensearch-key"
  
  NodeToNodeEncryptionOptions:
    Enabled: true
  
  DomainEndpointOptions:
    EnforceHTTPS: true
    TLSSecurityPolicy: "Policy-Min-TLS-1-2-2019-07"
```

## Security and Network Infrastructure

### AWS Native Security Architecture
**Identity and Access Management**:
```yaml
IAM Roles:
  BedrockAgentExecutionRole:
    AssumeRolePolicyDocument:
      Service: "bedrock.amazonaws.com"
    ManagedPolicyArns:
      - "arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentServiceRolePolicy"
    InlinePolicies:
      - "LambdaInvokePolicy"
      - "DynamoDBAccessPolicy"
      - "S3AccessPolicy"
  
  LambdaToolExecutionRole:
    AssumeRolePolicyDocument:
      Service: "lambda.amazonaws.com"
    ManagedPolicyArns:
      - "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
    InlinePolicies:
      - "BedrockInvokePolicy"
      - "DynamoDBCRUDPolicy"
      - "S3ReadWritePolicy"
      - "OpenSearchAccessPolicy"
```

**Encryption Infrastructure**:
```yaml
KMS Key Configuration:
  AgentContextKey:
    Description: "AI Agent context data encryption"
    KeyUsage: "ENCRYPT_DECRYPT"
    KeySpec: "SYMMETRIC_DEFAULT"
    KeyRotationStatus: "Enabled"
    KeyPolicy:
      - "Allow Bedrock agents to use key"
      - "Allow Lambda functions to use key"
      - "Allow DynamoDB to use key"
  
  InvestigationDataKey:
    Description: "Investigation evidence encryption"
    KeyUsage: "ENCRYPT_DECRYPT"
    KeySpec: "SYMMETRIC_DEFAULT"
    KeyRotationStatus: "Enabled"
    MultiRegion: true
```

**Network Security**:
```yaml
VPC Configuration:
  CIDR: "10.0.0.0/16"
  
  Subnets:
    PrivateSubnets:
      - "10.0.1.0/24" (us-east-1a)
      - "10.0.2.0/24" (us-east-1b)
      - "10.0.3.0/24" (us-east-1c)
    PublicSubnets:
      - "10.0.101.0/24" (us-east-1a)
      - "10.0.102.0/24" (us-east-1b)
      - "10.0.103.0/24" (us-east-1c)
  
  SecurityGroups:
    BedrockAgentSG:
      InboundRules: []
      OutboundRules:
        - "HTTPS to Lambda functions"
        - "HTTPS to AWS services via VPC endpoints"
    
    LambdaToolSG:
      InboundRules:
        - "HTTPS from Bedrock agents"
      OutboundRules:
        - "HTTPS to AWS services"
        - "Redis to ElastiCache"
        - "HTTPS to OpenSearch"
  
  VPCEndpoints:
    - "com.amazonaws.us-east-1.bedrock-runtime"
    - "com.amazonaws.us-east-1.dynamodb"
    - "com.amazonaws.us-east-1.s3"
    - "com.amazonaws.us-east-1.kms"
    - "com.amazonaws.us-east-1.logs"
    - "com.amazonaws.us-east-1.monitoring"
```

## Monitoring and Observability Infrastructure

### CloudWatch Native Monitoring
**Metrics and Dashboards**:
```yaml
CloudWatch Configuration:
  CustomMetrics:
    - "AI.Agent.ResponseTime"
    - "AI.Agent.TokenConsumption"
    - "AI.Agent.ErrorRate"
    - "AI.Agent.ThreatDetectionRate"
    - "AI.Context.CacheHitRate"
    - "AI.Investigation.CompletionRate"
  
  Dashboards:
    - "AI Agent Performance Dashboard"
    - "Cost and Token Usage Dashboard"
    - "Security and Compliance Dashboard"
    - "Infrastructure Health Dashboard"
  
  Alarms:
    CriticalAlarms:
      - "Agent response time > 30s for CRITICAL threats"
      - "Token budget > 90% consumed"
      - "Agent error rate > 5%"
      - "Context store unavailable"
    
    WarningAlarms:
      - "Agent response time > SLA threshold"
      - "Cache hit rate < 70%"
      - "Investigation completion rate < 95%"
      - "Token consumption trending high"
```

**Distributed Tracing**:
```yaml
X-Ray Configuration:
  TracingConfig:
    Mode: "Active"
    SamplingRate: 0.1
  
  ServiceMap:
    - "Bedrock Agents"
    - "Lambda Tools"
    - "DynamoDB Context Store"
    - "ElastiCache"
    - "OpenSearch Knowledge Base"
    - "Step Functions Workflows"
  
  TraceSegments:
    - "Agent invocation and response"
    - "Context retrieval and storage"
    - "Cache operations"
    - "Knowledge base queries"
    - "External API calls"
```

**Log Management**:
```yaml
CloudWatch Logs:
  LogGroups:
    - "/aws/bedrock/agents/threat-classifier"
    - "/aws/bedrock/agents/investigation"
    - "/aws/bedrock/agents/response-orchestration"
    - "/aws/bedrock/agents/threat-intelligence"
    - "/aws/bedrock/agents/root-cause-analysis"
    - "/aws/lambda/agent-tools"
    - "/aws/stepfunctions/agent-workflows"
  
  LogRetention: 30 days (operational), 7 years (audit)
  LogEncryption: "KMS encrypted"
  
  LogInsights:
    - "Agent performance analysis queries"
    - "Error pattern detection queries"
    - "Cost analysis queries"
    - "Security audit queries"
```

## Integration and Messaging Infrastructure

### Event-Driven Architecture
**Amazon EventBridge**:
```yaml
EventBridge Configuration:
  CustomEventBus: "ai-agent-events"
  
  EventRules:
    ThreatClassificationComplete:
      EventPattern:
        source: ["ai-agent-service"]
        detail-type: ["Threat Classification Complete"]
      Targets:
        - "InvestigationAgent Lambda"
        - "Audit Trail DynamoDB"
    
    InvestigationComplete:
      EventPattern:
        source: ["ai-agent-service"]
        detail-type: ["Investigation Complete"]
      Targets:
        - "ResponseOrchestrationAgent Lambda"
        - "Dashboard WebSocket API"
    
    EmergencyThreatDetected:
      EventPattern:
        source: ["ai-agent-service"]
        detail-type: ["Emergency Threat Detected"]
      Targets:
        - "SNS Emergency Topic"
        - "Step Functions Emergency Workflow"
```

### API Gateway Infrastructure
**Amazon API Gateway**:
```yaml
API Gateway Configuration:
  RestAPI:
    Name: "ai-agent-service-api"
    EndpointType: "REGIONAL"
    
    Resources:
      /agents:
        GET: "List agent status"
        POST: "Trigger agent execution"
      /investigations/{id}:
        GET: "Get investigation details"
        PUT: "Update investigation"
      /threats:
        GET: "Query threat classifications"
        POST: "Submit threat for analysis"
    
    Authentication:
      Type: "AWS_IAM"
      AuthorizationType: "AWS_IAM"
    
    Throttling:
      BurstLimit: 1000
      RateLimit: 500
  
  WebSocketAPI:
    Name: "ai-agent-realtime-api"
    RouteSelectionExpression: "$request.body.action"
    
    Routes:
      $connect: "Connection handler Lambda"
      $disconnect: "Disconnection handler Lambda"
      subscribe: "Subscription handler Lambda"
      unsubscribe: "Unsubscription handler Lambda"
```

## Disaster Recovery Infrastructure

### Multi-Region Active-Passive Architecture
**Primary Region (us-east-1)**:
```yaml
Primary Infrastructure:
  Bedrock Agents: "Active deployment"
  DynamoDB Tables: "Active with cross-region replication"
  ElastiCache: "Active cluster"
  OpenSearch: "Active domain"
  Lambda Functions: "Active deployment"
  S3 Buckets: "Active with cross-region replication"
```

**Secondary Region (us-west-2)**:
```yaml
Disaster Recovery Infrastructure:
  Bedrock Agents: "Warm standby (pre-deployed, inactive)"
  DynamoDB Tables: "Global tables with eventual consistency"
  ElastiCache: "Standby cluster (stopped, ready to start)"
  OpenSearch: "Cross-cluster replication"
  Lambda Functions: "Deployed but not receiving traffic"
  S3 Buckets: "Cross-region replication destination"
  
  Failover Automation:
    Route53 Health Checks: "Monitor primary region health"
    Lambda Failover Function: "Automated failover orchestration"
    CloudFormation StackSets: "Infrastructure consistency"
    
  RTO Target: "15 minutes"
  RPO Target: "5 minutes"
```

This comprehensive infrastructure design provides a robust, scalable, and secure foundation for the AI Agent Service with full AWS-native integration and multi-region disaster recovery capabilities.