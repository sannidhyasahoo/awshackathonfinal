# WebSocket API Documentation

## Overview

The WebSocket API provides real-time streaming of threat detection events, AI agent interactions, and system metrics. This enables responsive web applications with live updates and interactive AI agent conversations.

## Connection

### Endpoint
```
wss://api.vpc-anomaly-detection.com/v1/ws
```

### Authentication
```javascript
const ws = new WebSocket('wss://api.vpc-anomaly-detection.com/v1/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'your-api-key',
    client_info: {
      name: 'Security Dashboard',
      version: '1.0.0'
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'auth_success') {
    console.log('Connected successfully');
    // Start subscribing to channels
  }
};
```

## Message Types

### Authentication Messages

#### Authenticate
```json
{
  "type": "authenticate",
  "token": "your-api-key",
  "client_info": {
    "name": "Security Dashboard",
    "version": "1.0.0",
    "user_id": "user-12345"
  }
}
```

#### Authentication Response
```json
{
  "type": "auth_success",
  "session_id": "ws-session-67890",
  "permissions": ["read_threats", "chat_agents", "execute_actions"],
  "rate_limits": {
    "messages_per_minute": 60,
    "agent_chats_per_hour": 100
  }
}
```

### Subscription Management

#### Subscribe to Channel
```json
{
  "type": "subscribe",
  "channel": "threat_alerts",
  "filters": {
    "severity": ["CRITICAL", "HIGH"],
    "threat_types": ["port_scanning", "crypto_mining"]
  }
}
```

#### Subscription Confirmation
```json
{
  "type": "subscription_confirmed",
  "channel": "threat_alerts",
  "subscription_id": "sub-12345"
}
```

#### Unsubscribe
```json
{
  "type": "unsubscribe",
  "subscription_id": "sub-12345"
}
```

## Available Channels

### 1. Threat Alerts (`threat_alerts`)

Real-time threat detection notifications.

**Subscription:**
```json
{
  "type": "subscribe",
  "channel": "threat_alerts",
  "filters": {
    "severity": ["CRITICAL", "HIGH"],
    "threat_types": ["port_scanning", "crypto_mining", "lateral_movement"],
    "resources": ["vpc-12345678"]
  }
}
```

**Event Message:**
```json
{
  "type": "threat_alert",
  "channel": "threat_alerts",
  "timestamp": "2024-12-19T21:30:00Z",
  "data": {
    "incident_id": "threat-001-20241219",
    "threat_type": "port_scanning",
    "severity": "HIGH",
    "confidence": 95,
    "source_ip": "192.168.1.100",
    "affected_resources": ["i-1234567890abcdef0"],
    "ai_summary": "Port scanning detected from internal IP targeting production web servers",
    "recommended_actions": ["isolate_source", "investigate_compromise"],
    "auto_response_available": true
  }
}
```

### 2. AI Agent Chat (`agent_chat`)

Interactive conversations with AI agents.

**Start Chat Session:**
```json
{
  "type": "start_chat",
  "agent_type": "threat_classifier",
  "context": {
    "incident_id": "threat-001-20241219",
    "user_role": "security_analyst"
  }
}
```

**Chat Session Started:**
```json
{
  "type": "chat_session_started",
  "session_id": "chat-12345",
  "agent_type": "threat_classifier",
  "agent_info": {
    "name": "Threat Classifier Agent",
    "model": "claude-3-5-sonnet",
    "capabilities": ["threat_analysis", "risk_assessment", "mitigation_advice"]
  }
}
```

**Send Message:**
```json
{
  "type": "chat_message",
  "session_id": "chat-12345",
  "message": "Can you analyze the port scanning activity from 192.168.1.100? What's the risk level?",
  "context": {
    "anomaly_data": {
      "source_ip": "192.168.1.100",
      "ports_scanned": 25,
      "time_window": "60s"
    }
  }
}
```

**Agent Response (Streaming):**
```json
{
  "type": "agent_response_chunk",
  "session_id": "chat-12345",
  "chunk_id": 1,
  "content": "I'm analyzing the port scanning activity from 192.168.1.100. ",
  "is_final": false
}
```

```json
{
  "type": "agent_response_chunk", 
  "session_id": "chat-12345",
  "chunk_id": 2,
  "content": "This appears to be reconnaissance activity with HIGH risk level. The source scanned 25 ports in 60 seconds, which indicates automated scanning tools.",
  "is_final": false
}
```

