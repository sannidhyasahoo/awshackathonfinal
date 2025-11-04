# Deployment Architecture - Anomaly Detection Service

## Deployment Strategy Overview

Multi-environment deployment with canary releases for ML models, blue-green deployment for infrastructure updates, and automated CI/CD pipeline integration.

## Environment Architecture

### Production Environment
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Production Environment                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   us-east-1     │    │   us-west-2     │    │   eu-west-1     │              │
│  │   (Primary)     │    │   (DR)          │    │   (Regional)    │              │
│  │                 │    │                 │    │                 │              │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │              │
│  │ │ ECS Fargate │ │    │ │ ECS Fargate │ │    │ │ ECS Fargate │ │              │
│  │ │ - 2-10 Tasks│ │    │ │ - 1-5 Tasks │ │    │ │ - 1-3 Tasks │ │              │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │              │
│  │                 │    │                 │    │                 │              │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │              │
│  │ │ SageMaker   │ │    │ │ SageMaker   │ │    │ │ SageMaker   │ │              │
│  │ │ - Primary   │ │    │ │ - Standby   │ │    │ │ - Regional  │ │              │
│  │ │ - Canary    │ │    │ │ - Backup    │ │    │ │ - Local     │ │              │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Development and Staging Environments
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Development & Staging Pipeline                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │  Development    │    │    Staging      │    │   Production    │              │
│  │                 │    │                 │    │                 │              │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │              │
│  │ │ ECS Fargate │ │    │ │ ECS Fargate │ │    │ │ ECS Fargate │ │              │
│  │ │ - 1 Task    │ │    │ │ - 2 Tasks   │ │    │ │ - 2-10 Tasks│ │              │
│  │ │ - Spot Inst │ │    │ │ - On-Demand │ │    │ │ - Mixed     │ │              │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │              │
│  │                 │    │                 │    │                 │              │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │              │
│  │ │ SageMaker   │ │    │ │ SageMaker   │ │    │ │ SageMaker   │ │              │
│  │ │ - Dev Models│ │    │ │ - Test      │ │    │ │ - Prod      │ │              │
│  │ │ - Synthetic │ │    │ │ - Validation│ │    │ │ - Canary    │ │              │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│           │                       │                       │                      │
│           └───────────────────────┼───────────────────────┘                      │
│                                   │                                              │
│                          Automated CI/CD Pipeline                               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## CI/CD Pipeline Architecture

### CodePipeline Configuration
```yaml
# Main Deployment Pipeline
AnomalyDetectionPipeline:
  Type: AWS::CodePipeline::Pipeline
  Properties:
    PipelineName: anomaly-detection-deployment
    RoleArn: !GetAtt CodePipelineRole.Arn
    ArtifactStore:
      Type: S3
      Location: !Ref PipelineArtifactsBucket
    Stages:
      - Name: Source
        Actions:
          - Name: SourceAction
            ActionTypeId:
              Category: Source
              Owner: AWS
              Provider: CodeCommit
              Version: 1
            Configuration:
              RepositoryName: anomaly-detection-service
              BranchName: main
            OutputArtifacts:
              - Name: SourceOutput

      - Name: Build
        Actions:
          - Name: BuildAction
            ActionTypeId:
              Category: Build
              Owner: AWS
              Provider: CodeBuild
              Version: 1
            Configuration:
              ProjectName: !Ref AnomalyDetectionBuildProject
            InputArtifacts:
              - Name: SourceOutput
            OutputArtifacts:
              - Name: BuildOutput

      - Name: DeployDev
        Actions:
          - Name: DeployToDevAction
            ActionTypeId:
              Category: Deploy
              Owner: AWS
              Provider: CloudFormation
              Version: 1
            Configuration:
              ActionMode: CREATE_UPDATE
              StackName: anomaly-detection-dev
              TemplatePath: BuildOutput::infrastructure/dev-template.yaml
              Capabilities: CAPABILITY_IAM
              RoleArn: !GetAtt CloudFormationRole.Arn
            InputArtifacts:
              - Name: BuildOutput

      - Name: TestDev
        Actions:
          - Name: IntegrationTestAction
            ActionTypeId:
              Category: Test
              Owner: AWS
              Provider: CodeBuild
              Version: 1
            Configuration:
              ProjectName: !Ref IntegrationTestProject
            InputArtifacts:
              - Name: BuildOutput

      - Name: DeployStaging
        Actions:
          - Name: DeployToStagingAction
            ActionTypeId:
              Category: Deploy
              Owner: AWS
              Provider: CloudFormation
              Version: 1
            Configuration:
              ActionMode: CREATE_UPDATE
              StackName: anomaly-detection-staging
              TemplatePath: BuildOutput::infrastructure/staging-template.yaml
              Capabilities: CAPABILITY_IAM
              RoleArn: !GetAtt CloudFormationRole.Arn
            InputArtifacts:
              - Name: BuildOutput

      - Name: ApprovalGate
        Actions:
          - Name: ManualApproval
            ActionTypeId:
              Category: Approval
              Owner: AWS
              Provider: Manual
              Version: 1
            Configuration:
              CustomData: "Please review staging deployment and approve for production"

      - Name: DeployProduction
        Actions:
          - Name: DeployToProdAction
            ActionTypeId:
              Category: Deploy
              Owner: AWS
              Provider: CloudFormation
              Version: 1
            Configuration:
              ActionMode: CREATE_UPDATE
              StackName: anomaly-detection-prod
              TemplatePath: BuildOutput::infrastructure/prod-template.yaml
              Capabilities: CAPABILITY_IAM
              RoleArn: !GetAtt CloudFormationRole.Arn
            InputArtifacts:
              - Name: BuildOutput
```

