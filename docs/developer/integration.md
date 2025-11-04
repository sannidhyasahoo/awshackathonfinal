# Frontend Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the VPC Flow Log Anomaly Detection System with web applications, focusing on React, Vue.js, and Angular implementations with AI agent capabilities.

## Quick Start Integration

### React Integration

#### Installation
```bash
npm install vpc-anomaly-detection-sdk @tanstack/react-query
```

#### Basic Setup
```jsx
import React from 'react';
import { VPCAnomalyProvider, useThreats, useAIAgent } from 'vpc-anomaly-detection-sdk/react';

function App() {
  return (
    <VPCAnomalyProvider 
      apiKey={process.env.REACT_APP_VPC_API_KEY}
      baseUrl="https://api.vpc-anomaly-detection.com/v1"
    >
      <SecurityDashboard />
    </VPCAnomalyProvider>
  );
}

function SecurityDashboard() {
  const { threats, loading, error } = useThreats({
    severity: ['CRITICAL', 'HIGH'],
    autoRefresh: true
  });

  const { chatWithAgent, messages, isTyping } = useAIAgent('threat_classifier');

  if (loading) return <div>Loading threats...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="security-dashboard">
      <ThreatList threats={threats} />
      <AIAgentChat 
        onSendMessage={chatWithAgent}
        messages={messages}
        isTyping={isTyping}
      />
    </div>
  );
}
```

#### Real-time Threat Component
```jsx
import { useWebSocket, useThreats } from 'vpc-anomaly-detection-sdk/react';

function RealTimeThreatFeed() {
  const [threats, setThreats] = useState([]);
  
  const { connected, subscribe } = useWebSocket({
    onThreatAlert: (threat) => {
      setThreats(prev => [threat, ...prev.slice(0, 99)]); // Keep last 100
      
      // Show notification for critical threats
      if (threat.severity === 'CRITICAL') {
        showNotification({
          title: `Critical Threat Detected`,
          body: `${threat.threat_type} from ${threat.source_ip}`,
          icon: '/threat-icon.png',
          actions: [
            { action: 'investigate', title: 'Investigate' },
            { action: 'isolate', title: 'Isolate' }
          ]
        });
      }
    }
  });

  useEffect(() => {
    if (connected) {
      subscribe('threat_alerts', {
        severity: ['CRITICAL', 'HIGH']
      });
    }
  }, [connected, subscribe]);

  return (
    <div className="threat-feed">
      <div className="connection-status">
        {connected ? '🟢 Live' : '🔴 Disconnected'}
      </div>
      
      {threats.map(threat => (
        <ThreatCard 
          key={threat.incident_id} 
          threat={threat}
          onAction={(action) => handleThreatAction(threat, action)}
        />
      ))}
    </div>
  );
}
```

#### AI Agent Chat Component
```jsx
import { useState, useRef, useEffect } from 'react';
import { useAIAgent } from 'vpc-anomaly-detection-sdk/react';

function AIAgentChat({ agentType = 'threat_classifier', context }) {
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef(null);
  
  const { 
    messages, 
    sendMessage, 
    isTyping, 
    startSession,
    sessionId 
  } = useAIAgent(agentType);

  useEffect(() => {
    startSession(context);
  }, [context]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!message.trim()) return;
    
    await sendMessage(message, context);
    setMessage('');
  };

  return (
    <div className="ai-chat">
      <div className="chat-header">
        <div className="agent-info">
          🤖 {agentType.replace('_', ' ').toUpperCase()}
          <span className={`status ${sessionId ? 'online' : 'offline'}`}>
            {sessionId ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>
      
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="content">
              {msg.role === 'agent' && msg.analysis && (
                <ThreatAnalysis analysis={msg.analysis} />
              )}
              <p>{msg.content}</p>
            </div>
            <div className="timestamp">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="message agent typing">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask the AI agent about threats..."
          disabled={!sessionId}
        />
        <button onClick={handleSend} disabled={!sessionId || !message.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
```

### Vue.js Integration

