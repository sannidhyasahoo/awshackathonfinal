# Infrastructure Design - Anomaly Detection Service

## Infrastructure Architecture Overview

Based on hybrid approach combining containers for processing with functions for events, managed ML platform, hybrid storage, hybrid messaging, hybrid network, and AWS native observability.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud Infrastructure                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   Public Subnet │    │  Private Subnet │    │ Private Subnet  │              │
│  │   - API Gateway │    │ - ECS Fargate   │    │ - SageMaker     │              │
│  │   - ALB         │    │ - Processing    │    │ - ML Models     │              │
│  │   - WAF/Shield  │    │ - Correlation   │    │ - ElastiCache   │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│           │                       │                       │                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Event & Messaging Layer                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │ │
│  │  │EventBridge  │  │   Kinesis   │  │     SQS     │  │ Lambda Functions│   │ │
│  │  │- Anomaly    │  │- Log Stream │  │- Reliable   │  │- Event Handlers │   │ │
│  │  │  Events     │  │- Real-time  │  │  Messaging  │  │- Notifications  │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│           │                       │                       │                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   Storage Layer │    │ Security Layer  │    │ Monitoring      │              │
│  │   - S3 Models   │    │ - KMS Keys      │    │ - CloudWatch    │              │
│  │   - DynamoDB    │    │ - IAM Roles     │    │ - X-Ray Tracing │              │
│  │   - ElastiCache │    │ - VPC Security  │    │ - CloudTrail    │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Compute Infrastructure

### Hybrid Compute Platform

#### ECS Fargate for Processing Engine
```yaml
# ECS Cluster Configuration
AnomalyDetectionCluster:
  Type: AWS::ECS::Cluster
  Properties:
    ClusterName: anomaly-detection-cluster
    CapacityProviders:
      - FARGATE
      - FARGATE_SPOT
    DefaultCapacityProviderStrategy:
      - CapacityProvider: FARGATE
        Weight: 70
      - CapacityProvider: FARGATE_SPOT
        Weight: 30

# Processing Engine Service
ProcessingEngineService:
  Type: AWS::ECS::Service
  Properties:
    ServiceName: anomaly-processing-engine
    Cluster: !Ref AnomalyDetectionCluster
    TaskDefinition: !Ref ProcessingEngineTaskDefinition
    DesiredCount: 2
    LaunchType: FARGATE
    NetworkConfiguration:
      AwsvpcConfiguration:
        SecurityGroups:
          - !Ref ProcessingEngineSecurityGroup
        Subnets:
          - !Ref PrivateSubnet1
          - !Ref PrivateSubnet2
    ServiceRegistries:
      - RegistryArn: !GetAtt ProcessingEngineServiceDiscovery.Arn

# Auto Scaling Configuration
ProcessingEngineAutoScaling:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    ServiceNamespace: ecs
    ResourceId: !Sub "service/${AnomalyDetectionCluster}/${ProcessingEngineService}"
    ScalableDimension: ecs:service:DesiredCount
    MinCapacity: 2
    MaxCapacity: 10
    RoleARN: !GetAtt ECSAutoScalingRole.Arn

# Event-Driven Scaling Policy
QueueDepthScalingPolicy:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyName: queue-depth-scaling
    PolicyType: TargetTrackingScaling
    ScalingTargetId: !Ref ProcessingEngineAutoScaling
    TargetTrackingScalingPolicyConfiguration:
      TargetValue: 1000
      CustomMetricSpecification:
        MetricName: QueueDepth
        Namespace: AnomalyDetection/Processing
        Statistic: Average
```

#### Lambda Functions for Event Handling
```yaml
# Anomaly Event Handler
AnomalyEventHandler:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: anomaly-event-handler
    Runtime: python3.9
    Handler: handler.process_anomaly_event
    Code:
      ZipFile: |
        import json
        import boto3
        
        def process_anomaly_event(event, context):
            # Process anomaly detection events
            for record in event['Records']:
                anomaly_data = json.loads(record['body'])
                # Route to appropriate handlers
                route_anomaly_notification(anomaly_data)
            
            return {'statusCode': 200}
    Environment:
      Variables:
        SNS_TOPIC_ARN: !Ref AnomalyNotificationTopic
    ReservedConcurrencyLimit: 100

# Configuration Update Handler
ConfigUpdateHandler:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: config-update-handler
    Runtime: python3.9
    Handler: handler.update_detection_config
    Code:
      ZipFile: |
        import boto3
        
        def update_detection_config(event, context):
            # Handle dynamic configuration updates
            ssm = boto3.client('ssm')
            # Update detection thresholds
            return {'statusCode': 200}
```