### CodeBuild Projects
```yaml
# Main Build Project
AnomalyDetectionBuildProject:
  Type: AWS::CodeBuild::Project
  Properties:
    Name: anomaly-detection-build
    ServiceRole: !GetAtt CodeBuildRole.Arn
    Artifacts:
      Type: CODEPIPELINE
    Environment:
      Type: LINUX_CONTAINER
      ComputeType: BUILD_GENERAL1_MEDIUM
      Image: aws/codebuild/amazonlinux2-x86_64-standard:3.0
      PrivilegedMode: true
    Source:
      Type: CODEPIPELINE
      BuildSpec: |
        version: 0.2
        phases:
          pre_build:
            commands:
              - echo Logging in to Amazon ECR...
              - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
          build:
            commands:
              - echo Build started on `date`
              - echo Building the Docker image...
              - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
              - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
              - echo Running unit tests...
              - python -m pytest tests/unit/
              - echo Building ML models...
              - python scripts/build_models.py
          post_build:
            commands:
              - echo Build completed on `date`
              - echo Pushing the Docker image...
              - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
        artifacts:
          files:
            - '**/*'

# Integration Test Project
IntegrationTestProject:
  Type: AWS::CodeBuild::Project
  Properties:
    Name: anomaly-detection-integration-tests
    ServiceRole: !GetAtt CodeBuildRole.Arn
    Artifacts:
      Type: CODEPIPELINE
    Environment:
      Type: LINUX_CONTAINER
      ComputeType: BUILD_GENERAL1_SMALL
      Image: aws/codebuild/amazonlinux2-x86_64-standard:3.0
    Source:
      Type: CODEPIPELINE
      BuildSpec: |
        version: 0.2
        phases:
          pre_build:
            commands:
              - echo Installing test dependencies...
              - pip install -r requirements-test.txt
          build:
            commands:
              - echo Running integration tests...
              - python -m pytest tests/integration/ -v
              - echo Running performance tests...
              - python tests/performance/load_test.py
              - echo Running security tests...
              - python tests/security/security_test.py
          post_build:
            commands:
              - echo Integration tests completed
```

## ML Model Deployment Strategy

