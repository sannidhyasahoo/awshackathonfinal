# Security Dashboard User Guide

## Overview

The VPC Flow Log Anomaly Detection Dashboard provides a comprehensive real-time view of your network security posture. The interface is designed for security analysts, incident responders, and security operations teams.

## Dashboard Layout

### Main Navigation
- **🏠 Home**: Overview and key metrics
- **🚨 Threats**: Active threat management
- **🔍 Investigation**: AI-powered investigation workspace
- **📊 Analytics**: Historical analysis and trends
- **⚙️ Settings**: Configuration and preferences

## Home Dashboard

### Security Overview Panel
The main dashboard displays critical security metrics at a glance:

```
┌─────────────────────────────────────────────────────────────┐
│ 🛡️ Security Status: HEALTHY        Cost Today: $0.42/$0.75  │
├─────────────────────────────────────────────────────────────┤
│ Active Threats: 12    │ Processed Today: 1.2M logs          │
│ Critical: 2          │ Detection Rate: 1,250/hour           │
│ High: 5             │ False Positives: 2.1%                │
│ Medium: 3           │ Avg Response: 2.3s                   │
│ Low: 2              │ System Health: ✅ All services up     │
└─────────────────────────────────────────────────────────────┘
```

### Real-time Threat Map
Interactive world map showing:
- **Threat origins** by geographic location
- **Attack vectors** with color-coded severity
- **Affected resources** with drill-down capability
- **Live threat feed** with auto-refresh

### Recent Activity Timeline
Chronological view of recent security events:
```
🕐 21:30 - 🚨 CRITICAL: Crypto mining detected from 10.0.1.50
🕐 21:28 - ⚠️ HIGH: Port scanning from 192.168.1.100 
🕐 21:25 - ℹ️ MEDIUM: Tor usage detected from 172.16.1.25
🕐 21:22 - ✅ RESOLVED: DDoS mitigation completed
```

## Threat Management

### Active Threats View
Comprehensive list of current security incidents:

| Incident ID | Time | Type | Severity | Source | Status | Actions |
|-------------|------|------|----------|--------|--------|---------|
| THR-001 | 21:30 | Port Scan | HIGH | 192.168.1.100 | INVESTIGATING | 🔍 📋 🚫 |
| THR-002 | 21:28 | Crypto Mining | CRITICAL | 10.0.1.50 | ACTIVE | 🔍 📋 🚫 |
| THR-003 | 21:25 | Tor Usage | MEDIUM | 172.16.1.25 | MONITORING | 🔍 📋 |

### Threat Detail Panel
Click any threat to view detailed analysis:

```
┌─────────────────────────────────────────────────────────────┐
│ 🚨 Threat Details: THR-001                                  │
├─────────────────────────────────────────────────────────────┤
│ Type: Port Scanning          Confidence: 95%               │
│ Severity: HIGH              Detection: 21:30:15            │
│ Source: 192.168.1.100       Duration: 45 seconds          │
│ Target: i-1234567890abcdef0  Ports: 22,80,443,3389,1433   │
├─────────────────────────────────────────────────────────────┤
│ 🤖 AI Analysis:                                            │
│ "Source IP performed reconnaissance scan targeting common   │
│ service ports. Pattern indicates automated scanning tool.  │
│ Recommend immediate isolation and investigation."           │
├─────────────────────────────────────────────────────────────┤
│ 📋 Recommended Actions:                                     │
│ • Isolate source IP immediately                            │
│ • Review security group configurations                     │
│ • Investigate potential compromise                         │
│ • Check CloudTrail for API activity                       │
└─────────────────────────────────────────────────────────────┘
```

### Quick Actions
One-click response actions available for each threat:
- **🚫 Isolate**: Immediately isolate affected resources
- **📸 Snapshot**: Create forensic snapshots
- **🔍 Investigate**: Launch AI-powered investigation
- **📋 Create Ticket**: Generate incident ticket
- **👥 Notify Team**: Send alerts to response team

## AI Investigation Workspace

### Chat Interface with AI Agents
Interactive conversation with specialized security agents:

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 Threat Classifier Agent                    [ONLINE] ✅   │
├─────────────────────────────────────────────────────────────┤
│ You: Can you analyze the port scanning from 192.168.1.100? │
│                                                             │
│ 🤖 Agent: I'm analyzing the port scanning activity. This    │
│ appears to be reconnaissance with HIGH risk level. The      │
│ source scanned 25 ports in 60 seconds using automated      │
│ tools. Key indicators:                                      │
│                                                             │
│ • High port diversity (22, 80, 443, 3389, 1433, 3306)    │
│ • Rapid scanning pattern (25 ports/60s)                   │
│ • Internal IP suggests potential compromise                 │
│ • Targeting production web servers                         │
│                                                             │
│ Recommended immediate actions:                              │
│ 1. Isolate source IP via security group modification       │
│ 2. Investigate initial compromise vector                   │
│ 3. Review authentication logs for brute force             │
│ 4. Check lateral movement indicators                       │
├─────────────────────────────────────────────────────────────┤
│ Type your message...                            [Send] 📤   │
└─────────────────────────────────────────────────────────────┘
```

### Investigation Timeline
Visual timeline of investigation progress:

```
Investigation: THR-001 Port Scanning Analysis
Progress: ████████████████████░░ 85% Complete

