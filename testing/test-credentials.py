#!/usr/bin/env python3
import boto3
import os

def test_credentials():
    """Test AWS credentials and basic connectivity"""
    print("=== AWS Credentials Test ===")
    
    # Check environment variables
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') 
    aws_session_token = os.getenv('AWS_SESSION_TOKEN')
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    print(f"AWS_ACCESS_KEY_ID: {'Set' if aws_access_key else 'Missing'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'Set' if aws_secret_key else 'Missing'}")
    print(f"AWS_SESSION_TOKEN: {'Set' if aws_session_token else 'Missing'}")
    print(f"AWS_DEFAULT_REGION: {aws_region}")
    print()
    
    if not all([aws_access_key, aws_secret_key, aws_session_token]):
        print("❌ Missing required AWS credentials")
        print("Run these commands first:")
        print('$Env:AWS_ACCESS_KEY_ID="your_access_key"')
        print('$Env:AWS_SECRET_ACCESS_KEY="your_secret_key"')
        print('$Env:AWS_SESSION_TOKEN="your_session_token"')
        print('$Env:AWS_DEFAULT_REGION="us-east-1"')
        return False
    
    # Test AWS connection
    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            aws_session_token=aws_session_token,
            region_name=aws_region
        )
        
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ AWS Connection Successful")
        print(f"Account ID: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}")
        print(f"Region: {aws_region}")
        
        # Test service access
        print("\nTesting service access...")
        
        # Test Kinesis
        try:
            kinesis = session.client('kinesis')
            streams = kinesis.list_streams(Limit=1)
            print("✅ Kinesis access: OK")
        except Exception as e:
            print(f"⚠️ Kinesis access: {e}")
        
        # Test DynamoDB
        try:
            dynamodb = session.client('dynamodb')
            tables = dynamodb.list_tables()
            print("✅ DynamoDB access: OK")
        except Exception as e:
            print(f"⚠️ DynamoDB access: {e}")
        
        # Test Bedrock
        try:
            bedrock = session.client('bedrock')
            models = bedrock.list_foundation_models()
            print("✅ Bedrock access: OK")
        except Exception as e:
            print(f"⚠️ Bedrock access: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS Connection Failed: {e}")
        return False

if __name__ == "__main__":
    test_credentials()