## ML Infrastructure

### Amazon SageMaker Platform

#### Model Training Infrastructure
```yaml
# SageMaker Execution Role
SageMakerExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: AnomalyDetectionSageMakerRole
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: sagemaker.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
      - arn:aws:iam::aws:policy/AmazonS3FullAccess

# Model Registry
ModelRegistry:
  Type: AWS::SageMaker::ModelPackageGroup
  Properties:
    ModelPackageGroupName: anomaly-detection-models
    ModelPackageGroupDescription: ML models for anomaly detection

# Isolation Forest Model Endpoint
IsolationForestEndpoint:
  Type: AWS::SageMaker::Endpoint
  Properties:
    EndpointName: isolation-forest-endpoint
    EndpointConfigName: !Ref IsolationForestEndpointConfig

IsolationForestEndpointConfig:
  Type: AWS::SageMaker::EndpointConfig
  Properties:
    EndpointConfigName: isolation-forest-config
    ProductionVariants:
      - ModelName: !Ref IsolationForestModel
        VariantName: primary
        InitialInstanceCount: 2
        InstanceType: ml.m5.large
        InitialVariantWeight: 90
      - ModelName: !Ref IsolationForestModelCanary
        VariantName: canary
        InitialInstanceCount: 1
        InstanceType: ml.m5.large
        InitialVariantWeight: 10

# LSTM Model Endpoint
LSTMEndpoint:
  Type: AWS::SageMaker::Endpoint
  Properties:
    EndpointName: lstm-model-endpoint
    EndpointConfigName: !Ref LSTMEndpointConfig
```

#### Model Training Pipeline
```python
# SageMaker Pipeline for Model Training
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import TrainingStep, ProcessingStep

def create_training_pipeline():
    # Data preprocessing step
    preprocessing_step = ProcessingStep(
        name="PreprocessFlowLogs",
        processor=preprocessing_processor,
        inputs=[
            ProcessingInput(
                source=f"s3://{bucket}/raw-flow-logs/",
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="train_data",
                source="/opt/ml/processing/train"
            )
        ]
    )
    
    # Model training step
    training_step = TrainingStep(
        name="TrainIsolationForest",
        estimator=isolation_forest_estimator,
        inputs={
            "training": TrainingInput(
                s3_data=preprocessing_step.properties.ProcessingOutputConfig.Outputs["train_data"].S3Output.S3Uri
            )
        }
    )
    
    # Model evaluation step
    evaluation_step = ProcessingStep(
        name="EvaluateModel",
        processor=evaluation_processor,
        inputs=[
            ProcessingInput(
                source=training_step.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model"
            )
        ]
    )
    
    pipeline = Pipeline(
        name="anomaly-detection-training-pipeline",
        steps=[preprocessing_step, training_step, evaluation_step]
    )
    
    return pipeline
```

## Storage Infrastructure

### Hybrid Storage Architecture

#### S3 for Model and Data Storage
```yaml
# Model Artifacts Bucket
ModelArtifactsBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub "${AWS::StackName}-model-artifacts"
    VersioningConfiguration:
      Status: Enabled
    LifecycleConfiguration:
      Rules:
        - Id: ModelVersionLifecycle
          Status: Enabled
          Transitions:
            - TransitionInDays: 30
              StorageClass: STANDARD_IA
            - TransitionInDays: 90
              StorageClass: GLACIER
    PublicAccessBlockConfiguration:
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true

# Training Data Bucket
TrainingDataBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub "${AWS::StackName}-training-data"
    LifecycleConfiguration:
      Rules:
        - Id: TrainingDataLifecycle
          Status: Enabled
          Transitions:
            - TransitionInDays: 7
              StorageClass: STANDARD_IA
            - TransitionInDays: 30
              StorageClass: GLACIER
```

