"""
Correlation State Manager
Manages correlation state across detection instances using ElastiCache.
"""

import json
import redis
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import logging

@dataclass
class CorrelationState:
    entity_key: str
    anomaly_history: List[Dict]
    correlation_context: Dict[str, Any]
    last_updated: datetime
    expiry_time: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'entity_key': self.entity_key,
            'anomaly_history': self.anomaly_history,
            'correlation_context': self.correlation_context,
            'last_updated': self.last_updated.isoformat(),
            'expiry_time': self.expiry_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CorrelationState':
        """Create from dictionary"""
        return cls(
            entity_key=data['entity_key'],
            anomaly_history=data['anomaly_history'],
            correlation_context=data['correlation_context'],
            last_updated=datetime.fromisoformat(data['last_updated']),
            expiry_time=datetime.fromisoformat(data['expiry_time'])
        )

class CorrelationStateManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Redis connection
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0),
            decode_responses=True,
            socket_timeout=config.get('socket_timeout', 5),
            socket_connect_timeout=config.get('connect_timeout', 5),
            retry_on_timeout=True
        )
        
        # State management parameters
        self.state_ttl = config.get('state_ttl', 1800)  # 30 minutes
        self.max_history_size = config.get('max_history_size', 100)
        self.cleanup_interval = config.get('cleanup_interval', 300)  # 5 minutes
        self.last_cleanup = datetime.utcnow()
        
        # Key prefixes
        self.entity_prefix = "correlation:entity:"
        self.global_prefix = "correlation:global:"
        
    def get_entity_correlation_state(self, entity_key: str) -> Optional[CorrelationState]:
        """Get correlation state for specific entity"""
        try:
            state_key = f"{self.entity_prefix}{entity_key}"
            state_data = self.redis_client.get(state_key)
            
            if state_data:
                data = json.loads(state_data)
                return CorrelationState.from_dict(data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get correlation state for {entity_key}: {e}")
            return None
    
    def update_entity_correlation_state(self, entity_key: str, 
                                      anomaly_data: Dict, 
                                      correlation_context: Optional[Dict] = None) -> bool:
        """Update correlation state for entity"""
        try:
            # Get existing state or create new
            state = self.get_entity_correlation_state(entity_key)
            
            if state is None:
                state = CorrelationState(
                    entity_key=entity_key,
                    anomaly_history=[],
                    correlation_context=correlation_context or {},
                    last_updated=datetime.utcnow(),
                    expiry_time=datetime.utcnow() + timedelta(seconds=self.state_ttl)
                )
            
            # Add anomaly to history
            anomaly_entry = {
                'anomaly_id': anomaly_data.get('anomaly_id'),
                'threat_type': anomaly_data.get('threat_type'),
                'confidence_score': anomaly_data.get('confidence_score'),
                'timestamp': datetime.utcnow().isoformat(),
                'source_ip': anomaly_data.get('source_ip'),
                'destination_ip': anomaly_data.get('destination_ip'),
                'destination_port': anomaly_data.get('destination_port')
            }
            
            state.anomaly_history.append(anomaly_entry)
            
            # Limit history size
            if len(state.anomaly_history) > self.max_history_size:
                state.anomaly_history = state.anomaly_history[-self.max_history_size:]
            
            # Update correlation context
            if correlation_context:
                state.correlation_context.update(correlation_context)
            
            # Update timestamps
            state.last_updated = datetime.utcnow()
            state.expiry_time = datetime.utcnow() + timedelta(seconds=self.state_ttl)
            
            # Save to Redis
            state_key = f"{self.entity_prefix}{entity_key}"
            self.redis_client.setex(
                state_key,
                self.state_ttl,
                json.dumps(state.to_dict())
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update correlation state for {entity_key}: {e}")
            return False
    
    def get_related_entities(self, entity_key: str, 
                           time_window: int = 300,
                           threat_types: Optional[Set[str]] = None) -> List[Dict]:
        """Get entities with related anomalies within time window"""
        try:
            related_entities = []
            current_time = datetime.utcnow()
            
            # Get all entity keys
            pattern = f"{self.entity_prefix}*"
            entity_keys = self.redis_client.keys(pattern)
            
            for key in entity_keys:
                if key == f"{self.entity_prefix}{entity_key}":
                    continue  # Skip self
                
                try:
                    state_data = self.redis_client.get(key)
                    if not state_data:
                        continue
                    
                    data = json.loads(state_data)
                    state = CorrelationState.from_dict(data)
                    
                    # Check for recent anomalies
                    recent_anomalies = []
                    for anomaly in state.anomaly_history:
                        anomaly_time = datetime.fromisoformat(anomaly['timestamp'])
                        time_diff = (current_time - anomaly_time).total_seconds()
                        
                        if time_diff <= time_window:
                            if threat_types is None or anomaly['threat_type'] in threat_types:
                                recent_anomalies.append(anomaly)
                    
                    if recent_anomalies:
                        related_entities.append({
                            'entity_key': state.entity_key,
                            'recent_anomalies': recent_anomalies,
                            'correlation_context': state.correlation_context
                        })
                
                except Exception as e:
                    self.logger.warning(f"Failed to process entity {key}: {e}")
                    continue
            
            return related_entities
            
        except Exception as e:
            self.logger.error(f"Failed to get related entities for {entity_key}: {e}")
            return []
    
    def get_global_correlation_metrics(self) -> Dict[str, Any]:
        """Get global correlation metrics"""
        try:
            metrics_key = f"{self.global_prefix}metrics"
            metrics_data = self.redis_client.get(metrics_key)
            
            if metrics_data:
                return json.loads(metrics_data)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get global correlation metrics: {e}")
            return {}
    
    def update_global_correlation_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Update global correlation metrics"""
        try:
            metrics_key = f"{self.global_prefix}metrics"
            
            # Get existing metrics
            existing_metrics = self.get_global_correlation_metrics()
            
            # Update with new metrics
            existing_metrics.update(metrics)
            existing_metrics['last_updated'] = datetime.utcnow().isoformat()
            
            # Save with TTL
            self.redis_client.setex(
                metrics_key,
                3600,  # 1 hour TTL for metrics
                json.dumps(existing_metrics)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update global correlation metrics: {e}")
            return False
    
    def cleanup_expired_states(self) -> int:
        """Clean up expired correlation states"""
        try:
            current_time = datetime.utcnow()
            
            # Check if cleanup is needed
            if (current_time - self.last_cleanup).total_seconds() < self.cleanup_interval:
                return 0
            
            cleaned_count = 0
            pattern = f"{self.entity_prefix}*"
            entity_keys = self.redis_client.keys(pattern)
            
            for key in entity_keys:
                try:
                    state_data = self.redis_client.get(key)
                    if not state_data:
                        continue
                    
                    data = json.loads(state_data)
                    expiry_time = datetime.fromisoformat(data['expiry_time'])
                    
                    if current_time > expiry_time:
                        self.redis_client.delete(key)
                        cleaned_count += 1
                
                except Exception as e:
                    self.logger.warning(f"Failed to process cleanup for {key}: {e}")
                    continue
            
            self.last_cleanup = current_time
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired correlation states")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired states: {e}")
            return 0
    
    def get_correlation_statistics(self) -> Dict[str, Any]:
        """Get correlation state statistics"""
        try:
            stats = {
                'total_entities': 0,
                'active_entities': 0,
                'total_anomalies': 0,
                'threat_type_distribution': {},
                'avg_anomalies_per_entity': 0.0,
                'oldest_state_age': 0,
                'newest_state_age': 0
            }
            
            current_time = datetime.utcnow()
            pattern = f"{self.entity_prefix}*"
            entity_keys = self.redis_client.keys(pattern)
            
            stats['total_entities'] = len(entity_keys)
            
            oldest_time = current_time
            newest_time = datetime.min
            total_anomalies = 0
            threat_counts = {}
            
            for key in entity_keys:
                try:
                    state_data = self.redis_client.get(key)
                    if not state_data:
                        continue
                    
                    data = json.loads(state_data)
                    state = CorrelationState.from_dict(data)
                    
                    # Check if active (recent anomalies)
                    recent_anomalies = [
                        a for a in state.anomaly_history
                        if (current_time - datetime.fromisoformat(a['timestamp'])).total_seconds() <= 3600
                    ]
                    
                    if recent_anomalies:
                        stats['active_entities'] += 1
                    
                    # Count anomalies and threat types
                    total_anomalies += len(state.anomaly_history)
                    
                    for anomaly in state.anomaly_history:
                        threat_type = anomaly['threat_type']
                        threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1
                    
                    # Track state ages
                    if state.last_updated < oldest_time:
                        oldest_time = state.last_updated
                    if state.last_updated > newest_time:
                        newest_time = state.last_updated
                
                except Exception as e:
                    self.logger.warning(f"Failed to process stats for {key}: {e}")
                    continue
            
            stats['total_anomalies'] = total_anomalies
            stats['threat_type_distribution'] = threat_counts
            
            if stats['total_entities'] > 0:
                stats['avg_anomalies_per_entity'] = total_anomalies / stats['total_entities']
            
            if oldest_time != current_time:
                stats['oldest_state_age'] = (current_time - oldest_time).total_seconds()
            
            if newest_time != datetime.min:
                stats['newest_state_age'] = (current_time - newest_time).total_seconds()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get correlation statistics: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False