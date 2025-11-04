# Business Logic Model - AI Agent Service

## Agent Architecture Overview

Based on functional design decisions, the AI Agent Service implements a **hybrid agent orchestration** approach with 5 specialized Bedrock agents using adaptive processing patterns.

### Core Business Logic Principles

1. **Hybrid Agent Coordination**: Combine sequential, parallel, and conditional routing based on threat characteristics
2. **Adaptive Processing**: AI agents determine optimal processing depth and resource allocation
3. **Context-Aware Authorization**: Authorization requirements scale with threat severity and business impact
4. **Multi-Format Reasoning**: Provide structured data, natural language, and evidence citations for explainability
5. **Hierarchical Context Management**: Different context levels with appropriate agent access patterns

## Agent Business Logic Models

### 1. ThreatClassifierAgent Business Logic

**Purpose**: Initial threat assessment with hybrid classification approach

**Processing Model**:
```
Anomaly Input → Rule-Based Screening → AI-Driven Analysis → MITRE ATT&CK Mapping → Severity Assessment
```

**Decision Algorithm**:
1. **Rule-Based Initial Screening**:
   - Apply predefined threat patterns (port scanning, DDoS signatures)
   - Check against known bad IP lists and suspicious port combinations
   - Assign initial threat category and confidence score (0.0-1.0)

2. **AI-Driven Detailed Analysis** (if initial confidence < 0.8):
   - Use Claude 3.5 Sonnet for contextual threat assessment
   - Analyze flow patterns, timing, and behavioral indicators
   - Generate natural language reasoning for threat classification

3. **MITRE ATT&CK Mapping**:
   - Map detected threats to MITRE ATT&CK techniques
   - Assign tactic and technique IDs based on observed behaviors
   - Calculate technique confidence scores

4. **Severity Assessment**:
   - **CRITICAL**: Active exploitation, data exfiltration, or lateral movement
   - **HIGH**: Reconnaissance with exploitation attempts or privilege escalation
   - **MEDIUM**: Suspicious patterns requiring investigation
   - **LOW**: Anomalous but likely benign activity
   - **INFO**: Baseline deviations for awareness

**Output**: ThreatClassification entity with severity, MITRE mapping, and reasoning

### 2. InvestigationAgent Business Logic

**Purpose**: Deep threat investigation with adaptive depth strategy

**Processing Model**:
```
ThreatClassification → Depth Assessment → Investigation Workflow → Evidence Collection → Analysis Report
```

**Adaptive Depth Algorithm**:
1. **Initial Depth Assessment**:
   - **Minimal**: LOW severity threats - basic context lookup
   - **Standard**: MEDIUM severity - historical correlation and pattern analysis
   - **Comprehensive**: HIGH/CRITICAL - full investigation with external enrichment
   - **Adaptive**: AI agent determines optimal depth based on initial findings

2. **Investigation Workflow Patterns**:
   - **Timeline Analysis**: Reconstruct attack timeline from flow logs
   - **Lateral Movement Detection**: Identify related suspicious activities
   - **Asset Impact Assessment**: Determine affected systems and data
   - **Attribution Analysis**: Correlate with known threat actor patterns

3. **Evidence Collection Strategy**:
   - **Primary Evidence**: Original flow logs and anomaly detection results
   - **Contextual Evidence**: Historical patterns, geo-IP data, DNS lookups
   - **Enrichment Evidence**: Threat intelligence feeds, vulnerability data
   - **Correlation Evidence**: Related incidents and similar attack patterns

**Output**: InvestigationReport entity with evidence, timeline, and impact assessment

### 3. ResponseOrchestrationAgent Business Logic

**Purpose**: Automated response execution with context-aware authorization

**Processing Model**:
```
InvestigationReport → Authorization Assessment → Response Planning → Execution Coordination → Impact Monitoring
```

**Context-Aware Authorization Algorithm**:
1. **Authorization Tiers**:
   - **Automatic**: Low-risk actions (logging, alerting, monitoring)
   - **Semi-Automatic**: Medium-risk actions with time-delayed execution (network isolation)
   - **Manual Approval**: High-risk actions requiring human authorization (credential revocation)
   - **Emergency Override**: Critical threats with immediate automated response

2. **Response Action Categories**:
   - **Containment**: Network isolation, traffic blocking, system quarantine
   - **Eradication**: Malware removal, credential revocation, access termination
   - **Recovery**: System restoration, backup recovery, service restart
   - **Communication**: Stakeholder notification, incident reporting, escalation

3. **Safety Constraints**:
   - Business impact assessment before disruptive actions
   - Rollback procedures for all automated responses
   - Approval workflows for actions affecting critical systems
   - Audit trail for all response decisions and executions

**Output**: ResponsePlan entity with authorized actions and execution timeline

### 4. ThreatIntelligenceAgent Business Logic

**Purpose**: Threat feed management with hybrid knowledge base approach

**Processing Model**:
```
Multiple Threat Feeds → Feed Validation → Knowledge Integration → Enrichment Processing → Context Delivery
```

**Hybrid Knowledge Base Strategy**:
1. **Static Baseline Knowledge**:
   - MITRE ATT&CK framework mappings
   - Known malware signatures and IoCs
   - Threat actor profiles and TTPs
   - Vulnerability databases and exploit patterns