#### Composition API Setup
```javascript
// composables/useVPCAnomaly.js
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { VPCAnomalyClient } from 'vpc-anomaly-detection-sdk';

export function useVPCAnomaly(apiKey) {
  const client = new VPCAnomalyClient({ apiKey });
  const threats = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const fetchThreats = async (filters = {}) => {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await client.threats.list(filters);
      threats.value = response.threats;
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  return {
    threats,
    loading,
    error,
    fetchThreats
  };
}

export function useAIAgentChat(agentType) {
  const messages = ref([]);
  const isTyping = ref(false);
  const sessionId = ref(null);
  const client = new VPCAnomalyClient();

  const startSession = async (context) => {
    try {
      const session = await client.aiAgents.startChat(agentType, context);
      sessionId.value = session.sessionId;
    } catch (error) {
      console.error('Failed to start chat session:', error);
    }
  };

  const sendMessage = async (message, context) => {
    if (!sessionId.value) return;

    // Add user message
    messages.value.push({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    });

    isTyping.value = true;

    try {
      const response = await client.aiAgents.chat({
        sessionId: sessionId.value,
        message,
        context
      });

      // Add agent response
      messages.value.push({
        role: 'agent',
        content: response.agent_response.analysis,
        analysis: response.agent_response.classification,
        timestamp: response.timestamp
      });
    } catch (error) {
      messages.value.push({
        role: 'system',
        content: 'Error: Failed to get agent response',
        timestamp: new Date().toISOString()
      });
    } finally {
      isTyping.value = false;
    }
  };

  return {
    messages,
    isTyping,
    sessionId,
    startSession,
    sendMessage
  };
}
```

#### Vue Component
```vue
<template>
  <div class="security-dashboard">
    <div class="threat-overview">
      <h2>Active Threats</h2>
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error.message }}</div>
      <div v-else class="threat-grid">
        <ThreatCard 
          v-for="threat in threats" 
          :key="threat.incident_id"
          :threat="threat"
          @investigate="openInvestigation"
          @isolate="isolateResource"
        />
      </div>
    </div>

    <div class="ai-assistant">
      <AIAgentChat 
        agent-type="threat_classifier"
        :context="selectedThreatContext"
        @message-sent="handleAgentMessage"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useVPCAnomaly, useAIAgentChat } from '@/composables/useVPCAnomaly';
import ThreatCard from '@/components/ThreatCard.vue';
import AIAgentChat from '@/components/AIAgentChat.vue';

const { threats, loading, error, fetchThreats } = useVPCAnomaly();
const selectedThreat = ref(null);

const selectedThreatContext = computed(() => {
  if (!selectedThreat.value) return null;
  
  return {
    incident_id: selectedThreat.value.incident_id,
    threat_data: selectedThreat.value,
    user_role: 'security_analyst'
  };
});

const openInvestigation = (threat) => {
  selectedThreat.value = threat;
};

const isolateResource = async (threat) => {
  try {
    await client.incidents.executeAction(threat.incident_id, {
      action_type: 'isolate_instance',
      parameters: {
        instance_id: threat.affected_resources[0]
      }
    });
    
    // Refresh threats
    await fetchThreats();
  } catch (error) {
    console.error('Failed to isolate resource:', error);
  }
};

onMounted(() => {
  fetchThreats({ severity: ['CRITICAL', 'HIGH'] });
});
</script>
```

### Angular Integration

#### Service Setup
```typescript
// services/vpc-anomaly.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, interval } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { VPCAnomalyClient } from 'vpc-anomaly-detection-sdk';

@Injectable({
  providedIn: 'root'
})
export class VPCAnomalyService {
  private client: VPCAnomalyClient;
  private threatsSubject = new BehaviorSubject<Threat[]>([]);
  private wsConnection: WebSocket | null = null;

  constructor() {
    this.client = new VPCAnomalyClient({
      apiKey: environment.vpcApiKey
    });
    
    this.initializeWebSocket();
  }

  get threats$(): Observable<Threat[]> {
    return this.threatsSubject.asObservable();
  }

  async fetchThreats(filters?: ThreatFilters): Promise<void> {
    try {
      const response = await this.client.threats.list(filters);
      this.threatsSubject.next(response.threats);
    } catch (error) {
      console.error('Failed to fetch threats:', error);
    }
  }

  private initializeWebSocket(): void {
    this.wsConnection = new WebSocket('wss://api.vpc-anomaly-detection.com/v1/ws');
    
    this.wsConnection.onopen = () => {
      this.wsConnection?.send(JSON.stringify({
        type: 'authenticate',
        token: environment.vpcApiKey
      }));
    };

    this.wsConnection.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'threat_alert') {
        const currentThreats = this.threatsSubject.value;
        this.threatsSubject.next([message.data, ...currentThreats]);
      }
    };
  }

  async chatWithAgent(agentType: string, message: string, context?: any): Promise<AgentResponse> {
    return await this.client.aiAgents.chat({
      agentType,
      message,
      context
    });
  }
}
```