### Canary Deployment for ML Models
```python
# SageMaker Model Deployment with Canary Strategy
import boto3
from sagemaker import Model
from sagemaker.predictor import Predictor

class CanaryModelDeployment:
    def __init__(self):
        self.sagemaker_client = boto3.client('sagemaker')
        self.cloudwatch = boto3.client('cloudwatch')
        
    def deploy_canary_model(self, model_name, new_model_uri, endpoint_name):
        """Deploy new model version with canary strategy"""
        
        # Create new model
        new_model = Model(
            image_uri=self.get_inference_image_uri(),
            model_data=new_model_uri,
            role=self.get_execution_role(),
            name=f"{model_name}-{self.get_timestamp()}"
        )
        
        # Update endpoint configuration with traffic splitting
        endpoint_config = {
            'EndpointConfigName': f"{endpoint_name}-config-{self.get_timestamp()}",
            'ProductionVariants': [
                {
                    'VariantName': 'primary',
                    'ModelName': self.get_current_model_name(endpoint_name),
                    'InitialInstanceCount': 2,
                    'InstanceType': 'ml.m5.large',
                    'InitialVariantWeight': 90  # 90% traffic to current model
                },
                {
                    'VariantName': 'canary',
                    'ModelName': new_model.name,
                    'InitialInstanceCount': 1,
                    'InstanceType': 'ml.m5.large',
                    'InitialVariantWeight': 10  # 10% traffic to new model
                }
            ]
        }
        
        # Create endpoint configuration
        self.sagemaker_client.create_endpoint_config(**endpoint_config)
        
        # Update endpoint
        self.sagemaker_client.update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config['EndpointConfigName']
        )
        
        # Monitor canary performance
        self.monitor_canary_performance(endpoint_name, 'canary')
        
    def monitor_canary_performance(self, endpoint_name, variant_name):
        """Monitor canary model performance and auto-promote or rollback"""
        
        # Define success criteria
        success_criteria = {
            'error_rate_threshold': 0.05,  # 5% error rate
            'latency_threshold': 500,      # 500ms latency
            'monitoring_duration': 3600    # 1 hour monitoring
        }
        
        # Monitor metrics for specified duration
        start_time = time.time()
        while time.time() - start_time < success_criteria['monitoring_duration']:
            
            # Get canary metrics
            error_rate = self.get_variant_error_rate(endpoint_name, variant_name)
            latency = self.get_variant_latency(endpoint_name, variant_name)
            
            # Check success criteria
            if (error_rate > success_criteria['error_rate_threshold'] or 
                latency > success_criteria['latency_threshold']):
                
                # Rollback canary deployment
                self.rollback_canary(endpoint_name)
                return False
            
            time.sleep(300)  # Check every 5 minutes
        
        # Promote canary to full traffic
        self.promote_canary(endpoint_name, variant_name)
        return True
    
    def promote_canary(self, endpoint_name, variant_name):
        """Promote canary to receive 100% traffic"""
        
        # Update traffic distribution
        self.sagemaker_client.update_endpoint_weights_and_capacities(
            EndpointName=endpoint_name,
            DesiredWeightsAndCapacities=[
                {
                    'VariantName': 'primary',
                    'DesiredWeight': 0
                },
                {
                    'VariantName': variant_name,
                    'DesiredWeight': 100
                }
            ]
        )
        
        # Clean up old model after successful promotion
        self.cleanup_old_model(endpoint_name, 'primary')
```

## Infrastructure as Code Templates

### Environment-Specific Templates

#### Development Environment Template
```yaml
# dev-template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Anomaly Detection Service - Development Environment'

Parameters:
  Environment:
    Type: String
    Default: dev
    Description: Environment name

Resources:
  # Minimal resources for development
  DevProcessingCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub "${Environment}-anomaly-detection"
      CapacityProviders:
        - FARGATE_SPOT  # Cost optimization for dev
      
  DevProcessingService:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: !Sub "${Environment}-processing-service"
      Cluster: !Ref DevProcessingCluster
      TaskDefinition: !Ref DevTaskDefinition
      DesiredCount: 1  # Single instance for dev
      LaunchType: FARGATE
      
  # Development-specific configurations
  DevModelEndpoint:
    Type: AWS::SageMaker::Endpoint
    Properties:
      EndpointName: !Sub "${Environment}-isolation-forest"
      EndpointConfigName: !Ref DevEndpointConfig
      
  DevEndpointConfig:
    Type: AWS::SageMaker::EndpointConfig
    Properties:
      EndpointConfigName: !Sub "${Environment}-config"
      ProductionVariants:
        - ModelName: !Ref DevModel
          VariantName: primary
          InitialInstanceCount: 1
          InstanceType: ml.t3.medium  # Smaller instance for dev
          InitialVariantWeight: 100
```

#### Production Environment Template
```yaml
# prod-template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Anomaly Detection Service - Production Environment'

Parameters:
  Environment:
    Type: String
    Default: prod
    Description: Environment name

Resources:
  # Production-grade resources
  ProdProcessingCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub "${Environment}-anomaly-detection"
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT
      DefaultCapacityProviderStrategy:
        - CapacityProvider: FARGATE
          Weight: 70
        - CapacityProvider: FARGATE_SPOT
          Weight: 30
          
  ProdProcessingService:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: !Sub "${Environment}-processing-service"
      Cluster: !Ref ProdProcessingCluster
      TaskDefinition: !Ref ProdTaskDefinition
      DesiredCount: 2  # Multiple instances for HA
      LaunchType: FARGATE
      
  # Production auto-scaling
  ProdAutoScaling:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      ServiceNamespace: ecs
      ResourceId: !Sub "service/${ProdProcessingCluster}/${ProdProcessingService}"
      ScalableDimension: ecs:service:DesiredCount
      MinCapacity: 2
      MaxCapacity: 10
      
  # Production ML endpoints with canary support
  ProdModelEndpoint:
    Type: AWS::SageMaker::Endpoint
    Properties:
      EndpointName: !Sub "${Environment}-isolation-forest"
      EndpointConfigName: !Ref ProdEndpointConfig
      
  ProdEndpointConfig:
    Type: AWS::SageMaker::EndpointConfig
    Properties:
      EndpointConfigName: !Sub "${Environment}-config"
      ProductionVariants:
        - ModelName: !Ref ProdModel
          VariantName: primary
          InitialInstanceCount: 2
          InstanceType: ml.m5.large
          InitialVariantWeight: 100
```

