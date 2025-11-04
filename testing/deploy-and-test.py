#!/usr/bin/env python3
import boto3
import json
import time
import os
from datetime import datetime

def check_deployment_status():
    """Check if the VPC Flow Log system is deployed"""
    print("=== Checking Deployment Status ===")
    
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    # Check Kinesis streams
    try:
        kinesis = session.client('kinesis')
        streams = kinesis.list_streams()
        vpc_streams = [s for s in streams['StreamNames'] if 'vpc' in s.lower() or 'flow' in s.lower()]
        
        if vpc_streams:
            print(f"✅ Found Kinesis streams: {vpc_streams}")
            return True, vpc_streams[0]
        else:
            print("❌ No VPC Flow Log streams found")
            print(f"Available streams: {streams['StreamNames']}")
            return False, None
    except Exception as e:
        print(f"❌ Failed to check Kinesis: {e}")
        return False, None

def deploy_minimal_infrastructure():
    """Deploy minimal infrastructure for testing"""
    print("=== Deploying Minimal Test Infrastructure ===")
    
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    # Create Kinesis stream for testing
    try:
        kinesis = session.client('kinesis')
        
        print("Creating Kinesis stream 'vpc-flow-logs-stream'...")
        kinesis.create_stream(
            StreamName='vpc-flow-logs-stream',
            ShardCount=1
        )
        
        # Wait for stream to be active
        print("Waiting for stream to become active...")
        waiter = kinesis.get_waiter('stream_exists')
        waiter.wait(StreamName='vpc-flow-logs-stream')
        
        print("✅ Kinesis stream created successfully")
        
    except kinesis.exceptions.ResourceInUseException:
        print("✅ Kinesis stream already exists")
    except Exception as e:
        print(f"❌ Failed to create Kinesis stream: {e}")
        return False
    
    # Create DynamoDB table for testing
    try:
        dynamodb = session.resource('dynamodb')
        
        print("Creating DynamoDB table 'threat-incidents'...")
        table = dynamodb.create_table(
            TableName='threat-incidents',
            KeySchema=[
                {'AttributeName': 'incident_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'incident_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be active
        print("Waiting for table to become active...")
        table.wait_until_exists()
        
        print("✅ DynamoDB table created successfully")
        
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("✅ DynamoDB table already exists")
    except Exception as e:
        print(f"❌ Failed to create DynamoDB table: {e}")
        return False
    
    return True

def test_with_existing_stream():
    """Test with any available Kinesis stream"""
    print("=== Testing with Available Infrastructure ===")
    
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    # Find any available stream or create one
    kinesis = session.client('kinesis')
    streams = kinesis.list_streams()
    
    if streams['StreamNames']:
        stream_name = streams['StreamNames'][0]
        print(f"Using existing stream: {stream_name}")
    else:
        print("No streams available, creating test stream...")
        if not deploy_minimal_infrastructure():
            return
        stream_name = 'vpc-flow-logs-stream'
    
    # Send test data
    test_data = {
        'source_ip': '192.168.1.100',
        'dest_ports': list(range(1, 25)),
        'timestamp': datetime.now().isoformat(),
        'test_type': 'port_scanning'
    }
    
    try:
        response = kinesis.put_record(
            StreamName=stream_name,
            Data=json.dumps(test_data),
            PartitionKey='test'
        )
        print(f"✅ Test data sent to {stream_name}")
        print(f"   Sequence Number: {response['SequenceNumber']}")
        print(f"   Shard ID: {response['ShardId']}")
        
    except Exception as e:
        print(f"❌ Failed to send test data: {e}")

if __name__ == "__main__":
    # Check current deployment status
    deployed, stream_name = check_deployment_status()
    
    if not deployed:
        print("\n🚀 System not deployed. Options:")
        print("1. Deploy minimal infrastructure for testing")
        print("2. Deploy full system first")
        print("3. Run simulation test (no deployment needed)")
        
        choice = input("\nChoose option (1/2/3): ").strip()
        
        if choice == "1":
            if deploy_minimal_infrastructure():
                print("\n✅ Minimal infrastructure deployed")
                test_with_existing_stream()
        elif choice == "2":
            print("\nRun: cd ../deployment && python deploy.py")
        elif choice == "3":
            print("\nRun: python simulate-test.py")
    else:
        print(f"\n✅ System appears to be deployed with stream: {stream_name}")
        test_with_existing_stream()