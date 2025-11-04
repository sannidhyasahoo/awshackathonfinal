#!/usr/bin/env python3
import os
import boto3
from aws_cdk import App, Environment

# Load all credentials from environment
aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') 
aws_session_token = os.getenv('AWS_SESSION_TOKEN')
otx_api_key = os.getenv('OTX_API_KEY')
abuseipdb_api_key = os.getenv('ABUSEIPDB_API_KEY')

# Configure AWS session
session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    aws_session_token=aws_session_token,
    region_name=aws_region
)

# Validate credentials
print("=== VPC Flow Log Anomaly Detection System Deployment ===")
print(f"Region: {aws_region}")
print(f"AWS Credentials: {'✅' if aws_secret_key else '❌'}")
print(f"OTX API Key: {'✅' if otx_api_key else '❌'}")
print(f"AbuseIPDB API Key: {'✅' if abuseipdb_api_key else '❌'}")

# CDK App initialization
app = App()
env = Environment(region=aws_region)

if __name__ == "__main__":
    if aws_secret_key and otx_api_key and abuseipdb_api_key:
        print("\n🚀 All credentials validated - proceeding with deployment")
        app.synth()
    else:
        print("\n⚠️ Missing credentials - deployment halted")