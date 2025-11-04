#!/usr/bin/env python3
"""
Quick deployment of minimal infrastructure for testing
Creates only the essential resources needed to test the system
"""
import boto3
import json
import os
import time

def quick_deploy():
    """Deploy minimal infrastructure for immediate testing"""
    print("=== Quick Deploy for Testing ===")
    
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    resources_created = []
    
    # 1. Create Kinesis Stream
    print("1. Creating Kinesis stream...")
    try:
        kinesis = session.client('kinesis')
        kinesis.create_stream(
            StreamName='vpc-flow-logs-stream',
            ShardCount=1
        )
        print("   ✅ Kinesis stream 'vpc-flow-logs-stream' created")
        resources_created.append("Kinesis Stream: vpc-flow-logs-stream")
        
        # Wait for active
        print("   Waiting for stream to become active...")
        waiter = kinesis.get_waiter('stream_exists')
        waiter.wait(StreamName='vpc-flow-logs-stream', WaiterConfig={'Delay': 10, 'MaxAttempts': 30})
        
    except kinesis.exceptions.ResourceInUseException:
        print("   ✅ Kinesis stream already exists")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # 2. Create DynamoDB Table
    print("2. Creating DynamoDB table...")
    try:
        dynamodb = session.resource('dynamodb')
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
        print("   ✅ DynamoDB table 'threat-incidents' created")
        resources_created.append("DynamoDB Table: threat-incidents")
        
        # Wait for active
        print("   Waiting for table to become active...")
        table.wait_until_exists()
        
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("   ✅ DynamoDB table already exists")
        else:
            print(f"   ❌ Failed: {e}")
    
    # 3. Create Lambda function for processing (simplified)
    print("3. Creating Lambda function...")
    try:
        lambda_client = session.client('lambda')
        
        # Simple Lambda code for threat detection
        lambda_code = '''
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('threat-incidents')
    
    for record in event['Records']:
        # Decode Kinesis data
        data = json.loads(record['kinesis']['data'])
        
        # Simple threat detection logic
        threat_detected = False
        threat_type = "unknown"
        severity = "LOW"
        
        if 'dest_ports' in data and len(data['dest_ports']) > 10:
            threat_detected = True
            threat_type = "port_scanning"
            severity = "HIGH"
        elif 'dest_port' in data and data['dest_port'] in [4444, 3333, 9999]:
            threat_detected = True
            threat_type = "crypto_mining"
            severity = "CRITICAL"
        
        if threat_detected:
            # Store in DynamoDB
            table.put_item(Item={
                'incident_id': f"test-{int(datetime.now().timestamp())}",
                'timestamp': datetime.now().isoformat(),
                'threat_type': threat_type,
                'severity': severity,
                'source_data': data
            })
    
    return {'statusCode': 200, 'body': 'Processed'}
'''
        
        # Create deployment package
        import zipfile
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zip_file:
                zip_file.writestr('lambda_function.py', lambda_code)
            
            with open(tmp.name, 'rb') as zip_data:
                lambda_client.create_function(
                    FunctionName='vpc-threat-detector',
                    Runtime='python3.9',
                    Role=f'arn:aws:iam::{session.client("sts").get_caller_identity()["Account"]}:role/lambda-execution-role',
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_data.read()},
                    Description='Simple threat detector for testing'
                )
        
        print("   ✅ Lambda function 'vpc-threat-detector' created")
        resources_created.append("Lambda Function: vpc-threat-detector")
        
    except Exception as e:
        print(f"   ⚠️ Lambda creation skipped: {e}")
        print("   (This is optional for basic testing)")
    
    print("\n=== Deployment Complete ===")
    print("Resources created:")
    for resource in resources_created:
        print(f"  ✅ {resource}")
    
    print("\nYou can now run:")
    print("  python quick-test.py")
    
    return True

if __name__ == "__main__":
    quick_deploy()