## Deployment Automation Scripts

### Deployment Orchestration
```python
# deploy.py - Deployment orchestration script
import boto3
import json
import time
from typing import Dict, List

class AnomalyDetectionDeployer:
    def __init__(self, environment: str):
        self.environment = environment
        self.cloudformation = boto3.client('cloudformation')
        self.ecs = boto3.client('ecs')
        self.sagemaker = boto3.client('sagemaker')
        
    def deploy_infrastructure(self, template_path: str, parameters: Dict):
        """Deploy infrastructure using CloudFormation"""
        
        stack_name = f"anomaly-detection-{self.environment}"
        
        with open(template_path, 'r') as template_file:
            template_body = template_file.read()
        
        # Convert parameters to CloudFormation format
        cf_parameters = [
            {'ParameterKey': k, 'ParameterValue': v}
            for k, v in parameters.items()
        ]
        
        try:
            # Check if stack exists
            self.cloudformation.describe_stacks(StackName=stack_name)
            
            # Update existing stack
            response = self.cloudformation.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=cf_parameters,
                Capabilities=['CAPABILITY_IAM']
            )
            
        except self.cloudformation.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                # Create new stack
                response = self.cloudformation.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=cf_parameters,
                    Capabilities=['CAPABILITY_IAM']
                )
            else:
                raise e
        
        # Wait for stack operation to complete
        self.wait_for_stack_operation(stack_name)
        
        return response
    
    def deploy_application(self, image_uri: str):
        """Deploy application containers"""
        
        cluster_name = f"{self.environment}-anomaly-detection"
        service_name = f"{self.environment}-processing-service"
        
        # Update task definition with new image
        task_definition = self.update_task_definition(image_uri)
        
        # Update ECS service
        self.ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            taskDefinition=task_definition['taskDefinitionArn']
        )
        
        # Wait for deployment to complete
        self.wait_for_service_deployment(cluster_name, service_name)
    
    def deploy_ml_models(self, model_artifacts: Dict):
        """Deploy ML models with canary strategy"""
        
        for model_type, artifact_uri in model_artifacts.items():
            endpoint_name = f"{self.environment}-{model_type}"
            
            if self.environment == 'prod':
                # Use canary deployment for production
                self.deploy_canary_model(model_type, artifact_uri, endpoint_name)
            else:
                # Direct deployment for non-production
                self.deploy_model_direct(model_type, artifact_uri, endpoint_name)
    
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks after deployment"""
        
        health_checks = [
            self.check_ecs_service_health(),
            self.check_sagemaker_endpoints(),
            self.check_api_gateway_health(),
            self.check_database_connectivity(),
            self.run_integration_tests()
        ]
        
        return all(health_checks)
    
    def rollback_deployment(self):
        """Rollback to previous deployment if health checks fail"""
        
        # Get previous task definition
        previous_task_def = self.get_previous_task_definition()
        
        # Rollback ECS service
        cluster_name = f"{self.environment}-anomaly-detection"
        service_name = f"{self.environment}-processing-service"
        
        self.ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            taskDefinition=previous_task_def
        )
        
        # Rollback ML models if needed
        self.rollback_ml_models()

# Main deployment script
if __name__ == "__main__":
    import sys
    
    environment = sys.argv[1]
    image_uri = sys.argv[2]
    
    deployer = AnomalyDetectionDeployer(environment)
    
    try:
        # Deploy infrastructure
        deployer.deploy_infrastructure(
            f"templates/{environment}-template.yaml",
            {"Environment": environment}
        )
        
        # Deploy application
        deployer.deploy_application(image_uri)
        
        # Run health checks
        if deployer.run_health_checks():
            print(f"Deployment to {environment} successful!")
        else:
            print(f"Health checks failed, rolling back...")
            deployer.rollback_deployment()
            sys.exit(1)
            
    except Exception as e:
        print(f"Deployment failed: {e}")
        deployer.rollback_deployment()
        sys.exit(1)
```