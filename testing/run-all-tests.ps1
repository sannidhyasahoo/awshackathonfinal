# Complete Testing Suite for VPC Flow Log Anomaly Detection System

Write-Host "=== VPC Flow Log Anomaly Detection System - Complete Testing ===" -ForegroundColor Green
Write-Host ""

# Test 1: Quick System Test
Write-Host "🧪 Test 1: Quick System Functionality Test" -ForegroundColor Cyan
Write-Host "Testing basic threat detection with synthetic data..." -ForegroundColor Yellow
python quick-test.py
Write-Host ""

# Test 2: Bedrock Agents Test  
Write-Host "🤖 Test 2: Bedrock Agents Response Test" -ForegroundColor Cyan
Write-Host "Testing AI agent classification and investigation..." -ForegroundColor Yellow
python test-agents.py
Write-Host ""

# Test 3: Load Test
Write-Host "⚡ Test 3: Performance Load Test" -ForegroundColor Cyan
Write-Host "Testing system under high-volume load..." -ForegroundColor Yellow
python load-test.py
Write-Host ""

# Test 4: Cost Monitoring
Write-Host "💰 Test 4: Cost Validation" -ForegroundColor Cyan
Write-Host "Checking cost optimization targets..." -ForegroundColor Yellow
aws ce get-cost-and-usage --time-period Start=2024-12-19,End=2024-12-20 --granularity DAILY --metrics BlendedCost --group-by Type=DIMENSION,Key=SERVICE
Write-Host ""

# Test 5: Real-time Monitoring
Write-Host "📊 Test 5: Real-time Monitoring Check" -ForegroundColor Cyan
Write-Host "Validating CloudWatch metrics and alerts..." -ForegroundColor Yellow
aws cloudwatch get-metric-statistics --namespace "VPCFlowLogAnomalyDetection" --metric-name "ThreatsDetected" --start-time 2024-12-19T00:00:00Z --end-time 2024-12-19T23:59:59Z --period 3600 --statistics Sum
Write-Host ""

Write-Host "✅ All tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review CloudWatch dashboards for metrics" -ForegroundColor White
Write-Host "2. Check DynamoDB tables for threat incidents" -ForegroundColor White  
Write-Host "3. Validate cost targets in AWS Cost Explorer" -ForegroundColor White
Write-Host "4. Monitor agent responses in Bedrock console" -ForegroundColor White