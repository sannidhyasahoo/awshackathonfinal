# Component Methods - VPC Flow Log Anomaly Detection System

## Data Ingestion Layer Methods

### VPCFlowLogIngestionComponent
```python
class VPCFlowLogIngestionComponent:
    def process_kinesis_records(self, event: KinesisEvent) -> ProcessingResult
    def validate_flow_log_format(self, record: FlowLogRecord) -> ValidationResult
    def route_to_enrichment(self, validated_records: List[FlowLogRecord]) -> None
    def handle_processing_errors(self, error: ProcessingError) -> ErrorResponse
```

### LogEnrichmentComponent
```python
class LogEnrichmentComponent:
    def enrich_with_geo_ip(self, ip_address: str) -> GeoIPInfo
    def enrich_with_ec2_metadata(self, instance_id: str) -> EC2Metadata
    def perform_dns_lookup(self, ip_address: str) -> DNSInfo
    def filter_benign_traffic(self, record: FlowLogRecord) -> bool
    def apply_sampling_rules(self, records: List[FlowLogRecord]) -> List[FlowLogRecord]
```

### DataStorageComponent
```python
class DataStorageComponent:
    def store_to_s3_parquet(self, records: List[EnrichedFlowLog]) -> S3Location
    def index_to_opensearch(self, records: List[EnrichedFlowLog]) -> IndexResult
    def manage_data_lifecycle(self, retention_policy: RetentionPolicy) -> None
    def query_historical_data(self, query: SearchQuery) -> QueryResult
```

## Anomaly Detection Layer Methods

### StatisticalDetectionComponent
```python
class StatisticalDetectionComponent:
    def detect_port_scanning(self, source_ip: str, time_window: int) -> PortScanAnomaly
    def detect_ddos_patterns(self, destination_ip: str, packet_rate: float) -> DDoSAnomaly
    def detect_c2_beaconing(self, connection_intervals: List[float]) -> BeaconingAnomaly
    def detect_crypto_mining(self, destination_ip: str, port: int) -> CryptoMiningAnomaly
    def detect_tor_usage(self, destination_ip: str) -> TorUsageAnomaly
    def calculate_coefficient_variation(self, intervals: List[float]) -> float
```

### MLDetectionComponent
```python
class MLDetectionComponent:
    def train_isolation_forest(self, training_data: DataFrame) -> IsolationForestModel
    def detect_anomalies_isolation_forest(self, data: DataFrame) -> List[Anomaly]
    def train_lstm_baseline(self, historical_data: DataFrame) -> LSTMModel
    def detect_baseline_deviations(self, current_data: DataFrame) -> List[Anomaly]
    def update_behavioral_baseline(self, new_data: DataFrame) -> BaselineUpdate
    def evaluate_model_performance(self, predictions: List[Prediction]) -> ModelMetrics
```

### AnomalyAggregationComponent
```python
class AnomalyAggregationComponent:
    def aggregate_detection_results(self, statistical: List[Anomaly], ml: List[Anomaly]) -> List[AggregatedAnomaly]
    def add_enriched_context(self, anomaly: Anomaly) -> EnrichedAnomaly
    def filter_duplicate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]
    def store_anomaly_for_agents(self, anomaly: EnrichedAnomaly) -> DynamoDBResult
    def calculate_anomaly_score(self, anomaly: Anomaly) -> float
```

## AI Agent Layer Methods

### ThreatClassifierAgent
```python
class ThreatClassifierAgent:
    def classify_threat(self, anomaly_summary: AnomalySummary) -> ThreatClassification
    def determine_severity_level(self, threat_indicators: List[Indicator]) -> SeverityLevel
    def identify_mitre_techniques(self, threat_pattern: ThreatPattern) -> List[MITRETechnique]
    def generate_reasoning(self, analysis_context: AnalysisContext) -> ReasoningReport
    def recommend_actions(self, threat_classification: ThreatClassification) -> List[RecommendedAction]
    def calculate_confidence_score(self, evidence: List[Evidence]) -> float
```

