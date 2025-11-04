"""
AI Agent Service CDK Stack
Infrastructure as Code for Bedrock agents and supporting services
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_bedrock as bedrock,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_opensearchserverless as opensearch,
    aws_iam as iam,
    aws_s3 as s3,
    aws_kms as kms,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_apigateway as apigateway,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    CfnOutput
)
from constructs import Construct

class AIAgentServiceStack(Stack):
    """CDK Stack for AI Agent Service infrastructure"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create KMS keys for encryption
        self.context_key = self._create_context_encryption_key()
        self.agent_key = self._create_agent_encryption_key()

        # Create DynamoDB tables
        self.context_table = self._create_context_table()
        self.threat_intel_table = self._create_threat_intel_table()

        # Create S3 buckets
        self.agent_artifacts_bucket = self._create_agent_artifacts_bucket()
        self.knowledge_base_bucket = self._create_knowledge_base_bucket()

        # Create OpenSearch collection for knowledge base
        self.knowledge_base_collection = self._create_opensearch_collection()

        # Create Lambda functions for agent tools
        self.lambda_functions = self._create_lambda_functions()

        # Create Bedrock agents
        self.agents = self._create_bedrock_agents()

        # Create API Gateway
        self.api_gateway = self._create_api_gateway()

        # Create Step Functions for orchestration
        self.orchestration_state_machine = self._create_orchestration_workflow()

        # Create monitoring and logging
        self._create_monitoring_resources()

    def _create_context_encryption_key(self) -> kms.Key:
        """Create KMS key for context data encryption"""
        return kms.Key(
            self, "ContextEncryptionKey",
            description="KMS key for AI agent context data encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_agent_encryption_key(self) -> kms.Key:
        """Create KMS key for agent data encryption"""
        return kms.Key(
            self, "AgentEncryptionKey",
            description="KMS key for AI agent service encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_context_table(self) -> dynamodb.Table:
        """Create DynamoDB table for hierarchical context management"""
        table = dynamodb.Table(
            self, "AIAgentContextTable",
            table_name="ai-agent-context",
            partition_key=dynamodb.Attribute(
                name="context_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.ON_DEMAND,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.context_key,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Add GSIs for hierarchical queries
        table.add_global_secondary_index(
            index_name="level-timestamp-index",
            partition_key=dynamodb.Attribute(name="level", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING)
        )

        table.add_global_secondary_index(
            index_name="investigation-id-index",
            partition_key=dynamodb.Attribute(name="investigation_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING)
        )

        table.add_global_secondary_index(
            index_name="agent-id-index",
            partition_key=dynamodb.Attribute(name="agent_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING)
        )

        return table

    def _create_threat_intel_table(self) -> dynamodb.Table:
        """Create DynamoDB table for threat intelligence data"""
        return dynamodb.Table(
            self, "ThreatIntelTable",
            table_name="threat-intelligence",
            partition_key=dynamodb.Attribute(
                name="ioc_value",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="ioc_type",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.ON_DEMAND,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.context_key,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_agent_artifacts_bucket(self) -> s3.Bucket:
        """Create S3 bucket for agent artifacts and configurations"""
        return s3.Bucket(
            self, "AgentArtifactsBucket",
            bucket_name=f"ai-agent-artifacts-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.agent_key,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="agent-artifacts-lifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_knowledge_base_bucket(self) -> s3.Bucket:
        """Create S3 bucket for knowledge base documents"""
        return s3.Bucket(
            self, "KnowledgeBaseBucket",
            bucket_name=f"ai-agent-knowledge-base-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.agent_key,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_opensearch_collection(self) -> opensearch.CfnCollection:
        """Create OpenSearch Serverless collection for knowledge base"""
        
        # Create security policy
        security_policy = opensearch.CfnSecurityPolicy(
            self, "KnowledgeBaseSecurityPolicy",
            name="ai-agent-kb-security-policy",
            type="encryption",
            policy=f"""{{
                "Rules": [{{
                    "ResourceType": "collection",
                    "Resource": ["collection/ai-agent-knowledge-base"]
                }}],
                "AWSOwnedKey": true
            }}"""
        )

        # Create network policy
        network_policy = opensearch.CfnSecurityPolicy(
            self, "KnowledgeBaseNetworkPolicy",
            name="ai-agent-kb-network-policy",
            type="network",
            policy=f"""[{{
                "Rules": [{{
                    "ResourceType": "collection",
                    "Resource": ["collection/ai-agent-knowledge-base"]
                }}, {{
                    "ResourceType": "dashboard",
                    "Resource": ["collection/ai-agent-knowledge-base"]
                }}],
                "AllowFromPublic": true
            }}]"""
        )

        # Create collection
        collection = opensearch.CfnCollection(
            self, "KnowledgeBaseCollection",
            name="ai-agent-knowledge-base",
            description="Knowledge base for AI agents with MITRE ATT&CK and threat intelligence",
            type="VECTORSEARCH"
        )

        collection.add_dependency(security_policy)
        collection.add_dependency(network_policy)

        return collection

    def _create_lambda_functions(self) -> dict:
        """Create Lambda functions for agent tools"""
        
        # Common Lambda execution role
        lambda_role = iam.Role(
            self, "AgentToolsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ]
        )

        # Grant permissions to access DynamoDB tables
        self.context_table.grant_read_write_data(lambda_role)
        self.threat_intel_table.grant_read_data(lambda_role)

        # Grant permissions to access S3 buckets
        self.agent_artifacts_bucket.grant_read(lambda_role)
        self.knowledge_base_bucket.grant_read(lambda_role)

        # Grant KMS permissions
        self.context_key.grant_encrypt_decrypt(lambda_role)
        self.agent_key.grant_decrypt(lambda_role)

        functions = {}

        # Threat Classifier Data Access Function
        functions['threat_classifier_data_access'] = lambda_.Function(
            self, "ThreatClassifierDataAccess",
            function_name="threat-classifier-data-access",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="threat_classifier_data_access.lambda_handler",
            code=lambda_.Code.from_asset("../code/tools/data-access"),
            role=lambda_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "CONTEXT_TABLE_NAME": self.context_table.table_name,
                "THREAT_INTEL_TABLE_NAME": self.threat_intel_table.table_name,
                "OPENSEARCH_ENDPOINT": self.knowledge_base_collection.attr_collection_endpoint
            }
        )

        # Investigation Forensic Tools Function
        functions['investigation_forensic_tools'] = lambda_.Function(
            self, "InvestigationForensicTools",
            function_name="investigation-forensic-tools",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="investigation_forensic_tools.lambda_handler",
            code=lambda_.Code.from_asset("../code/tools/forensic"),
            role=lambda_role,
            timeout=Duration.minutes(5),
            memory_size=2048,
            environment={
                "CONTEXT_TABLE_NAME": self.context_table.table_name
            }
        )

        # Response Containment Tools Function
        functions['response_containment_tools'] = lambda_.Function(
            self, "ResponseContainmentTools",
            function_name="response-containment-tools",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="response_containment_tools.lambda_handler",
            code=lambda_.Code.from_asset("../code/tools/containment"),
            role=lambda_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "CONTEXT_TABLE_NAME": self.context_table.table_name
            }
        )

        return functions

    def _create_bedrock_agents(self) -> dict:
        """Create Bedrock agents with action groups"""
        
        # Create IAM role for Bedrock agents
        agent_role = iam.Role(
            self, "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "BedrockAgentPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream"
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[func.function_arn for func in self.lambda_functions.values()]
                        )
                    ]
                )
            }
        )

        agents = {}

        # Threat Classifier Agent
        agents['threat_classifier'] = bedrock.CfnAgent(
            self, "ThreatClassifierAgent",
            agent_name="ThreatClassifierAgent",
            description="AI-powered threat classification with severity assessment",
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction="""You are an expert cybersecurity analyst specializing in network threat classification. 
            Analyze network anomalies and provide accurate threat assessments with severity levels, 
            confidence scores, and MITRE ATT&CK mappings.""",
            agent_resource_role_arn=agent_role.role_arn,
            idle_session_ttl_in_seconds=1800,
            action_groups=[
                bedrock.CfnAgent.AgentActionGroupProperty(
                    action_group_name="DataAccessTools",
                    description="Tools for accessing threat data and baselines",
                    action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                        lambda_=self.lambda_functions['threat_classifier_data_access'].function_arn
                    ),
                    function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
                        functions=[
                            bedrock.CfnAgent.FunctionProperty(
                                name="get_resource_baseline",
                                description="Get baseline behavior patterns for a resource"
                            ),
                            bedrock.CfnAgent.FunctionProperty(
                                name="check_threat_intel",
                                description="Check indicators against threat intelligence"
                            )
                        ]
                    )
                )
            ]
        )

        return agents

    def _create_api_gateway(self) -> apigateway.RestApi:
        """Create API Gateway for agent management"""
        
        api = apigateway.RestApi(
            self, "AIAgentServiceAPI",
            rest_api_name="ai-agent-service-api",
            description="API for AI Agent Service management and monitoring",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )

        # Create resources and methods
        agents_resource = api.root.add_resource("agents")
        agents_resource.add_method("GET")  # List agents
        agents_resource.add_method("POST")  # Trigger agent

        investigations_resource = api.root.add_resource("investigations")
        investigation_resource = investigations_resource.add_resource("{id}")
        investigation_resource.add_method("GET")  # Get investigation
        investigation_resource.add_method("PUT")  # Update investigation

        return api

    def _create_orchestration_workflow(self) -> sfn.StateMachine:
        """Create Step Functions workflow for agent orchestration"""
        
        # Define workflow steps
        classify_threat = tasks.BedrockInvokeModel(
            self, "ClassifyThreat",
            model=tasks.BedrockModel.from_string("anthropic.claude-3-5-sonnet-20241022-v2:0"),
            body=sfn.TaskInput.from_object({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": sfn.JsonPath.string_at("$.anomaly_data")
                    }
                ]
            }),
            result_path="$.classification_result"
        )

        # Create state machine
        definition = classify_threat

        return sfn.StateMachine(
            self, "AgentOrchestrationWorkflow",
            state_machine_name="ai-agent-orchestration",
            definition=definition,
            timeout=Duration.minutes(30)
        )

    def _create_monitoring_resources(self):
        """Create CloudWatch monitoring resources"""
        
        # Create log groups
        logs.LogGroup(
            self, "AgentServiceLogGroup",
            log_group_name="/aws/lambda/ai-agent-service",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create EventBridge rule for scheduled cleanup
        cleanup_rule = events.Rule(
            self, "ContextCleanupRule",
            schedule=events.Schedule.cron(hour="2", minute="0"),
            description="Daily cleanup of expired context entries"
        )

        # Add outputs
        CfnOutput(
            self, "ContextTableName",
            value=self.context_table.table_name,
            description="DynamoDB table name for agent context"
        )

        CfnOutput(
            self, "APIGatewayURL",
            value=self.api_gateway.url,
            description="API Gateway URL for agent service"
        )

        CfnOutput(
            self, "KnowledgeBaseEndpoint",
            value=self.knowledge_base_collection.attr_collection_endpoint,
            description="OpenSearch collection endpoint for knowledge base"
        )