#### DynamoDB for Metadata and Configuration
```yaml
# Anomaly Detection Metadata
AnomalyMetadataTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: anomaly-detection-metadata
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: anomaly_id
        AttributeType: S
      - AttributeName: detection_timestamp
        AttributeType: S
    KeySchema:
      - AttributeName: anomaly_id
        KeyType: HASH
      - AttributeName: detection_timestamp
        KeyType: RANGE
    GlobalSecondaryIndexes:
      - IndexName: timestamp-index
        KeySchema:
          - AttributeName: detection_timestamp
            KeyType: HASH
        Projection:
          ProjectionType: ALL
    StreamSpecification:
      StreamViewType: NEW_AND_OLD_IMAGES
    PointInTimeRecoverySpecification:
      PointInTimeRecoveryEnabled: true

# Model Configuration Table
ModelConfigurationTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: model-configuration
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: model_type
        AttributeType: S
      - AttributeName: version
        AttributeType: S
    KeySchema:
      - AttributeName: model_type
        KeyType: HASH
      - AttributeName: version
        KeyType: RANGE
```

#### ElastiCache for Correlation State
```yaml
# Redis Cluster for Correlation State
CorrelationStateCache:
  Type: AWS::ElastiCache::ReplicationGroup
  Properties:
    ReplicationGroupId: anomaly-correlation-cache
    ReplicationGroupDescription: Correlation state cache for anomaly detection
    Engine: redis
    CacheNodeType: cache.r6g.large
    NumCacheClusters: 3
    Port: 6379
    ParameterGroupName: default.redis7
    SecurityGroupIds:
      - !Ref CacheSecurityGroup
    SubnetGroupName: !Ref CacheSubnetGroup
    AtRestEncryptionEnabled: true
    TransitEncryptionEnabled: true
    AutomaticFailoverEnabled: true
    MultiAZEnabled: true
    SnapshotRetentionLimit: 7
    SnapshotWindow: "03:00-05:00"
    PreferredMaintenanceWindow: "sun:05:00-sun:07:00"

CacheSubnetGroup:
  Type: AWS::ElastiCache::SubnetGroup
  Properties:
    Description: Subnet group for correlation cache
    SubnetIds:
      - !Ref PrivateSubnet1
      - !Ref PrivateSubnet2
```

## Messaging Infrastructure

### Hybrid Messaging Architecture

#### EventBridge for Anomaly Events
```yaml
# Custom Event Bus
AnomalyEventBus:
  Type: AWS::Events::EventBus
  Properties:
    Name: anomaly-detection-events

# Anomaly Detection Rule
AnomalyDetectionRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: !Ref AnomalyEventBus
    EventPattern:
      source: ["anomaly-detection-service"]
      detail-type: ["Anomaly Detected"]
    Targets:
      - Arn: !GetAtt AnomalyNotificationTopic.TopicArn
        Id: "AnomalyNotificationTarget"
      - Arn: !GetAtt AnomalyEventHandler.Arn
        Id: "AnomalyProcessingTarget"
```

#### Kinesis for Real-time Streaming
```yaml
# Kinesis Data Stream
FlowLogStream:
  Type: AWS::Kinesis::Stream
  Properties:
    Name: vpc-flow-log-stream
    ShardCount: 5
    RetentionPeriodHours: 24
    StreamEncryption:
      EncryptionType: KMS
      KeyId: !Ref KinesisKMSKey

# Kinesis Analytics Application
AnomalyDetectionAnalytics:
  Type: AWS::KinesisAnalytics::Application
  Properties:
    ApplicationName: anomaly-detection-analytics
    ApplicationDescription: Real-time anomaly detection on flow logs
    Inputs:
      - NamePrefix: "flow_log_input"
        KinesisStreamsInput:
          ResourceARN: !GetAtt FlowLogStream.Arn
          RoleARN: !GetAtt KinesisAnalyticsRole.Arn
        InputSchema:
          RecordColumns:
            - Name: "timestamp"
              SqlType: "TIMESTAMP"
            - Name: "source_ip"
              SqlType: "VARCHAR(15)"
            - Name: "destination_ip"
              SqlType: "VARCHAR(15)"
```

#### SQS for Reliable Messaging
```yaml
# Processing Queue
ProcessingQueue:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: anomaly-processing-queue
    VisibilityTimeoutSeconds: 300
    MessageRetentionPeriod: 1209600  # 14 days
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt ProcessingDLQ.Arn
      maxReceiveCount: 3
    KmsMasterKeyId: !Ref SQSKMSKey

# Dead Letter Queue
ProcessingDLQ:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: anomaly-processing-dlq
    MessageRetentionPeriod: 1209600
```

## Network and Security Infrastructure

### Hybrid Network Architecture

