# Additional Credentials Required

## AWS Credentials ✅
- **AWS_DEFAULT_REGION**: us-east-1 ✅
- **AWS_SECRET_ACCESS_KEY**: Provided ✅  
- **AWS_SESSION_TOKEN**: Provided ✅

## Required Third-Party API Keys

### 1. Threat Intelligence Feeds
- **AlienVault OTX API Key**: Required for threat intelligence enrichment
  - Sign up at: https://otx.alienvault.com/
  - Generate API key in account settings
  - Environment variable: `OTX_API_KEY`

- **AbuseIPDB API Key**: Required for IP reputation checks
  - Sign up at: https://www.abuseipdb.com/
  - Generate API key in account dashboard
  - Environment variable: `ABUSEIPDB_API_KEY`

### 2. Notification Services (Optional)
- **Slack Webhook URL**: For alert notifications
  - Create Slack app and webhook
  - Environment variable: `SLACK_WEBHOOK_URL`

- **PagerDuty Integration Key**: For critical alerts
  - Create PagerDuty service integration
  - Environment variable: `PAGERDUTY_INTEGRATION_KEY`

- **JIRA API Token**: For incident ticket creation
  - Generate in JIRA account settings
  - Environment variables: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`

### 3. System Configuration
- **Bedrock Model Access**: Ensure Claude 3.5 Sonnet/Haiku access enabled in AWS Bedrock console
- **VPC Flow Logs**: Enable VPC Flow Logs in target VPCs
- **Service Quotas**: Request increases for Bedrock, Kinesis, SageMaker if needed

## Deployment Command
```bash
# Set AWS credentials
$Env:AWS_DEFAULT_REGION="us-east-1"
$Env:AWS_SECRET_ACCESS_KEY="<your_secret_key>"
$Env:AWS_SESSION_TOKEN="<your_session_token>"

# Set optional API keys
$Env:OTX_API_KEY="<your_otx_key>"
$Env:ABUSEIPDB_API_KEY="<your_abuseipdb_key>"

# Deploy system
cd deployment
python deploy.py
```

## Minimum Required for Basic Deployment
- ✅ AWS credentials (provided)
- ⚠️ OTX_API_KEY (recommended for threat intelligence)
- ⚠️ ABUSEIPDB_API_KEY (recommended for IP reputation)

System will deploy with AWS credentials only, but threat intelligence features require API keys.