#### Angular Component
```typescript
// components/security-dashboard.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { VPCAnomalyService } from '../services/vpc-anomaly.service';

@Component({
  selector: 'app-security-dashboard',
  template: `
    <div class="security-dashboard">
      <div class="metrics-panel">
        <app-security-metrics [threats]="threats$ | async"></app-security-metrics>
      </div>
      
      <div class="threats-panel">
        <h2>Active Threats</h2>
        <app-threat-list 
          [threats]="threats$ | async"
          (investigate)="openInvestigation($event)"
          (isolate)="isolateResource($event)">
        </app-threat-list>
      </div>
      
      <div class="ai-panel">
        <app-ai-agent-chat
          [agentType]="'threat_classifier'"
          [context]="selectedThreatContext"
          (messageSent)="handleAgentMessage($event)">
        </app-ai-agent-chat>
      </div>
    </div>
  `,
  styleUrls: ['./security-dashboard.component.scss']
})
export class SecurityDashboardComponent implements OnInit, OnDestroy {
  threats$: Observable<Threat[]>;
  selectedThreat: Threat | null = null;
  selectedThreatContext: any = null;
  
  private destroy$ = new Subject<void>();

  constructor(private vpcService: VPCAnomalyService) {
    this.threats$ = this.vpcService.threats$;
  }

  ngOnInit(): void {
    this.vpcService.fetchThreats({ severity: ['CRITICAL', 'HIGH'] });
    
    // Auto-refresh every 30 seconds
    interval(30000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.vpcService.fetchThreats({ severity: ['CRITICAL', 'HIGH'] });
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  openInvestigation(threat: Threat): void {
    this.selectedThreat = threat;
    this.selectedThreatContext = {
      incident_id: threat.incident_id,
      threat_data: threat,
      user_role: 'security_analyst'
    };
  }

  async isolateResource(threat: Threat): Promise<void> {
    try {
      await this.vpcService.executeAction(threat.incident_id, {
        action_type: 'isolate_instance',
        parameters: {
          instance_id: threat.affected_resources[0]
        }
      });
      
      // Refresh threats after action
      await this.vpcService.fetchThreats();
    } catch (error) {
      console.error('Failed to isolate resource:', error);
    }
  }

  handleAgentMessage(message: string): void {
    console.log('Agent message:', message);
  }
}
```

## Advanced Integration Patterns

### State Management Integration

#### Redux/RTK Query
```javascript
// store/vpcAnomalyApi.js
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const vpcAnomalyApi = createApi({
  reducerPath: 'vpcAnomalyApi',
  baseQuery: fetchBaseQuery({
    baseUrl: 'https://api.vpc-anomaly-detection.com/v1',
    prepareHeaders: (headers, { getState }) => {
      headers.set('authorization', `Bearer ${getState().auth.apiKey}`);
      return headers;
    },
  }),
  tagTypes: ['Threat', 'Investigation', 'Metrics'],
  endpoints: (builder) => ({
    getThreats: builder.query({
      query: (filters) => ({
        url: '/threats',
        params: filters
      }),
      providesTags: ['Threat'],
      // Real-time updates via WebSocket
      onCacheEntryAdded: async (arg, { updateCachedData, cacheDataLoaded, cacheEntryRemoved }) => {
        const ws = new WebSocket('wss://api.vpc-anomaly-detection.com/v1/ws');
        
        try {
          await cacheDataLoaded;
          
          ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'threat_alert') {
              updateCachedData((draft) => {
                draft.threats.unshift(message.data);
              });
            }
          };
        } catch {
          // Handle error
        }
        
        await cacheEntryRemoved;
        ws.close();
      }
    }),
    
    chatWithAgent: builder.mutation({
      query: ({ agentType, message, context }) => ({
        url: '/ai-agents/chat',
        method: 'POST',
        body: { agent_type: agentType, message, context }
      })
    }),
    
    executeAction: builder.mutation({
      query: ({ incidentId, action }) => ({
        url: `/incidents/${incidentId}/actions`,
        method: 'POST',
        body: action
      }),
      invalidatesTags: ['Threat']
    })
  })
});

export const { 
  useGetThreatsQuery, 
  useChatWithAgentMutation, 
  useExecuteActionMutation 
} = vpcAnomalyApi;
```