🕐 21:30:00 - Investigation started by Threat Classifier Agent
🕐 21:30:15 - Evidence collection initiated
🕐 21:30:45 - CloudTrail analysis completed (23 events found)
🕐 21:31:20 - Network topology analysis in progress...
🕐 21:31:45 - Vulnerability assessment queued
```

### Evidence Collection
Real-time display of evidence gathered by AI agents:

| Evidence Type | Count | Status | Key Findings |
|---------------|-------|--------|--------------|
| CloudTrail Events | 23 | ✅ Complete | 3 suspicious API calls |
| Network Flows | 156 | ✅ Complete | Lateral movement detected |
| Vulnerability Scans | 3 | 🔄 In Progress | SSH brute force vectors |
| Threat Intel Matches | 2 | ✅ Complete | Known attack patterns |

## Analytics Dashboard

### Threat Trends
Historical analysis with interactive charts:
- **Daily threat volume** over time
- **Threat type distribution** (pie chart)
- **Geographic threat origins** (heat map)
- **Response time metrics** (line graph)
- **Cost optimization trends** (area chart)

### Performance Metrics
System performance monitoring:
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 System Performance (Last 24 Hours)                      │
├─────────────────────────────────────────────────────────────┤
│ Detection Latency:    ████████████████████░ 2.3s avg       │
│ Processing Rate:      ████████████████████░ 1,250/hour     │
│ Agent Response Time:  ████████████████████░ 15s avg        │
│ False Positive Rate:  ██░░░░░░░░░░░░░░░░░░░ 2.1%           │
│ System Availability:  ████████████████████░ 99.95%         │
└─────────────────────────────────────────────────────────────┘
```

### Cost Analysis
Daily cost breakdown and optimization metrics:
- **Bedrock usage**: Token consumption and costs
- **Infrastructure costs**: Kinesis, SageMaker, storage
- **Cost per threat detected**: Efficiency metrics
- **Budget tracking**: Against $0.75/day target

## Settings and Configuration

### Alert Preferences
Customize notification settings:
- **Severity thresholds**: Which threats trigger alerts
- **Notification channels**: Email, Slack, PagerDuty
- **Business hours**: Different rules for off-hours
- **Escalation policies**: Auto-escalation rules

### AI Agent Configuration
Manage AI agent behavior:
- **Response sensitivity**: Adjust confidence thresholds
- **Investigation depth**: Control analysis scope
- **Auto-response rules**: Define automated actions
- **Human approval gates**: Require approval for actions

### Dashboard Customization
Personalize your dashboard:
- **Widget layout**: Drag-and-drop arrangement
- **Refresh intervals**: Auto-update frequency
- **Color themes**: Light/dark mode options
- **Data retention**: Historical data settings

## Mobile Interface

### Responsive Design
The dashboard automatically adapts to mobile devices:
- **Simplified navigation** with bottom tab bar
- **Touch-optimized controls** for threat management
- **Swipe gestures** for quick actions
- **Push notifications** for critical alerts

### Mobile-Specific Features
- **Quick response actions** via notification actions
- **Voice commands** for hands-free operation
- **Offline mode** for viewing cached data
- **Biometric authentication** for secure access

## Keyboard Shortcuts

### Navigation
- `Ctrl + 1`: Home dashboard
- `Ctrl + 2`: Active threats
- `Ctrl + 3`: Investigation workspace
- `Ctrl + 4`: Analytics
- `Ctrl + 5`: Settings

### Threat Management
- `Space`: Quick view threat details
- `Enter`: Open full investigation
- `I`: Isolate resource
- `S`: Create snapshot
- `T`: Create ticket
- `Esc`: Close modals/panels

### AI Chat
- `Ctrl + Enter`: Send message
- `↑/↓`: Navigate message history
- `Ctrl + K`: Clear chat
- `Tab`: Switch between agents

## Accessibility Features

### Screen Reader Support
- **ARIA labels** on all interactive elements
- **Semantic HTML** structure for navigation
- **Keyboard navigation** for all features
- **High contrast mode** for visual impairments

### Internationalization
- **Multi-language support** (English, Spanish, French, German, Japanese)
- **Right-to-left** text support for Arabic/Hebrew
- **Timezone handling** for global teams
- **Localized date/time formats**

## Integration with External Tools

### SIEM Integration
- **Export threat data** to Splunk, QRadar, Sentinel
- **Bi-directional sync** with existing SIEM platforms
- **Custom field mapping** for different SIEM schemas
- **Real-time data streaming** via APIs

### Ticketing Systems
- **Auto-create tickets** in JIRA, ServiceNow, Remedy
- **Sync investigation progress** with ticket updates
- **Attach evidence** and AI analysis to tickets
- **Close loop** when incidents are resolved

### Communication Platforms
- **Slack integration** with interactive buttons
- **Microsoft Teams** notifications and bot commands
- **Email templates** for different stakeholder groups
- **Webhook support** for custom integrations

## Best Practices

### Daily Operations
1. **Start with overview** - Check system health and active threats
2. **Prioritize by severity** - Focus on CRITICAL and HIGH threats first
3. **Use AI assistance** - Leverage agent analysis for complex investigations
4. **Document decisions** - Add notes to investigations for team collaboration
5. **Review trends** - Check analytics for emerging patterns

### Incident Response
1. **Rapid triage** - Use quick actions for immediate response
2. **Gather context** - Review full threat details before acting
3. **Coordinate response** - Use chat features for team collaboration
4. **Track progress** - Monitor investigation timeline and evidence
5. **Post-incident review** - Use root cause analysis for improvements

### Performance Optimization
1. **Customize filters** - Reduce noise with appropriate severity filters
2. **Use bookmarks** - Save frequently accessed views and searches
3. **Optimize refresh rates** - Balance real-time updates with performance
4. **Archive old data** - Maintain dashboard performance with data retention
5. **Monitor costs** - Keep track of daily spending against budget targets