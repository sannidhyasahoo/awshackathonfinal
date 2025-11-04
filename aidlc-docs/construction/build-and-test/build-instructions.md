# Build Instructions - VPC Flow Log Anomaly Detection System

## Prerequisites

### Build Tools and Versions
- **AWS CDK**: v2.100.0 or later
- **Python**: 3.11 or later
- **Node.js**: 18.x or later (for CDK)
- **Docker**: 20.10 or later
- **AWS CLI**: v2.13.0 or later

### Dependencies
- **Python Packages**: boto3, aws-cdk-lib, constructs, pytest, moto
- **AWS Services**: Bedrock, Lambda, DynamoDB, OpenSearch, S3, Kinesis, SageMaker
- **Development Tools**: pytest, black, flake8, mypy

### Environment Variables
```bash
export AWS_ACCOUNT_ID=<your-account-id>
export AWS_REGION=us-east-1
export ENVIRONMENT=development
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION
```

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL2
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Disk Space**: 10GB free space
- **Network**: Internet access for AWS services and package downloads

## Build Steps

### 1. Install Dependencies

#### Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Install Node.js Dependencies (for CDK)
```bash
npm install -g aws-cdk@latest
npm install
```

#### Install AWS CLI and Configure
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
```

### 2. Configure Environment

#### Set Up AWS Credentials
```bash
# Option 1: AWS CLI configuration
aws configure set aws_access_key_id <your-access-key>
aws configure set aws_secret_access_key <your-secret-key>
aws configure set region us-east-1

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
export AWS_DEFAULT_REGION=us-east-1
```

#### Bootstrap CDK (First Time Only)
```bash
cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION
```

#### Verify AWS Access
```bash
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1
```

### 3. Build All Units

#### Unit 1: Data Ingestion Service
```bash
cd aidlc-docs/construction/data-ingestion-service/code
python -m py_compile src/**/*.py
pytest tests/unit/ --verbose
```

#### Unit 2: Anomaly Detection Service
```bash
cd aidlc-docs/construction/anomaly-detection-service/code
python -m py_compile src/**/*.py
pytest tests/unit/ --verbose
```

#### Unit 3: AI Agent Service
```bash
cd aidlc-docs/construction/ai-agent-service/code
python -m py_compile business-logic/*.py
python -m py_compile tools/**/*.py
python -m py_compile infrastructure/**/*.py
```

#### Build CDK Infrastructure
```bash
cd aidlc-docs/construction/ai-agent-service/code/deployment/cdk
cdk synth --all
cdk diff --all
```

#### Package Lambda Functions
```bash
# Package data access tools
cd tools/data-access
zip -r ../../deployment/lambda-packages/data-access-tools.zip .

# Package business logic
cd ../../business-logic
zip -r ../deployment/lambda-packages/business-logic.zip .

# Package infrastructure components
cd ../infrastructure
zip -r ../deployment/lambda-packages/infrastructure.zip .
```

### 4. Verify Build Success

#### Expected Output
- **Python Compilation**: No syntax errors, all .py files compile successfully
- **CDK Synthesis**: CloudFormation templates generated without errors
- **Lambda Packages**: ZIP files created in deployment/lambda-packages/
- **Unit Tests**: All unit tests pass with >80% coverage

#### Build Artifacts
```
deployment/
├── lambda-packages/
│   ├── data-access-tools.zip
│   ├── business-logic.zip
│   └── infrastructure.zip
├── cdk/
│   └── cdk.out/
│       ├── AIAgentServiceStack.template.json
│       ├── DataIngestionStack.template.json
│       └── AnomalyDetectionStack.template.json
└── cloudformation/
    └── generated-templates/
```

#### Common Warnings (Acceptable)
- CDK version compatibility warnings
- Python deprecation warnings for non-critical features
- AWS service quota warnings (informational)

## Troubleshooting

### Build Fails with Dependency Errors

**Cause**: Missing or incompatible Python packages
**Solution**:
```bash
# Clear pip cache and reinstall
pip cache purge
pip uninstall -r requirements.txt -y
pip install -r requirements.txt --no-cache-dir

# Check for conflicting packages
pip check
```

### Build Fails with AWS Permission Errors

**Cause**: Insufficient AWS permissions for CDK or Bedrock
**Solution**:
```bash
# Verify required permissions
aws iam get-user
aws bedrock list-foundation-models --region us-east-1

# Check CDK bootstrap status
cdk doctor
```

### Build Fails with Compilation Errors

**Cause**: Python syntax errors or import issues
**Solution**:
```bash
# Run syntax check
python -m py_compile src/**/*.py

# Check imports
python -c "import boto3; import aws_cdk; print('Imports successful')"

# Run linting
flake8 src/ --max-line-length=100
black src/ --check
```

### CDK Synthesis Fails

**Cause**: Invalid CDK constructs or missing dependencies
**Solution**:
```bash
# Check CDK version compatibility
cdk --version
npm list aws-cdk-lib

# Validate CDK app
cdk ls
cdk synth --verbose

# Check for circular dependencies
cdk diff --verbose
```

### Lambda Packaging Fails

**Cause**: Missing files or permission issues
**Solution**:
```bash
# Check file permissions
ls -la tools/data-access/
chmod +x tools/data-access/*.py

# Verify all required files are present
find tools/ -name "*.py" -type f
find infrastructure/ -name "*.py" -type f

# Create packages with verbose output
zip -r -v deployment/lambda-packages/data-access-tools.zip tools/data-access/
```

## Build Validation Checklist

- [ ] All Python files compile without syntax errors
- [ ] All unit tests pass with >80% coverage
- [ ] CDK synthesis completes successfully
- [ ] Lambda packages created and contain all required files
- [ ] AWS credentials configured and verified
- [ ] Required AWS services accessible (Bedrock, Lambda, DynamoDB)
- [ ] No critical security vulnerabilities in dependencies
- [ ] Build artifacts generated in expected locations

## Next Steps

After successful build:
1. Proceed to unit test execution
2. Run integration tests
3. Execute performance tests
4. Deploy to development environment for validation