### InvestigationAgent
```python
class InvestigationAgent:
    def build_attack_timeline(self, incident_data: IncidentData) -> AttackTimeline
    def identify_entry_vector(self, initial_indicators: List[Indicator]) -> EntryVector
    def map_lateral_movement(self, network_activity: NetworkActivity) -> LateralMovementMap
    def assess_data_risk(self, affected_resources: List[Resource]) -> DataRiskAssessment
    def find_persistence_mechanisms(self, system_changes: List[SystemChange]) -> List[PersistenceMechanism]
    def generate_investigation_report(self, findings: InvestigationFindings) -> InvestigationReport
```

### ResponseOrchestrationAgent
```python
class ResponseOrchestrationAgent:
    def determine_response_actions(self, threat_severity: SeverityLevel) -> List[ResponseAction]
    def execute_isolation_response(self, instance_id: str) -> IsolationResult
    def execute_credential_revocation(self, credentials: List[Credential]) -> RevocationResult
    def execute_alerting_response(self, alert_config: AlertConfig) -> AlertResult
    def request_human_approval(self, action: DestructiveAction) -> ApprovalRequest
    def coordinate_incident_response(self, incident: Incident) -> ResponseCoordination
```

### ThreatIntelligenceAgent
```python
class ThreatIntelligenceAgent:
    def fetch_threat_feeds(self, sources: List[ThreatSource]) -> List[ThreatIndicator]
    def update_threat_database(self, indicators: List[ThreatIndicator]) -> UpdateResult
    def enrich_with_threat_context(self, ioc: IOC) -> ThreatContext
    def update_knowledge_base(self, new_intelligence: ThreatIntelligence) -> KBUpdateResult
    def query_threat_reputation(self, indicator: str) -> ReputationScore
    def manage_indicator_ttl(self, indicators: List[ThreatIndicator]) -> TTLManagementResult
```

### RootCauseAnalysisAgent
```python
class RootCauseAnalysisAgent:
    def analyze_incident_root_cause(self, resolved_incident: ResolvedIncident) -> RootCauseAnalysis
    def identify_contributing_factors(self, incident_context: IncidentContext) -> List[ContributingFactor]
    def assess_control_failures(self, security_controls: List[SecurityControl]) -> List[ControlFailure]
    def generate_prevention_recommendations(self, root_cause: RootCause) -> List[PreventionRecommendation]
    def estimate_implementation_effort(self, recommendations: List[Recommendation]) -> List[EffortEstimate]
    def prioritize_recommendations(self, recommendations: List[Recommendation]) -> PrioritizedRecommendations
```

## Orchestration Layer Methods

### WorkflowOrchestrationComponent
```python
class WorkflowOrchestrationComponent:
    def start_detection_workflow(self, anomaly: Anomaly) -> WorkflowExecution
    def route_by_threat_severity(self, classification: ThreatClassification) -> RoutingDecision
    def execute_parallel_agents(self, high_severity_threat: Threat) -> ParallelExecution
    def execute_sequential_workflow(self, standard_threat: Threat) -> SequentialExecution
    def handle_workflow_errors(self, error: WorkflowError) -> ErrorHandling
    def manage_workflow_state(self, execution_id: str) -> WorkflowState
```

### AgentCoordinationComponent
```python
class AgentCoordinationComponent:
    def coordinate_agent_execution(self, agents: List[Agent], context: ExecutionContext) -> CoordinationResult
    def manage_agent_context_sharing(self, shared_context: SharedContext) -> ContextSharingResult
    def handle_agent_dependencies(self, dependency_graph: DependencyGraph) -> DependencyResolution
    def manage_agent_tool_access(self, agent: Agent, tools: List[Tool]) -> ToolAccessResult
    def aggregate_agent_results(self, agent_results: List[AgentResult]) -> AggregatedResult
```