**Final Response:**
```json
{
  "type": "agent_response_complete",
  "session_id": "chat-12345",
  "full_response": "I'm analyzing the port scanning activity from 192.168.1.100. This appears to be reconnaissance activity with HIGH risk level. The source scanned 25 ports in 60 seconds, which indicates automated scanning tools.",
  "analysis": {
    "threat_classification": {
      "severity": "HIGH",
      "confidence": 95,
      "threat_type": "port_scanning"
    },
    "risk_factors": [
      "High port diversity indicates reconnaissance",
      "Internal IP suggests potential compromise",
      "Targeting production infrastructure"
    ],
    "recommended_actions": [
      "Immediate isolation of source IP",
      "Investigation of initial compromise vector",
      "Review of security group configurations"
    ]
  },
  "metadata": {
    "processing_time": "14.2s",
    "tokens_used": 450
  }
}
```

### 3. Investigation Progress (`investigation_progress`)

Real-time updates on ongoing investigations.

**Subscribe:**
```json
{
  "type": "subscribe",
  "channel": "investigation_progress",
  "investigation_id": "inv-12345-67890"
}
```

**Progress Update:**
```json
{
  "type": "investigation_update",
  "channel": "investigation_progress",
  "investigation_id": "inv-12345-67890",
  "timestamp": "2024-12-19T21:32:00Z",
  "data": {
    "progress": 45,
    "status": "ANALYZING_EVIDENCE",
    "current_activity": "Querying CloudTrail logs for API activity",
    "evidence_collected": 12,
    "tools_executed": ["query_cloudtrail", "check_vulnerabilities"],
    "estimated_completion": "2024-12-19T21:35:00Z",
    "findings_preview": [
      "Suspicious API calls detected",
      "Privilege escalation attempts identified"
    ]
  }
}
```

### 4. System Metrics (`system_metrics`)

Real-time system health and performance metrics.

**Subscribe:**
```json
{
  "type": "subscribe", 
  "channel": "system_metrics",
  "metrics": ["threat_count", "processing_rate", "cost_tracking"]
}
```

**Metrics Update:**
```json
{
  "type": "metrics_update",
  "channel": "system_metrics",
  "timestamp": "2024-12-19T21:30:00Z",
  "data": {
    "threat_count": {
      "active": 12,
      "last_hour": 8,
      "last_24h": 45
    },
    "processing_rate": {
      "anomalies_per_hour": 1250,
      "avg_detection_time": "2.3s",
      "queue_depth": 15
    },
    "cost_tracking": {
      "today": "$0.42",
      "projected_daily": "$0.68",
      "budget_status": "UNDER_BUDGET"
    },
    "agent_performance": {
      "threat_classifier": {
        "avg_response_time": "15s",
        "success_rate": 98.5
      },
      "investigation_agent": {
        "avg_response_time": "45s", 
        "success_rate": 96.2
      }
    }
  }
}
```

### 5. Response Actions (`response_actions`)

Real-time updates on automated response execution.

**Subscribe:**
```json
{
  "type": "subscribe",
  "channel": "response_actions",
  "filters": {
    "action_types": ["isolate_instance", "block_ip"],
    "approval_status": ["PENDING", "EXECUTING"]
  }
}
```

**Action Update:**
```json
{
  "type": "action_update",
  "channel": "response_actions", 
  "timestamp": "2024-12-19T21:31:00Z",
  "data": {
    "action_id": "action-12345",
    "incident_id": "threat-001-20241219",
    "action_type": "isolate_instance",
    "status": "EXECUTING",
    "progress": 75,
    "target_resource": "i-1234567890abcdef0",
    "estimated_completion": "2024-12-19T21:31:30Z",
    "execution_log": [
      "Security group backup created",
      "Isolation rules applied",
      "Verifying connectivity restrictions"
    ]
  }
}
```

## Interactive Features

### Agent Tool Execution Streaming

Watch AI agents execute tools in real-time:

```json
{
  "type": "agent_tool_execution",
  "session_id": "chat-12345",
  "tool_name": "query_cloudtrail",
  "status": "EXECUTING",
  "parameters": {
    "resource": "i-1234567890abcdef0",
    "time_range": "24h"
  }
}
```