#### Zustand Store
```javascript
// store/vpcAnomalyStore.js
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { VPCAnomalyClient } from 'vpc-anomaly-detection-sdk';

const client = new VPCAnomalyClient();

export const useVPCAnomalyStore = create(
  subscribeWithSelector((set, get) => ({
    // State
    threats: [],
    selectedThreat: null,
    agentSessions: {},
    wsConnection: null,
    loading: false,
    error: null,

    // Actions
    setThreats: (threats) => set({ threats }),
    
    selectThreat: (threat) => set({ selectedThreat: threat }),
    
    addThreat: (threat) => set((state) => ({
      threats: [threat, ...state.threats]
    })),
    
    fetchThreats: async (filters) => {
      set({ loading: true, error: null });
      try {
        const response = await client.threats.list(filters);
        set({ threats: response.threats, loading: false });
      } catch (error) {
        set({ error, loading: false });
      }
    },
    
    startAgentSession: async (agentType, context) => {
      try {
        const session = await client.aiAgents.startChat(agentType, context);
        set((state) => ({
          agentSessions: {
            ...state.agentSessions,
            [agentType]: {
              sessionId: session.sessionId,
              messages: [],
              isTyping: false
            }
          }
        }));
        return session.sessionId;
      } catch (error) {
        console.error('Failed to start agent session:', error);
      }
    },
    
    sendAgentMessage: async (agentType, message, context) => {
      const session = get().agentSessions[agentType];
      if (!session) return;
      
      // Add user message
      set((state) => ({
        agentSessions: {
          ...state.agentSessions,
          [agentType]: {
            ...session,
            messages: [...session.messages, {
              role: 'user',
              content: message,
              timestamp: new Date().toISOString()
            }],
            isTyping: true
          }
        }
      }));
      
      try {
        const response = await client.aiAgents.chat({
          sessionId: session.sessionId,
          message,
          context
        });
        
        // Add agent response
        set((state) => ({
          agentSessions: {
            ...state.agentSessions,
            [agentType]: {
              ...state.agentSessions[agentType],
              messages: [...state.agentSessions[agentType].messages, {
                role: 'agent',
                content: response.agent_response.analysis,
                analysis: response.agent_response.classification,
                timestamp: response.timestamp
              }],
              isTyping: false
            }
          }
        }));
      } catch (error) {
        set((state) => ({
          agentSessions: {
            ...state.agentSessions,
            [agentType]: {
              ...state.agentSessions[agentType],
              isTyping: false
            }
          }
        }));
      }
    },
    
    initializeWebSocket: () => {
      const ws = new WebSocket('wss://api.vpc-anomaly-detection.com/v1/ws');
      
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'authenticate',
          token: process.env.REACT_APP_VPC_API_KEY
        }));
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'threat_alert') {
          get().addThreat(message.data);
        }
      };
      
      set({ wsConnection: ws });
    }
  }))
);

// Subscribe to threat selection changes
useVPCAnomalyStore.subscribe(
  (state) => state.selectedThreat,
  (selectedThreat) => {
    if (selectedThreat) {
      // Auto-start investigation agent session
      useVPCAnomalyStore.getState().startAgentSession('investigation_agent', {
        incident_id: selectedThreat.incident_id,
        threat_data: selectedThreat
      });
    }
  }
);
```

### Custom Hooks and Utilities

#### React Custom Hooks
```javascript
// hooks/useRealTimeThreats.js
import { useState, useEffect, useCallback } from 'react';
import { useVPCAnomalyStore } from '../store/vpcAnomalyStore';

export function useRealTimeThreats(filters = {}) {
  const { 
    threats, 
    loading, 
    error, 
    fetchThreats, 
    initializeWebSocket 
  } = useVPCAnomalyStore();
  
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchThreats(filters);
    initializeWebSocket();
  }, []);

  useEffect(() => {
    setLastUpdate(new Date());
  }, [threats]);

  const refresh = useCallback(() => {
    fetchThreats(filters);
  }, [filters]);

  return {
    threats,
    loading,
    error,
    lastUpdate,
    refresh
  };
}

// hooks/useAIAgentConversation.js
export function useAIAgentConversation(agentType, autoStart = true) {
  const { 
    agentSessions, 
    startAgentSession, 
    sendAgentMessage 
  } = useVPCAnomalyStore();
  
  const session = agentSessions[agentType];
  
  useEffect(() => {
    if (autoStart && !session) {
      startAgentSession(agentType);
    }
  }, [agentType, autoStart, session]);

  const sendMessage = useCallback((message, context) => {
    return sendAgentMessage(agentType, message, context);
  }, [agentType]);

  return {
    messages: session?.messages || [],
    isTyping: session?.isTyping || false,
    sessionId: session?.sessionId,
    sendMessage
  };
}

// hooks/useNotifications.js
export function useNotifications() {
  const [permission, setPermission] = useState(Notification.permission);

  useEffect(() => {
    if (permission === 'default') {
      Notification.requestPermission().then(setPermission);
    }
  }, []);

  const showThreatNotification = useCallback((threat) => {
    if (permission === 'granted') {
      const notification = new Notification(`${threat.severity} Threat Detected`, {
        body: `${threat.threat_type} from ${threat.source_ip}`,
        icon: '/threat-icon.png',
        tag: threat.incident_id,
        actions: [
          { action: 'investigate', title: 'Investigate' },
          { action: 'isolate', title: 'Isolate' }
        ]
      });

      notification.onclick = () => {
        window.focus();
        // Navigate to threat details
      };
    }
  }, [permission]);

  return { showThreatNotification };
}
```