## Interface Layer Methods

### AnalystDashboardComponent
```python
class AnalystDashboardComponent:
    def render_threat_map(self, threats: List[Threat]) -> ThreatMapVisualization
    def display_incident_timeline(self, incidents: List[Incident]) -> TimelineVisualization
    def provide_investigation_workspace(self, incident: Incident) -> InvestigationWorkspace
    def handle_agent_chat_interface(self, user_query: str) -> ChatResponse
    def authenticate_analyst(self, credentials: UserCredentials) -> AuthenticationResult
    def authorize_dashboard_access(self, user: User, resource: Resource) -> AuthorizationResult
```

### APIGatewayComponent
```python
class APIGatewayComponent:
    def handle_rest_api_request(self, request: APIRequest) -> APIResponse
    def handle_websocket_connection(self, connection: WebSocketConnection) -> ConnectionResult
    def authenticate_api_request(self, request: APIRequest) -> AuthenticationResult
    def apply_rate_limiting(self, client_id: str, request_count: int) -> RateLimitResult
    def route_to_backend_service(self, request: APIRequest) -> RoutingResult
```

## Cross-Cutting Methods

### StateManagementComponent
```python
class StateManagementComponent:
    def create_incident_record(self, incident: Incident) -> IncidentRecord
    def update_incident_status(self, incident_id: str, status: IncidentStatus) -> UpdateResult
    def store_threat_intelligence(self, threat_intel: ThreatIntelligence, ttl: int) -> StorageResult
    def retrieve_analyst_feedback(self, incident_id: str) -> AnalystFeedback
    def manage_data_consistency(self, operations: List[DataOperation]) -> ConsistencyResult
```

### MonitoringComponent
```python
class MonitoringComponent:
    def collect_system_metrics(self, metric_sources: List[MetricSource]) -> MetricCollection
    def track_cost_optimization(self, funnel_metrics: FunnelMetrics) -> CostTrackingResult
    def generate_system_alerts(self, alert_conditions: List[AlertCondition]) -> List[Alert]
    def create_operational_dashboard(self, dashboard_config: DashboardConfig) -> Dashboard
    def analyze_performance_trends(self, historical_metrics: List[Metric]) -> TrendAnalysis
```

### ConfigurationComponent
```python
class ConfigurationComponent:
    def load_environment_config(self, environment: Environment) -> Configuration
    def validate_configuration(self, config: Configuration) -> ValidationResult
    def update_runtime_parameters(self, parameters: Dict[str, Any]) -> UpdateResult
    def manage_feature_flags(self, flags: List[FeatureFlag]) -> FeatureFlagResult
    def handle_configuration_rollback(self, rollback_target: ConfigVersion) -> RollbackResult
```

## Agent Tool Methods (Lambda Proxy Pattern)

### Agent Tool Interface Methods
```python
class AgentToolInterface:
    def get_resource_baseline(self, resource_id: str) -> ResourceBaseline
    def check_threat_intel(self, indicator: str) -> ThreatIntelResult
    def get_recent_cloudtrail(self, resource: str, timerange: TimeRange) -> CloudTrailEvents
    def query_flow_logs_history(self, ip: str, hours: int) -> FlowLogHistory
    def get_iam_permissions(self, role: str) -> IAMPermissions
    def check_vulnerabilities(self, instance: str) -> VulnerabilityReport
    def query_guardduty(self, resource: str) -> GuardDutyFindings
    def get_network_topology(self, vpc: str) -> NetworkTopology
    def isolate_instance(self, instance_id: str) -> IsolationResult
    def snapshot_for_forensics(self, instance_id: str) -> SnapshotResult
    def revoke_credentials(self, role: str) -> RevocationResult
    def block_ip_at_waf(self, ip: str) -> WAFBlockResult
    def notify_team(self, severity: str, message: str) -> NotificationResult
    def create_incident_ticket(self, details: IncidentDetails) -> TicketResult
```