```json
{
  "type": "agent_tool_result",
  "session_id": "chat-12345", 
  "tool_name": "query_cloudtrail",
  "status": "COMPLETED",
  "results": {
    "events_found": 23,
    "suspicious_activities": 3,
    "summary": "Found evidence of privilege escalation attempts"
  }
}
```

### Collaborative Investigation

Multiple users can collaborate on investigations:

```json
{
  "type": "investigation_collaboration",
  "investigation_id": "inv-12345-67890",
  "event": "USER_JOINED",
  "user": {
    "id": "analyst-456",
    "name": "Sarah Chen",
    "role": "Senior Security Analyst"
  }
}
```

```json
{
  "type": "investigation_note_added",
  "investigation_id": "inv-12345-67890",
  "note": {
    "id": "note-789",
    "author": "analyst-456",
    "content": "Found additional evidence in network logs",
    "timestamp": "2024-12-19T21:33:00Z",
    "attachments": ["network-analysis.json"]
  }
}
```

## Client Implementation Examples

### React Hook for WebSocket
```javascript
import { useState, useEffect, useRef } from 'react';

export function useVPCWebSocket(apiKey) {
  const [connected, setConnected] = useState(false);
  const [threats, setThreats] = useState([]);
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket('wss://api.vpc-anomaly-detection.com/v1/ws');
    
    ws.current.onopen = () => {
      ws.current.send(JSON.stringify({
        type: 'authenticate',
        token: apiKey
      }));
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'auth_success':
          setConnected(true);
          // Subscribe to threat alerts
          ws.current.send(JSON.stringify({
            type: 'subscribe',
            channel: 'threat_alerts'
          }));
          break;
          
        case 'threat_alert':
          setThreats(prev => [message.data, ...prev]);
          break;
      }
    };

    return () => ws.current?.close();
  }, [apiKey]);

  const sendMessage = (message) => {
    if (connected) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { connected, threats, sendMessage };
}
```

### Vue.js Composition API
```javascript
import { ref, onMounted, onUnmounted } from 'vue';

export function useAIAgentChat(apiKey) {
  const connected = ref(false);
  const messages = ref([]);
  const ws = ref(null);

  const startChat = (agentType, context) => {
    ws.value.send(JSON.stringify({
      type: 'start_chat',
      agent_type: agentType,
      context
    }));
  };

  const sendMessage = (sessionId, message, context) => {
    ws.value.send(JSON.stringify({
      type: 'chat_message',
      session_id: sessionId,
      message,
      context
    }));
  };

  onMounted(() => {
    ws.value = new WebSocket('wss://api.vpc-anomaly-detection.com/v1/ws');
    
    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'agent_response_chunk') {
        // Handle streaming response
        const lastMessage = messages.value[messages.value.length - 1];
        if (lastMessage && lastMessage.streaming) {
          lastMessage.content += data.content;
        } else {
          messages.value.push({
            type: 'agent',
            content: data.content,
            streaming: true,
            session_id: data.session_id
          });
        }
      }
    };
  });

  onUnmounted(() => {
    ws.value?.close();
  });

  return { connected, messages, startChat, sendMessage };
}
```

## Error Handling

### Connection Errors
```json
{
  "type": "error",
  "code": "CONNECTION_FAILED",
  "message": "WebSocket connection failed",
  "retry_after": 5000
}
```

### Rate Limiting
```json
{
  "type": "rate_limit_exceeded",
  "limit_type": "messages_per_minute",
  "current_usage": "65/60",
  "reset_time": "2024-12-19T21:31:00Z"
}
```

### Agent Errors
```json
{
  "type": "agent_error",
  "session_id": "chat-12345",
  "error": {
    "code": "AGENT_TIMEOUT",
    "message": "Agent response timed out",
    "retry_available": true
  }
}
```

## Best Practices

### Connection Management
1. **Implement reconnection logic** with exponential backoff
2. **Handle authentication expiry** gracefully
3. **Monitor connection health** with ping/pong
4. **Buffer messages** during disconnections

### Performance Optimization
1. **Subscribe only to needed channels**
2. **Use message filtering** to reduce bandwidth
3. **Implement client-side caching** for repeated data
4. **Batch UI updates** for high-frequency events

### Security Considerations
1. **Validate all incoming messages**
2. **Sanitize user inputs** before sending
3. **Implement proper error boundaries**
4. **Log security-relevant events**