#### VPC Configuration
```yaml
# Main VPC
AnomalyDetectionVPC:
  Type: AWS::EC2::VPC
  Properties:
    CidrBlock: 10.0.0.0/16
    EnableDnsHostnames: true
    EnableDnsSupport: true
    Tags:
      - Key: Name
        Value: AnomalyDetectionVPC

# Public Subnets for API Gateway
PublicSubnet1:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref AnomalyDetectionVPC
    CidrBlock: 10.0.1.0/24
    AvailabilityZone: !Select [0, !GetAZs '']
    MapPublicIpOnLaunch: true

PublicSubnet2:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref AnomalyDetectionVPC
    CidrBlock: 10.0.2.0/24
    AvailabilityZone: !Select [1, !GetAZs '']
    MapPublicIpOnLaunch: true

# Private Subnets for Processing
PrivateSubnet1:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref AnomalyDetectionVPC
    CidrBlock: 10.0.10.0/24
    AvailabilityZone: !Select [0, !GetAZs '']

PrivateSubnet2:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref AnomalyDetectionVPC
    CidrBlock: 10.0.11.0/24
    AvailabilityZone: !Select [1, !GetAZs '']
```

#### API Gateway and Load Balancer
```yaml
# Application Load Balancer
ApplicationLoadBalancer:
  Type: AWS::ElasticLoadBalancingV2::LoadBalancer
  Properties:
    Name: anomaly-detection-alb
    Type: application
    Scheme: internet-facing
    SecurityGroups:
      - !Ref ALBSecurityGroup
    Subnets:
      - !Ref PublicSubnet1
      - !Ref PublicSubnet2

# API Gateway
AnomalyDetectionAPI:
  Type: AWS::ApiGateway::RestApi
  Properties:
    Name: anomaly-detection-api
    Description: API for anomaly detection service
    EndpointConfiguration:
      Types:
        - REGIONAL
    Policy:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal: '*'
          Action: 'execute-api:Invoke'
          Resource: '*'
          Condition:
            IpAddress:
              'aws:SourceIp': 
                - '10.0.0.0/16'  # VPC CIDR
```

#### Security Groups
```yaml
# Processing Engine Security Group
ProcessingEngineSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Security group for processing engine
    VpcId: !Ref AnomalyDetectionVPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 8080
        ToPort: 8080
        SourceSecurityGroupId: !Ref ALBSecurityGroup
    SecurityGroupEgress:
      - IpProtocol: -1
        CidrIp: 0.0.0.0/0

# Cache Security Group
CacheSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Security group for ElastiCache
    VpcId: !Ref AnomalyDetectionVPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 6379
        ToPort: 6379
        SourceSecurityGroupId: !Ref ProcessingEngineSecurityGroup
```

## Monitoring Infrastructure

### AWS Native Observability

#### CloudWatch Configuration
```yaml
# Custom Metrics Dashboard
AnomalyDetectionDashboard:
  Type: AWS::CloudWatch::Dashboard
  Properties:
    DashboardName: AnomalyDetectionMetrics
    DashboardBody: !Sub |
      {
        "widgets": [
          {
            "type": "metric",
            "properties": {
              "metrics": [
                ["AnomalyDetection/Service", "ProcessingLatency"],
                ["AnomalyDetection/Service", "AnomaliesDetected"],
                ["AnomalyDetection/Service", "FalsePositiveRate"]
              ],
              "period": 300,
              "stat": "Average",
              "region": "${AWS::Region}",
              "title": "Anomaly Detection Performance"
            }
          }
        ]
      }

# SLA Breach Alarm
SLABreachAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: AnomalyDetection-SLA-Breach
    AlarmDescription: Alert when processing latency exceeds 5 minutes
    MetricName: ProcessingLatency
    Namespace: AnomalyDetection/Service
    Statistic: Average
    Period: 300
    EvaluationPeriods: 1
    Threshold: 300
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SLABreachTopic
```

#### X-Ray Tracing
```yaml
# X-Ray Tracing Configuration
XRayTracingConfig:
  Type: AWS::XRay::SamplingRule
  Properties:
    SamplingRule:
      RuleName: AnomalyDetectionTracing
      Priority: 9000
      FixedRate: 0.1
      ReservoirSize: 1
      ServiceName: anomaly-detection-service
      ServiceType: "*"
      Host: "*"
      HTTPMethod: "*"
      URLPath: "*"
      Version: 1
```