#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

def test_bedrock_agents():
    """Test Bedrock agent responses directly"""
    print("=== Testing Bedrock Agents ===")
    
    bedrock_agent = boto3.client('bedrock-agent-runtime')
    
    # Test Threat Classifier Agent
    print("1. Testing Threat Classifier Agent...")
    
    test_anomaly = {
        'source_ip': '192.168.1.100',
        'anomaly_type': 'port_scanning',
        'ports_scanned': 25,
        'time_window': '60_seconds',
        'resource_context': {
            'instance_id': 'i-1234567890abcdef0',
            'security_groups': ['sg-web-servers'],
            'tags': {'Environment': 'Production', 'Role': 'WebServer'}
        }
    }
    
    try:
        response = bedrock_agent.invoke_agent(
            agentId='threat-classifier-agent-id',
            agentAliasId='TSTALIASID',
            sessionId='test-session-1',
            inputText=f"Analyze this network anomaly: {json.dumps(test_anomaly)}"
        )
        
        print("   ✅ Threat Classifier Agent responded")
        # Process response stream
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    print(f"   Response: {chunk['bytes'].decode()}")
    except Exception as e:
        print(f"   ❌ Threat Classifier test failed: {e}")
    
    # Test Investigation Agent
    print("2. Testing Investigation Agent...")
    
    critical_threat = {
        'threat_id': 'threat-001',
        'severity': 'CRITICAL',
        'threat_type': 'lateral_movement',
        'source_ip': '10.0.1.50',
        'affected_resources': ['i-1234567890abcdef0', 'i-0987654321fedcba0']
    }
    
    try:
        response = bedrock_agent.invoke_agent(
            agentId='investigation-agent-id',
            agentAliasId='TSTALIASID',
            sessionId='test-session-2',
            inputText=f"Investigate this critical threat: {json.dumps(critical_threat)}"
        )
        
        print("   ✅ Investigation Agent responded")
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    print(f"   Investigation: {chunk['bytes'].decode()}")
    except Exception as e:
        print(f"   ❌ Investigation Agent test failed: {e}")

def test_step_functions():
    """Test Step Functions orchestration"""
    print("3. Testing Step Functions Workflow...")
    
    stepfunctions = boto3.client('stepfunctions')
    
    test_input = {
        'anomaly_id': 'test-anomaly-001',
        'anomaly_data': {
            'source_ip': '192.168.1.100',
            'anomaly_type': 'port_scanning',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat()
        }
    }
    
    try:
        response = stepfunctions.start_execution(
            stateMachineArn='arn:aws:states:us-east-1:123456789012:stateMachine:ThreatDetectionWorkflow',
            name=f'test-execution-{int(datetime.now().timestamp())}',
            input=json.dumps(test_input)
        )
        
        execution_arn = response['executionArn']
        print(f"   ✅ Workflow started: {execution_arn}")
        
        # Check execution status
        import time
        time.sleep(30)  # Wait for execution
        
        status = stepfunctions.describe_execution(executionArn=execution_arn)
        print(f"   Status: {status['status']}")
        
    except Exception as e:
        print(f"   ❌ Step Functions test failed: {e}")

if __name__ == "__main__":
    test_bedrock_agents()
    test_step_functions()