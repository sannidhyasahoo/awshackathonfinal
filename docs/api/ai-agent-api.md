# AI Agent API Documentation

## Overview

The AI Agent API provides direct access to the 5 specialized Bedrock agents for threat analysis, investigation, and response orchestration. Each agent has unique capabilities and tools for different aspects of security analysis.

## Available Agents

### 1. Threat Classifier Agent
**Purpose**: Analyzes network anomalies and determines threat classification
**Model**: Claude 3.5 Sonnet
**Response Time**: ~15 seconds average

### 2. Investigation Agent  
**Purpose**: Conducts deep investigation of confirmed threats
**Model**: Claude 3.5 Sonnet
**Response Time**: ~45 seconds average

### 3. Response Orchestration Agent
**Purpose**: Executes automated incident response actions
**Model**: Claude 3.5 Haiku (optimized for speed)
**Response Time**: ~8 seconds average

### 4. Threat Intelligence Agent
**Purpose**: Enriches threats with external intelligence feeds
**Model**: Claude 3.5 Sonnet
**Response Time**: ~20 seconds average

### 5. Root Cause Analysis Agent
**Purpose**: Post-incident analysis and prevention recommendations
**Model**: Claude 3.5 Sonnet
**Response Time**: ~60 seconds average

## Agent Interaction Patterns

### Synchronous Chat API

#### POST /ai-agents/chat
Direct synchronous interaction with any agent.

**Request:**
```json
{
  "agent_type": "threat_classifier",
  "message": "Analyze this network anomaly",
  "context": {
    "anomaly_data": {
      "source_ip": "192.168.1.100",
      "dest_ports": [22, 80, 443, 3389, 1433],
      "time_window": "60_seconds",
      "packet_count": 150
    },
    "resource_context": {
      "instance_id": "i-1234567890abcdef0",
      "security_groups": ["sg-web-servers"],
      "vpc_id": "vpc-12345678",
      "tags": {"Environment": "Production"}
    }
  },
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "agent_response": {
    "analysis": "This pattern indicates port scanning reconnaissance activity targeting common service ports.",
    "classification": {
      "is_threat": true,
      "severity": "HIGH", 
      "confidence": 95,
      "threat_type": "port_scanning",
      "mitre_techniques": ["T1046"]
    },
    "reasoning": "The source IP attempted connections to 5 different service ports within 60 seconds, which exceeds normal application behavior patterns. The targeted ports (22, 80, 443, 3389, 1433) represent common attack vectors.",
    "recommended_actions": [
      "Isolate source IP immediately",
      "Review security group configurations", 
      "Investigate potential lateral movement",
      "Check CloudTrail for API activity from source"
    ],
    "risk_assessment": {
      "blast_radius": "MEDIUM",
      "data_at_risk": "Customer databases accessible from web tier",
      "business_impact": "Potential service disruption if attack succeeds"
    }
  },
  "session_id": "chat-session-67890",
  "agent_metadata": {
    "model_used": "claude-3-5-sonnet",
    "processing_time": "14.2s",
    "token_usage": {
      "input_tokens": 450,
      "output_tokens": 320
    }
  },
  "timestamp": "2024-12-19T21:30:00Z"
}
```

### Asynchronous Investigation API

#### POST /ai-agents/investigate
Start an asynchronous investigation for complex analysis.

**Request:**
```json
{
  "incident_id": "threat-001-20241219",
  "investigation_type": "FULL_ANALYSIS",
  "priority": "HIGH",
  "context": {
    "threat_data": {
      "source_ip": "192.168.1.100",
      "affected_resources": ["i-1234567890abcdef0", "i-0987654321fedcba0"],
      "attack_vectors": ["port_scanning", "lateral_movement"]
    },
    "time_range": {
      "start": "2024-12-19T21:00:00Z",
      "end": "2024-12-19T21:30:00Z"
    }
  }
}
```

**Response:**
```json
{
  "investigation_id": "inv-12345-67890",
  "status": "IN_PROGRESS",
  "estimated_completion": "2024-12-19T21:35:00Z",
  "progress_url": "/ai-agents/investigations/inv-12345-67890",
  "webhook_url": "https://your-app.com/webhooks/investigation-complete"
}
```

#### GET /ai-agents/investigations/{investigation_id}
Get investigation progress and results.

**Response:**
```json
{
  "investigation_id": "inv-12345-67890",
  "status": "COMPLETED",
  "progress": 100,
  "started_at": "2024-12-19T21:30:00Z",
  "completed_at": "2024-12-19T21:34:30Z",
  "results": {
    "executive_summary": "Confirmed lateral movement attack originating from compromised web server. Attacker gained initial access via SSH brute force, then used stolen credentials to access database servers.",
    "attack_timeline": [
      {
        "timestamp": "2024-12-19T21:15:00Z",
        "event": "SSH brute force attack initiated",
        "evidence": "CloudTrail logs show 47 failed SSH attempts",
        "severity": "MEDIUM"
      },
      {
        "timestamp": "2024-12-19T21:18:30Z", 
        "event": "Successful SSH login achieved",
        "evidence": "Authentication success for user 'admin'",
        "severity": "HIGH"
      },
      {
        "timestamp": "2024-12-19T21:20:00Z",
        "event": "Lateral movement to database server",
        "evidence": "Network connections to internal DB subnet",
        "severity": "CRITICAL"
      }
    ],
    "evidence_collected": {
      "cloudtrail_events": 23,
      "network_flows": 156,
      "vulnerability_scans": 3,
      "threat_intel_matches": 2
    },
    "impact_assessment": {
      "compromised_resources": 3,
      "data_accessed": "Customer PII database",
      "estimated_records_at_risk": 50000,
      "business_impact": "HIGH"
    },
    "containment_recommendations": [
      {
        "action": "Isolate compromised instances",
        "priority": "IMMEDIATE",
        "estimated_time": "2 minutes"
      },
      {
        "action": "Reset all admin credentials", 
        "priority": "URGENT",
        "estimated_time": "15 minutes"
      },
      {
        "action": "Patch SSH vulnerabilities",
        "priority": "HIGH", 
        "estimated_time": "2 hours"
      }
    ]
  }
}
```

