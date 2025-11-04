"""
Threat Classifier Data Access Tools
Lambda function for ThreatClassifierAgent data access operations
"""

import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
opensearch_client = boto3.client('opensearchserverless')
athena_client = boto3.client('athena')

# Configuration
CONTEXT_TABLE = 'ai-agent-context'
THREAT_INTEL_TABLE = 'threat-intelligence'
BASELINE_BUCKET = 'security-baselines'
OPENSEARCH_ENDPOINT = 'https://threat-intel.us-east-1.aoss.amazonaws.com'

def lambda_handler(event, context):
    """Main Lambda handler for threat classifier data access tools"""
    try:
        function_name = event.get('function')
        parameters = event.get('parameters', {})
        
        if function_name == 'get_resource_baseline':
            return get_resource_baseline(parameters)
        elif function_name == 'check_threat_intel':
            return check_threat_intel(parameters)
        elif function_name == 'get_recent_cloudtrail':
            return get_recent_cloudtrail(parameters)
        elif function_name == 'get_investigation_context':
            return get_investigation_context(parameters)
        elif function_name == 'update_classification_context':
            return update_classification_context(parameters)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown function: {function_name}'})
            }
            
    except Exception as e:
        logger.error(f"Error in threat classifier data access: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_resource_baseline(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Get baseline behavior patterns for a specific resource"""
    resource_id = parameters.get('resource_id')
    timeframe_hours = parameters.get('timeframe_hours', 168)  # Default 7 days
    
    try:
        # Query DynamoDB for historical baseline data
        table = dynamodb.Table('resource-baselines')
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=timeframe_hours)
        
        response = table.query(
            KeyConditionExpression='resource_id = :rid AND #ts BETWEEN :start AND :end',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':rid': resource_id,
                ':start': start_time.isoformat(),
                ':end': end_time.isoformat()
            },
            ScanIndexForward=False,
            Limit=100
        )
        
        baseline_data = response.get('Items', [])
        
        # Calculate baseline metrics
        if baseline_data:
            baseline_summary = calculate_baseline_metrics(baseline_data)
        else:
            baseline_summary = {
                'status': 'no_baseline_data',
                'message': f'No baseline data found for resource {resource_id}',
                'recommendation': 'Treat as new resource, use conservative thresholds'
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'resource_id': resource_id,
                'timeframe_hours': timeframe_hours,
                'baseline_summary': baseline_summary,
                'data_points': len(baseline_data)
            })
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB error getting baseline for {resource_id}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Database error: {e}'})
        }

def check_threat_intel(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Check indicators against threat intelligence feeds"""
    indicators = parameters.get('indicators', [])
    indicator_type = parameters.get('indicator_type', 'ip')
    
    try:
        table = dynamodb.Table(THREAT_INTEL_TABLE)
        threat_matches = []
        
        for indicator in indicators:
            # Query threat intelligence table
            response = table.get_item(
                Key={
                    'ioc_value': indicator,
                    'ioc_type': indicator_type
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                threat_matches.append({
                    'indicator': indicator,
                    'threat_category': item.get('threat_category'),
                    'confidence': item.get('confidence'),
                    'source': item.get('source'),
                    'first_seen': item.get('first_seen'),
                    'last_updated': item.get('last_updated'),
                    'description': item.get('description')
                })
        
        # Calculate overall threat score
        threat_score = calculate_threat_score(threat_matches)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'indicators_checked': len(indicators),
                'threat_matches': threat_matches,
                'threat_score': threat_score,
                'recommendation': get_threat_recommendation(threat_score)
            })
        }
        
    except ClientError as e:
        logger.error(f"Error checking threat intel: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Threat intel lookup failed: {e}'})
        }

def get_recent_cloudtrail(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Get recent CloudTrail API activity for a resource or user"""
    resource_name = parameters.get('resource_name')
    hours_back = parameters.get('hours_back', 24)
    event_types = parameters.get('event_types', [])
    
    try:
        # Build Athena query for CloudTrail data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        query = f"""
        SELECT eventtime, eventname, sourceipaddress, useragent, 
               useridentity, requestparameters, responseelements
        FROM cloudtrail_logs
        WHERE year = '{start_time.year}' 
          AND month = '{start_time.month:02d}'
          AND day = '{start_time.day:02d}'
          AND eventtime >= '{start_time.isoformat()}'
          AND eventtime <= '{end_time.isoformat()}'
        """
        
        # Add resource filter
        if resource_name:
            query += f" AND (useridentity.arn LIKE '%{resource_name}%' OR requestparameters LIKE '%{resource_name}%')"
        
        # Add event type filter
        if event_types:
            event_filter = "', '".join(event_types)
            query += f" AND eventname IN ('{event_filter}')"
        
        query += " ORDER BY eventtime DESC LIMIT 100"
        
        # Execute Athena query
        response = athena_client.start_query_execution(
            QueryString=query,
            ResultConfiguration={
                'OutputLocation': 's3://athena-query-results-bucket/'
            },
            WorkGroup='security-analysis'
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Wait for query completion (simplified for demo)
        # In production, would use async pattern or polling
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'resource_name': resource_name,
                'hours_back': hours_back,
                'query_execution_id': query_execution_id,
                'status': 'query_submitted',
                'message': 'CloudTrail analysis initiated'
            })
        }
        
    except ClientError as e:
        logger.error(f"Error querying CloudTrail: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'CloudTrail query failed: {e}'})
        }

def get_investigation_context(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve existing investigation context and related findings"""
    anomaly_id = parameters.get('anomaly_id')
    
    try:
        table = dynamodb.Table(CONTEXT_TABLE)
        
        # Get global and investigation-specific context
        response = table.query(
            IndexName='anomaly-id-index',
            KeyConditionExpression='anomaly_id = :aid',
            ExpressionAttributeValues={':aid': anomaly_id}
        )
        
        context_items = response.get('Items', [])
        
        # Organize context by level
        context_data = {
            'global_context': [],
            'investigation_context': [],
            'agent_context': []
        }
        
        for item in context_items:
            context_level = item.get('context_level', 'unknown')
            if context_level.startswith('global'):
                context_data['global_context'].append(item)
            elif context_level.startswith('investigation'):
                context_data['investigation_context'].append(item)
            elif context_level.startswith('agent'):
                context_data['agent_context'].append(item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'anomaly_id': anomaly_id,
                'context_data': context_data,
                'total_items': len(context_items)
            })
        }
        
    except ClientError as e:
        logger.error(f"Error getting investigation context: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Context retrieval failed: {e}'})
        }

