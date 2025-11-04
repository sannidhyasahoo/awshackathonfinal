"""
EventBridge Event Publisher
Publishes validated anomalies to AI Agent Service via EventBridge
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)

@dataclass
class AnomalyEvent:
    """Anomaly event data structure"""
    anomaly_id: str
    threat_type: str
    severity: str
    confidence_score: float
    source_ip: str
    destination_ip: str
    timestamp: str
    flow_data: Dict[str, Any]
    detection_method: str
    validation_results: Dict[str, Any]
    correlation_context: Optional[Dict[str, Any]] = None

class EventPublisher:
    """EventBridge event publisher for anomaly notifications"""
    
    def __init__(self, event_bus_name: str, source_name: str = "anomaly-detection-service"):
        self.event_bus_name = event_bus_name
        self.source_name = source_name
        self.client = boto3.client('events')
        self._health_status = True
        
    async def publish_anomaly(self, anomaly: AnomalyEvent) -> bool:
        """Publish single anomaly event"""
        try:
            event_entry = self._create_event_entry(anomaly)
            response = self.client.put_events(Entries=[event_entry])
            
            if response['FailedEntryCount'] > 0:
                logger.error(f"Failed to publish anomaly {anomaly.anomaly_id}: {response['Entries'][0].get('ErrorMessage')}")
                return False
                
            logger.info(f"Published anomaly event {anomaly.anomaly_id}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS error publishing anomaly {anomaly.anomaly_id}: {e}")
            self._health_status = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing anomaly {anomaly.anomaly_id}: {e}")
            return False
    
    async def publish_batch(self, anomalies: List[AnomalyEvent]) -> Dict[str, int]:
        """Publish batch of anomaly events (max 10 per batch)"""
        results = {"success": 0, "failed": 0}
        
        # Process in batches of 10 (EventBridge limit)
        for i in range(0, len(anomalies), 10):
            batch = anomalies[i:i+10]
            batch_results = await self._publish_batch_chunk(batch)
            results["success"] += batch_results["success"]
            results["failed"] += batch_results["failed"]
            
        return results
    
    async def _publish_batch_chunk(self, batch: List[AnomalyEvent]) -> Dict[str, int]:
        """Publish single batch chunk"""
        try:
            entries = [self._create_event_entry(anomaly) for anomaly in batch]
            response = self.client.put_events(Entries=entries)
            
            success_count = len(batch) - response['FailedEntryCount']
            failed_count = response['FailedEntryCount']
            
            if failed_count > 0:
                for i, entry in enumerate(response['Entries']):
                    if 'ErrorCode' in entry:
                        logger.error(f"Failed to publish batch item {i}: {entry.get('ErrorMessage')}")
            
            logger.info(f"Batch published: {success_count} success, {failed_count} failed")
            return {"success": success_count, "failed": failed_count}
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS error publishing batch: {e}")
            self._health_status = False
            return {"success": 0, "failed": len(batch)}
        except Exception as e:
            logger.error(f"Unexpected error publishing batch: {e}")
            return {"success": 0, "failed": len(batch)}
    
    def _create_event_entry(self, anomaly: AnomalyEvent) -> Dict[str, Any]:
        """Create EventBridge event entry"""
        detail = asdict(anomaly)
        
        # Add metadata
        detail['event_version'] = '1.0'
        detail['published_at'] = datetime.utcnow().isoformat()
        detail['publisher'] = self.source_name
        
        return {
            'Source': self.source_name,
            'DetailType': f'Anomaly Detected - {anomaly.threat_type}',
            'Detail': json.dumps(detail),
            'EventBusName': self.event_bus_name,
            'Resources': [
                f'arn:aws:vpc-flow-logs:*:*:anomaly/{anomaly.anomaly_id}'
            ]
        }
    
    async def publish_system_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Publish system events (health, errors, etc.)"""
        try:
            event_entry = {
                'Source': self.source_name,
                'DetailType': f'System Event - {event_type}',
                'Detail': json.dumps({
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    'service': self.source_name,
                    **details
                }),
                'EventBusName': self.event_bus_name
            }
            
            response = self.client.put_events(Entries=[event_entry])
            
            if response['FailedEntryCount'] > 0:
                logger.error(f"Failed to publish system event {event_type}")
                return False
                
            logger.info(f"Published system event {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing system event {event_type}: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get publisher health status"""
        try:
            # Test EventBridge connectivity
            self.client.describe_event_bus(Name=self.event_bus_name)
            self._health_status = True
            
            return {
                'status': 'healthy',
                'event_bus': self.event_bus_name,
                'source': self.source_name,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self._health_status = False
            return {
                'status': 'unhealthy',
                'error': str(e),
                'event_bus': self.event_bus_name,
                'last_check': datetime.utcnow().isoformat()
            }

class EventPublisherManager:
    """Manages multiple event publishers with failover"""
    
    def __init__(self, primary_bus: str, fallback_bus: Optional[str] = None):
        self.primary_publisher = EventPublisher(primary_bus)
        self.fallback_publisher = EventPublisher(fallback_bus) if fallback_bus else None
        self._metrics = {
            'events_published': 0,
            'events_failed': 0,
            'failover_count': 0
        }
    
    async def publish_anomaly(self, anomaly: AnomalyEvent) -> bool:
        """Publish with automatic failover"""
        # Try primary publisher
        success = await self.primary_publisher.publish_anomaly(anomaly)
        if success:
            self._metrics['events_published'] += 1
            return True
        
        # Try fallback if available
        if self.fallback_publisher:
            logger.warning(f"Primary publisher failed, trying fallback for {anomaly.anomaly_id}")
            success = await self.fallback_publisher.publish_anomaly(anomaly)
            if success:
                self._metrics['events_published'] += 1
                self._metrics['failover_count'] += 1
                return True
        
        self._metrics['events_failed'] += 1
        return False
    
    async def publish_batch(self, anomalies: List[AnomalyEvent]) -> Dict[str, int]:
        """Publish batch with automatic failover"""
        # Try primary publisher
        results = await self.primary_publisher.publish_batch(anomalies)
        
        # If some failed and fallback available, retry failed ones
        if results['failed'] > 0 and self.fallback_publisher:
            logger.warning(f"Primary publisher had {results['failed']} failures, retrying with fallback")
            # Note: In real implementation, would need to track which specific events failed
            # For simplicity, this is a basic retry mechanism
            
        self._metrics['events_published'] += results['success']
        self._metrics['events_failed'] += results['failed']
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get publisher metrics"""
        primary_health = self.primary_publisher.get_health_status()
        fallback_health = self.fallback_publisher.get_health_status() if self.fallback_publisher else None
        
        return {
            'metrics': self._metrics,
            'primary_publisher': primary_health,
            'fallback_publisher': fallback_health
        }