## Agent-Specific APIs

### Threat Classifier Agent

#### POST /ai-agents/threat-classifier/classify
Classify a specific anomaly as threat or benign.

**Request:**
```json
{
  "anomaly_data": {
    "source_ip": "10.0.1.50",
    "dest_ip": "45.76.102.45",
    "dest_port": 4444,
    "connection_count": 1,
    "bytes_transferred": 1024,
    "duration": "300s"
  },
  "baseline_data": {
    "normal_connections": ["80", "443"],
    "typical_destinations": ["internal_services"],
    "resource_role": "web_server"
  }
}
```

**Response:**
```json
{
  "classification": {
    "is_threat": true,
    "threat_type": "crypto_mining",
    "severity": "CRITICAL",
    "confidence": 98
  },
  "analysis": {
    "threat_indicators": [
      "Connection to known mining pool IP",
      "Port 4444 commonly used for mining protocols",
      "Unusual for web server to initiate external connections"
    ],
    "mitre_mapping": ["T1496"],
    "business_context": "Web server should not connect to external mining pools"
  }
}
```

### Investigation Agent

#### POST /ai-agents/investigation/deep-dive
Conduct detailed investigation with tool usage.

**Request:**
```json
{
  "incident_id": "threat-001-20241219",
  "investigation_scope": {
    "time_range_hours": 24,
    "resource_scope": ["vpc-12345678"],
    "investigation_depth": "COMPREHENSIVE"
  },
  "tools_requested": [
    "query_cloudtrail",
    "analyze_network_topology", 
    "check_vulnerabilities",
    "correlate_threat_intel"
  ]
}
```

### Response Orchestration Agent

#### POST /ai-agents/response/orchestrate
Execute coordinated incident response.

**Request:**
```json
{
  "incident_id": "threat-001-20241219",
  "response_level": "CRITICAL",
  "affected_resources": ["i-1234567890abcdef0"],
  "approval_mode": "HUMAN_REQUIRED",
  "business_hours": true
}
```

**Response:**
```json
{
  "response_plan": {
    "immediate_actions": [
      {
        "action": "isolate_instance",
        "resource": "i-1234567890abcdef0",
        "method": "security_group_modification",
        "estimated_time": "30s",
        "approval_required": true
      }
    ],
    "follow_up_actions": [
      {
        "action": "create_forensic_snapshot",
        "resource": "i-1234567890abcdef0", 
        "estimated_time": "5m",
        "approval_required": false
      }
    ],
    "notification_plan": {
      "immediate": ["security_team", "incident_commander"],
      "escalation": ["ciso", "engineering_manager"],
      "external": ["customer_success"]
    }
  },
  "execution_id": "resp-12345-67890"
}
```

## WebSocket API for Real-time Agent Interaction

### Connection
```javascript
const ws = new WebSocket('wss://api.vpc-anomaly-detection.com/v1/ai-agents/ws');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'your-api-key'
  }));
};
```

### Real-time Agent Chat
```javascript
// Send message to agent
ws.send(JSON.stringify({
  type: 'agent_chat',
  agent_type: 'threat_classifier',
  message: 'Analyze this anomaly...',
  session_id: 'chat-session-12345'
}));

// Receive streaming response
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'agent_response_chunk') {
    // Handle streaming response chunk
    console.log(data.content);
  }
};
```

### Investigation Progress Updates
```javascript
// Subscribe to investigation updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'investigation_progress',
  investigation_id: 'inv-12345-67890'
}));

// Receive progress updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'investigation_update') {
    console.log(`Progress: ${data.progress}%`);
    console.log(`Status: ${data.status}`);
  }
};
```

## Error Handling

### Agent-Specific Errors
```json
{
  "error": {
    "code": "AGENT_TIMEOUT",
    "message": "Agent response timed out after 60 seconds",
    "agent_type": "investigation_agent",
    "retry_after": 30,
    "fallback_available": true
  }
}
```

### Rate Limiting
```json
{
  "error": {
    "code": "AGENT_RATE_LIMITED", 
    "message": "Agent usage quota exceeded",
    "quota_reset": "2024-12-19T22:00:00Z",
    "current_usage": "95/100 requests per hour"
  }
}
```

## Best Practices

### Efficient Agent Usage
1. **Use appropriate agent types** for specific tasks
2. **Provide rich context** for better analysis quality
3. **Implement caching** for repeated queries
4. **Use async APIs** for complex investigations
5. **Handle timeouts gracefully** with fallback logic

### Cost Optimization
1. **Batch similar requests** when possible
2. **Use Haiku model** for simple classification tasks
3. **Cache agent responses** for identical inputs
4. **Implement request deduplication**
5. **Monitor token usage** and optimize prompts

### Integration Patterns
```javascript
// Example: Progressive enhancement with fallback
async function analyzeThreats(anomalies) {
  try {
    // Try AI agent first
    const aiAnalysis = await aiAgent.classify(anomalies);
    return aiAnalysis;
  } catch (error) {
    if (error.code === 'AGENT_TIMEOUT') {
      // Fallback to rule-based analysis
      return ruleBasedClassifier.analyze(anomalies);
    }
    throw error;
  }
}
```