### Performance Optimization

#### Virtualization for Large Datasets
```jsx
// components/VirtualizedThreatList.jsx
import { FixedSizeList as List } from 'react-window';
import { memo } from 'react';

const ThreatRow = memo(({ index, style, data }) => {
  const threat = data[index];
  
  return (
    <div style={style} className="threat-row">
      <ThreatCard threat={threat} />
    </div>
  );
});

function VirtualizedThreatList({ threats, height = 600 }) {
  return (
    <List
      height={height}
      itemCount={threats.length}
      itemSize={120}
      itemData={threats}
      overscanCount={5}
    >
      {ThreatRow}
    </List>
  );
}
```

#### Memoization and Optimization
```jsx
// components/OptimizedThreatCard.jsx
import { memo, useMemo } from 'react';

const ThreatCard = memo(({ threat, onAction }) => {
  const severityColor = useMemo(() => {
    const colors = {
      CRITICAL: '#dc2626',
      HIGH: '#ea580c',
      MEDIUM: '#d97706',
      LOW: '#65a30d'
    };
    return colors[threat.severity] || '#6b7280';
  }, [threat.severity]);

  const formattedTime = useMemo(() => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(new Date(threat.timestamp));
  }, [threat.timestamp]);

  return (
    <div className="threat-card" style={{ borderLeftColor: severityColor }}>
      <div className="threat-header">
        <span className="threat-type">{threat.threat_type}</span>
        <span className="threat-time">{formattedTime}</span>
      </div>
      <div className="threat-details">
        <p>Source: {threat.source_ip}</p>
        <p>Confidence: {threat.confidence}%</p>
      </div>
      <div className="threat-actions">
        <button onClick={() => onAction('investigate', threat)}>
          Investigate
        </button>
        <button onClick={() => onAction('isolate', threat)}>
          Isolate
        </button>
      </div>
    </div>
  );
});

export default ThreatCard;
```

## Testing Integration

### Unit Testing
```javascript
// __tests__/useVPCAnomaly.test.js
import { renderHook, act } from '@testing-library/react';
import { useVPCAnomaly } from '../hooks/useVPCAnomaly';

// Mock the SDK
jest.mock('vpc-anomaly-detection-sdk', () => ({
  VPCAnomalyClient: jest.fn().mockImplementation(() => ({
    threats: {
      list: jest.fn().mockResolvedValue({
        threats: [
          {
            incident_id: 'test-001',
            threat_type: 'port_scanning',
            severity: 'HIGH'
          }
        ]
      })
    }
  }))
}));

describe('useVPCAnomaly', () => {
  it('should fetch threats successfully', async () => {
    const { result } = renderHook(() => useVPCAnomaly('test-api-key'));

    expect(result.current.loading).toBe(false);
    expect(result.current.threats).toEqual([]);

    await act(async () => {
      await result.current.fetchThreats();
    });

    expect(result.current.threats).toHaveLength(1);
    expect(result.current.threats[0].incident_id).toBe('test-001');
  });
});
```

### Integration Testing
```javascript
// __tests__/SecurityDashboard.integration.test.js
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SecurityDashboard } from '../components/SecurityDashboard';

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  send: jest.fn(),
  close: jest.fn(),
  onopen: null,
  onmessage: null,
  onclose: null
}));

describe('SecurityDashboard Integration', () => {
  it('should display threats and allow interaction', async () => {
    render(<SecurityDashboard />);

    // Wait for threats to load
    await waitFor(() => {
      expect(screen.getByText('Port Scanning')).toBeInTheDocument();
    });

    // Test threat interaction
    const investigateButton = screen.getByText('Investigate');
    await userEvent.click(investigateButton);

    // Verify AI chat opens
    expect(screen.getByText('Threat Classifier Agent')).toBeInTheDocument();
  });
});
```

This comprehensive integration guide provides everything needed to build a modern, responsive web application with AI agent capabilities for the VPC Flow Log Anomaly Detection System.