2. **Dynamic Threat Feed Integration**:
   - Real-time IoC feeds (IPs, domains, hashes)
   - Threat actor campaign updates
   - Zero-day vulnerability disclosures
   - Geopolitical threat landscape changes

3. **Knowledge Validation Logic**:
   - Source credibility scoring (government, commercial, open source)
   - Cross-reference validation across multiple feeds
   - Temporal relevance assessment (age, update frequency)
   - False positive filtering based on historical accuracy

4. **Enrichment Processing**:
   - Contextual threat scoring based on organizational relevance
   - Geographic and industry-specific threat prioritization
   - Asset-based risk assessment integration
   - Historical incident correlation

**Output**: ThreatIntelligence entity with validated IoCs and contextual scoring

### 5. RootCauseAnalysisAgent Business Logic

**Purpose**: Post-incident analysis with comprehensive correlation methodology

**Processing Model**:
```
Incident Data → Timeline Reconstruction → Causal Analysis → Systemic Assessment → Recommendation Generation
```

**Analysis Methodology**:
1. **Timeline Reconstruction**:
   - Chronological event sequencing from multiple data sources
   - Attack vector identification and progression mapping
   - Decision point analysis (where prevention could have occurred)
   - Impact cascade analysis (how damage propagated)

2. **Causal Analysis Framework**:
   - **Immediate Causes**: Direct technical failures or exploits
   - **Contributing Factors**: Configuration weaknesses, process gaps
   - **Root Causes**: Systemic issues, architectural vulnerabilities
   - **Organizational Factors**: Training, procedures, resource constraints

3. **Systemic Assessment**:
   - Similar vulnerability identification across infrastructure
   - Process improvement opportunities
   - Technology gap analysis
   - Risk mitigation prioritization

**Output**: RootCauseReport entity with findings and improvement recommendations

## Agent Coordination Patterns

### Sequential Processing Pattern
Used for: Standard threat progression (Classification → Investigation → Response)
```
ThreatClassifier → InvestigationAgent → ResponseOrchestration
```

### Parallel Processing Pattern
Used for: High-volume anomaly processing with multiple threat types
```
                    ┌─ ThreatClassifier
Anomaly Batch ──────┼─ ThreatIntelligence ──→ Result Aggregation
                    └─ RootCauseAnalysis
```

### Conditional Routing Pattern
Used for: Threat-specific agent specialization
```
Anomaly → Threat Type Assessment → {
    Port Scan → ThreatClassifier + ThreatIntelligence
    DDoS → ThreatClassifier + ResponseOrchestration
    C2 Beacon → Full Agent Pipeline
    Crypto Mining → ThreatClassifier + Investigation
    Tor Usage → ThreatIntelligence + Investigation
}
```

### Adaptive Hybrid Pattern
Used for: Dynamic agent coordination based on threat characteristics
```
Anomaly → Context Analysis → {
    Low Confidence → Parallel Classification + Intelligence
    High Confidence → Sequential Pipeline
    Critical Threat → Emergency Response + Full Investigation
    Known Pattern → Cached Response + Minimal Analysis
}
```

## Cost Optimization Logic

### Adaptive Token Management
1. **Model Selection Strategy**:
   - **Claude 3.5 Haiku**: Initial screening, simple classification
   - **Claude 3.5 Sonnet**: Complex analysis, detailed investigation
   - **Titan Embeddings**: Knowledge base similarity search

2. **Caching Strategy**:
   - Cache AI responses for similar anomaly patterns
   - Cache threat intelligence lookups for known IoCs
   - Cache investigation results for recurring threat types
   - TTL-based cache expiration with threat landscape updates

3. **Budget Management**:
   - Daily/monthly token budgets per agent
   - Dynamic budget allocation based on threat severity
   - Graceful degradation to rule-based processing when budget exceeded
   - Priority queuing for critical threats

4. **Processing Optimization**:
   - Batch similar anomalies for efficient processing
   - Pre-filter obvious false positives before AI analysis
   - Use statistical confidence to determine AI processing necessity
   - Implement circuit breakers for expensive operations

## Context Management Architecture

### Hierarchical Context Levels

1. **Global Context** (accessible to all agents):
   - System-wide threat landscape
   - Organizational security policies
   - Asset inventory and criticality
   - Historical incident patterns

2. **Investigation Context** (shared within investigation):
   - Anomaly details and detection results
   - Related flow logs and network data
   - Timeline and correlation information
   - Intermediate analysis results

3. **Agent-Specific Context** (private to each agent):
   - Agent processing state and history
   - Model-specific parameters and thresholds
   - Agent performance metrics and optimization data
   - Specialized knowledge base access patterns

### Context Sharing Patterns

1. **Context Inheritance**: Child agents inherit parent context
2. **Context Enrichment**: Each agent adds specialized context
3. **Context Synchronization**: Real-time context updates across agents
4. **Context Persistence**: Long-term context storage for learning

This business logic model provides the foundation for implementing the 5 specialized Bedrock agents with adaptive processing, cost optimization, and comprehensive threat analysis capabilities.