# REST API Reference

## Base URL
```
https://api.vpc-anomaly-detection.com/v1
```

## Authentication
All API requests require authentication using API keys:
```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

## Endpoints

### Threat Detection

#### GET /threats
Get list of detected threats with filtering and pagination.

**Parameters:**
- `severity` (optional): Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `status` (optional): Filter by status (ACTIVE, INVESTIGATING, RESOLVED)
- `limit` (optional): Number of results (default: 50, max: 1000)
- `offset` (optional): Pagination offset (default: 0)
- `start_time` (optional): ISO timestamp for time range filtering
- `end_time` (optional): ISO timestamp for time range filtering

**Response:**
```json
{
  "threats": [
    {
      "incident_id": "threat-001-20241219",
      "timestamp": "2024-12-19T21:30:00Z",
      "threat_type": "port_scanning",
      "severity": "HIGH",
      "confidence": 95,
      "source_ip": "192.168.1.100",
      "affected_resources": ["i-1234567890abcdef0"],
      "status": "ACTIVE",
      "ai_analysis": {
        "reasoning": "Source IP scanned 25 unique ports in 60 seconds, indicating reconnaissance activity",
        "mitre_techniques": ["T1046"],
        "recommended_actions": ["isolate_source", "investigate_lateral_movement"]
      },
      "investigation_status": "IN_PROGRESS"
    }
  ],
  "total_count": 150,
  "has_more": true
}
```

#### GET /threats/{incident_id}
Get detailed information about a specific threat.

**Response:**
```json
{
  "incident_id": "threat-001-20241219",
  "timestamp": "2024-12-19T21:30:00Z",
  "threat_type": "port_scanning",
  "severity": "HIGH",
  "confidence": 95,
  "source_ip": "192.168.1.100",
  "dest_ips": ["10.0.1.50", "10.0.1.51", "10.0.1.52"],
  "ports_scanned": [22, 80, 443, 3389, 1433, 3306],
  "affected_resources": [
    {
      "resource_id": "i-1234567890abcdef0",
      "resource_type": "EC2",
      "tags": {"Environment": "Production", "Role": "WebServer"}
    }
  ],
  "ai_analysis": {
    "classifier_agent": {
      "reasoning": "Multiple port scanning patterns detected",
      "confidence": 95,
      "threat_indicators": ["high_port_diversity", "rapid_scanning"]
    },
    "investigation_agent": {
      "timeline": [
        {
          "timestamp": "2024-12-19T21:29:30Z",
          "event": "Initial connection attempt to port 22"
        },
        {
          "timestamp": "2024-12-19T21:30:00Z",
          "event": "Rapid scanning of 25 ports initiated"
        }
      ],
      "evidence": {
        "cloudtrail_events": 5,
        "network_connections": 25,
        "suspicious_patterns": ["port_enumeration", "service_discovery"]
      }
    }
  },
  "response_actions": [
    {
      "action": "security_group_isolation",
      "status": "PENDING_APPROVAL",
      "timestamp": "2024-12-19T21:31:00Z"
    }
  ],
  "investigation_notes": "Investigating potential lateral movement from compromised source"
}
```

### AI Agent Interaction

#### POST /ai-agents/chat
Interact with AI agents for threat analysis and investigation.

**Request:**
```json
{
  "agent_type": "threat_classifier",
  "message": "Analyze this network anomaly: source IP 192.168.1.100 connected to 25 different ports in 60 seconds",
  "context": {
    "incident_id": "threat-001-20241219",
    "resource_context": {
      "instance_id": "i-1234567890abcdef0",
      "security_groups": ["sg-web-servers"],
      "vpc_id": "vpc-12345678"
    }
  }
}
```

**Response:**
```json
{
  "agent_response": {
    "analysis": "This pattern indicates port scanning reconnaissance activity. The rapid connection attempts to diverse ports suggest an attacker is mapping available services.",
    "threat_classification": {
      "is_threat": true,
      "severity": "HIGH",
      "confidence": 95,
      "threat_type": "port_scanning",
      "mitre_techniques": ["T1046"]
    },
    "recommended_actions": [
      "Isolate source IP immediately",
      "Review security group rules",
      "Check for lateral movement indicators",
      "Analyze CloudTrail logs for API activity"
    ],
    "reasoning": "High port diversity (25 ports) in short timeframe (60s) exceeds normal application behavior. Source IP shows no legitimate business justification for this access pattern."
  },
  "session_id": "chat-session-12345",
  "timestamp": "2024-12-19T21:32:00Z"
}
```

#### GET /ai-agents/sessions/{session_id}
Get chat session history with AI agents.

**Response:**
```json
{
  "session_id": "chat-session-12345",
  "agent_type": "investigation_agent",
  "messages": [
    {
      "timestamp": "2024-12-19T21:30:00Z",
      "role": "user",
      "content": "Investigate this critical threat: lateral movement detected"
    },
    {
      "timestamp": "2024-12-19T21:30:15Z",
      "role": "agent",
      "content": "I'll investigate the lateral movement. Let me analyze the attack timeline and gather evidence.",
      "actions_taken": ["query_cloudtrail", "analyze_network_topology"]
    }
  ],
  "investigation_summary": {
    "findings": ["Compromised credentials used", "Privilege escalation attempted"],
    "evidence_collected": 15,
    "timeline_events": 8
  }
}
```

### Real-time Data

#### GET /dashboard/metrics
Get real-time dashboard metrics.

**Response:**
```json
{
  "current_metrics": {
    "active_threats": 12,
    "threats_last_24h": 45,
    "processing_rate": "1,250 anomalies/hour",
    "system_health": "HEALTHY",
    "cost_today": "$0.42",
    "false_positive_rate": "2.1%"
  },
  "threat_breakdown": {
    "CRITICAL": 2,
    "HIGH": 5,
    "MEDIUM": 3,
    "LOW": 2
  },
  "top_threat_types": [
    {"type": "port_scanning", "count": 8},
    {"type": "crypto_mining", "count": 3},
    {"type": "tor_usage", "count": 1}
  ],
  "geographic_distribution": [
    {"country": "US", "threat_count": 7},
    {"country": "CN", "threat_count": 3},
    {"country": "RU", "threat_count": 2}
  ]
}
```

### Incident Management

#### POST /incidents/{incident_id}/actions
Execute response actions for an incident.

**Request:**
```json
{
  "action_type": "isolate_instance",
  "parameters": {
    "instance_id": "i-1234567890abcdef0",
    "isolation_method": "security_group_modification"
  },
  "approval_required": true,
  "justification": "Critical threat requires immediate containment"
}
```

**Response:**
```json
{
  "action_id": "action-12345",
  "status": "PENDING_APPROVAL",
  "estimated_execution_time": "30 seconds",
  "approval_url": "https://dashboard.com/approve/action-12345",
  "rollback_available": true
}
```

#### GET /incidents/{incident_id}/timeline
Get incident investigation timeline.

**Response:**
```json
{
  "incident_id": "threat-001-20241219",
  "timeline": [
    {
      "timestamp": "2024-12-19T21:29:00Z",
      "event_type": "DETECTION",
      "description": "Anomaly detected by statistical analysis",
      "source": "kinesis_analytics"
    },
    {
      "timestamp": "2024-12-19T21:29:30Z",
      "event_type": "AI_CLASSIFICATION",
      "description": "Threat classified as HIGH severity port scanning",
      "source": "threat_classifier_agent",
      "confidence": 95
    },
    {
      "timestamp": "2024-12-19T21:30:00Z",
      "event_type": "INVESTIGATION_STARTED",
      "description": "Investigation agent began evidence collection",
      "source": "investigation_agent"
    }
  ],
  "investigation_progress": {
    "evidence_collected": 8,
    "tools_executed": ["query_cloudtrail", "check_vulnerabilities"],
    "completion_percentage": 75
  }
}
```

### Configuration

#### GET /config/agents
Get AI agent configuration and status.

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "threat-classifier",
      "name": "Threat Classifier Agent",
      "model": "claude-3-5-sonnet",
      "status": "ACTIVE",
      "last_invocation": "2024-12-19T21:30:00Z",
      "success_rate": 98.5,
      "average_response_time": "15s"
    },
    {
      "agent_id": "investigation-agent",
      "name": "Investigation Agent",
      "model": "claude-3-5-sonnet",
      "status": "ACTIVE",
      "tools_available": ["query_cloudtrail", "check_vulnerabilities", "analyze_network"],
      "success_rate": 96.2
    }
  ]
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "THREAT_NOT_FOUND",
    "message": "The specified threat incident was not found",
    "details": "Incident ID 'invalid-id' does not exist",
    "timestamp": "2024-12-19T21:30:00Z"
  }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

## Rate Limits
- **Standard endpoints**: 1000 requests/hour
- **AI agent chat**: 100 requests/hour
- **Real-time metrics**: 600 requests/hour

## SDKs and Libraries

### JavaScript/TypeScript
```bash
npm install vpc-anomaly-detection-sdk
```

### Python
```bash
pip install vpc-anomaly-detection
```

### Example Usage
```javascript
import { VPCAnomalyClient } from 'vpc-anomaly-detection-sdk';

const client = new VPCAnomalyClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.vpc-anomaly-detection.com/v1'
});

// Get active threats
const threats = await client.threats.list({
  severity: 'HIGH',
  status: 'ACTIVE'
});

// Chat with AI agent
const response = await client.aiAgents.chat({
  agentType: 'threat_classifier',
  message: 'Analyze this suspicious activity...'
});
```