def update_classification_context(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Update classification context with findings and reasoning"""
    anomaly_id = parameters.get('anomaly_id')
    classification_data = parameters.get('classification_data', {})
    
    try:
        table = dynamodb.Table(CONTEXT_TABLE)
        
        # Create context entry
        context_item = {
            'context_id': f"classification_{anomaly_id}_{int(datetime.utcnow().timestamp())}",
            'anomaly_id': anomaly_id,
            'context_level': 'agent_classification',
            'agent_type': 'threat_classifier',
            'timestamp': datetime.utcnow().isoformat(),
            'classification_data': classification_data,
            'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp())
        }
        
        table.put_item(Item=context_item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'anomaly_id': anomaly_id,
                'context_id': context_item['context_id'],
                'status': 'context_updated'
            })
        }
        
    except ClientError as e:
        logger.error(f"Error updating classification context: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Context update failed: {e}'})
        }

def calculate_baseline_metrics(baseline_data: List[Dict]) -> Dict[str, Any]:
    """Calculate baseline metrics from historical data"""
    if not baseline_data:
        return {'status': 'no_data'}
    
    # Extract key metrics
    connection_counts = [item.get('connection_count', 0) for item in baseline_data]
    unique_destinations = [item.get('unique_destinations', 0) for item in baseline_data]
    data_volumes = [item.get('data_volume_mb', 0) for item in baseline_data]
    
    return {
        'status': 'baseline_available',
        'connection_patterns': {
            'avg_connections': sum(connection_counts) / len(connection_counts),
            'max_connections': max(connection_counts),
            'typical_range': [min(connection_counts), max(connection_counts)]
        },
        'destination_patterns': {
            'avg_destinations': sum(unique_destinations) / len(unique_destinations),
            'max_destinations': max(unique_destinations)
        },
        'data_patterns': {
            'avg_data_volume': sum(data_volumes) / len(data_volumes),
            'max_data_volume': max(data_volumes)
        },
        'data_points': len(baseline_data)
    }

def calculate_threat_score(threat_matches: List[Dict]) -> float:
    """Calculate overall threat score from threat intelligence matches"""
    if not threat_matches:
        return 0.0
    
    total_score = 0.0
    for match in threat_matches:
        confidence = match.get('confidence', 0.5)
        category_weight = {
            'malware': 0.9,
            'botnet': 0.8,
            'phishing': 0.7,
            'suspicious': 0.5,
            'scanning': 0.4
        }.get(match.get('threat_category', 'unknown'), 0.3)
        
        total_score += confidence * category_weight
    
    # Normalize to 0-1 range
    return min(total_score / len(threat_matches), 1.0)

def get_threat_recommendation(threat_score: float) -> str:
    """Get recommendation based on threat score"""
    if threat_score >= 0.8:
        return "HIGH RISK: Strong threat intelligence match, treat as confirmed threat"
    elif threat_score >= 0.6:
        return "MEDIUM RISK: Moderate threat indicators, investigate further"
    elif threat_score >= 0.3:
        return "LOW RISK: Some suspicious indicators, monitor closely"
    else:
        return "MINIMAL RISK: No significant threat intelligence matches"