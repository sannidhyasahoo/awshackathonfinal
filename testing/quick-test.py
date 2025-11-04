#!/usr/bin/env python3
import boto3
import json
import time
import os
from datetime import datetime

def test_system():
    """Quick system test with synthetic threats"""
    print("=== VPC Flow Log Anomaly Detection System Test ===")
    
    # Configure AWS session with credentials
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    # Test credentials first
    try:
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials validated for account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credential validation failed: {e}")
        print("Please ensure environment variables are set:")
        print("  $Env:AWS_ACCESS_KEY_ID")
        print("  $Env:AWS_SECRET_ACCESS_KEY")
        print("  $Env:AWS_SESSION_TOKEN")
        print("  $Env:AWS_DEFAULT_REGION")
        return
    
    # Test 1: Port Scanning Detection
    print("1. Testing port scanning detection...")
    kinesis = session.client('kinesis')
    
    test_data = {
        'source_ip': '192.168.1.100',
        'dest_ports': list(range(1, 25)),
        'timestamp': datetime.now().isoformat(),
        'test_type': 'port_scanning'
    }
    
    try:
        kinesis.put_record(
            StreamName='vpc-flow-logs-stream',
            Data=json.dumps(test_data),
            PartitionKey='test'
        )
        print("   ✅ Port scan test data sent")
    except Exception as e:
        print(f"   ❌ Failed to send test data: {e}")
    
    # Test 2: Crypto Mining Detection
    print("2. Testing crypto mining detection...")
    mining_data = {
        'source_ip': '10.0.1.50',
        'dest_ip': '45.76.102.45',  # Known mining pool
        'dest_port': 4444,
        'timestamp': datetime.now().isoformat(),
        'test_type': 'crypto_mining'
    }
    
    try:
        kinesis.put_record(
            StreamName='vpc-flow-logs-stream',
            Data=json.dumps(mining_data),
            PartitionKey='test'
        )
        print("   ✅ Crypto mining test data sent")
    except Exception as e:
        print(f"   ❌ Failed to send mining data: {e}")
    
    # Wait for processing
    print("3. Waiting for threat detection (2 minutes)...")
    time.sleep(120)
    
    # Check results
    print("4. Checking detection results...")
    try:
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table('threat-incidents')
        
        response = table.scan(
            FilterExpression='contains(#data, :test)',
            ExpressionAttributeNames={'#data': 'data'},
            ExpressionAttributeValues={':test': 'test_type'}
        )
        
        if response['Items']:
            print(f"   ✅ {len(response['Items'])} threats detected")
            for item in response['Items']:
                print(f"      - {item.get('threat_type', 'Unknown')}: {item.get('severity', 'Unknown')}")
        else:
            print("   ⚠️ No threats detected yet - may need more time")
    except Exception as e:
        print(f"   ❌ Failed to check results: {e}")

if __name__ == "__main__":
    test_system()