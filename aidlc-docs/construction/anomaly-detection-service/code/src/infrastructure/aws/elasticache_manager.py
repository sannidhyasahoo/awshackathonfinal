"""
ElastiCache Correlation State Manager
Manages distributed correlation state using Amazon ElastiCache Redis.
"""

import redis
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import logging
import boto3

@dataclass
class CacheClusterInfo:
    cluster_id: str
    endpoint: str
    port: int
    status: str
    node_count: int
    cache_node_type: str

class ElastiCacheManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # ElastiCache configuration
        self.cluster_id = config.get('cluster_id', 'anomaly-correlation-cache')
        self.region = config.get('region', 'us-east-1')
        
        # AWS ElastiCache client for management operations
        self.elasticache = boto3.client('elasticache', region_name=self.region)
        
        # Redis connection configuration
        self.redis_config = {
            'host': config.get('redis_host'),
            'port': config.get('redis_port', 6379),
            'db': config.get('redis_db', 0),
            'decode_responses': True,
            'socket_timeout': config.get('socket_timeout', 5),
            'socket_connect_timeout': config.get('connect_timeout', 5),
            'retry_on_timeout': True,
            'health_check_interval': 30
        }
        
        # Connection pool
        self.connection_pool = None
        self.redis_client = None
        
        # Cache configuration
        self.default_ttl = config.get('default_ttl', 1800)  # 30 minutes
        self.max_connections = config.get('max_connections', 50)
        
        # Key prefixes for organization
        self.key_prefixes = {
            'correlation': 'corr:',
            'entity': 'entity:',
            'metrics': 'metrics:',
            'config': 'config:'
        }
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection with connection pooling"""
        try:
            if not self.redis_config['host']:
                # Auto-discover endpoint if not provided
                self.redis_config['host'] = self._discover_cluster_endpoint()
            
            # Create connection pool
            self.connection_pool = redis.ConnectionPool(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                decode_responses=self.redis_config['decode_responses'],
                socket_timeout=self.redis_config['socket_timeout'],
                socket_connect_timeout=self.redis_config['connect_timeout'],
                retry_on_timeout=self.redis_config['retry_on_timeout'],
                health_check_interval=self.redis_config['health_check_interval'],
                max_connections=self.max_connections
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            self.redis_client.ping()
            
            self.logger.info(f"ElastiCache connection initialized: {self.redis_config['host']}:{self.redis_config['port']}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ElastiCache connection: {e}")
            raise e
    
    def _discover_cluster_endpoint(self) -> str:
        """Auto-discover ElastiCache cluster endpoint"""
        try:
            response = self.elasticache.describe_cache_clusters(
                CacheClusterId=self.cluster_id,
                ShowCacheNodeInfo=True
            )
            
            clusters = response.get('CacheClusters', [])
            if clusters:
                cluster = clusters[0]
                if cluster['CacheClusterStatus'] == 'available':
                    # For Redis cluster mode disabled
                    if cluster.get('CacheNodes'):
                        endpoint = cluster['CacheNodes'][0]['Endpoint']['Address']
                        self.logger.info(f"Discovered cluster endpoint: {endpoint}")
                        return endpoint
                    
                    # For Redis cluster mode enabled
                    if cluster.get('ConfigurationEndpoint'):
                        endpoint = cluster['ConfigurationEndpoint']['Address']
                        self.logger.info(f"Discovered configuration endpoint: {endpoint}")
                        return endpoint
            
            raise Exception(f"No available endpoint found for cluster {self.cluster_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to discover cluster endpoint: {e}")
            raise e
    
    def set_correlation_state(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set correlation state with optional TTL"""
        try:
            full_key = f"{self.key_prefixes['correlation']}{key}"
            serialized_data = json.dumps(data, default=str)
            
            if ttl is None:
                ttl = self.default_ttl
            
            result = self.redis_client.setex(full_key, ttl, serialized_data)
            
            self.logger.debug(f"Set correlation state: {key} (TTL: {ttl}s)")
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to set correlation state for {key}: {e}")
            return False
    
    def get_correlation_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get correlation state by key"""
        try:
            full_key = f"{self.key_prefixes['correlation']}{key}"
            data = self.redis_client.get(full_key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get correlation state for {key}: {e}")
            return None
    
    def delete_correlation_state(self, key: str) -> bool:
        """Delete correlation state"""
        try:
            full_key = f"{self.key_prefixes['correlation']}{key}"
            result = self.redis_client.delete(full_key)
            
            self.logger.debug(f"Deleted correlation state: {key}")
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to delete correlation state for {key}: {e}")
            return False
    
    def get_correlation_keys(self, pattern: str = "*") -> List[str]:
        """Get correlation keys matching pattern"""
        try:
            full_pattern = f"{self.key_prefixes['correlation']}{pattern}"
            keys = self.redis_client.keys(full_pattern)
            
            # Remove prefix from keys
            prefix_len = len(self.key_prefixes['correlation'])
            return [key[prefix_len:] for key in keys]
            
        except Exception as e:
            self.logger.error(f"Failed to get correlation keys: {e}")
            return []
    
    def set_entity_state(self, entity_id: str, state: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set entity-specific state"""
        try:
            full_key = f"{self.key_prefixes['entity']}{entity_id}"
            serialized_state = json.dumps(state, default=str)
            
            if ttl is None:
                ttl = self.default_ttl
            
            result = self.redis_client.setex(full_key, ttl, serialized_state)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to set entity state for {entity_id}: {e}")
            return False
    
    def get_entity_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity-specific state"""
        try:
            full_key = f"{self.key_prefixes['entity']}{entity_id}"
            data = self.redis_client.get(full_key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get entity state for {entity_id}: {e}")
            return None
    
    def increment_counter(self, key: str, increment: int = 1, ttl: Optional[int] = None) -> int:
        """Increment counter with optional TTL"""
        try:
            full_key = f"{self.key_prefixes['metrics']}{key}"
            
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.incr(full_key, increment)
            
            if ttl:
                pipe.expire(full_key, ttl)
            
            results = pipe.execute()
            return results[0]
            
        except Exception as e:
            self.logger.error(f"Failed to increment counter {key}: {e}")
            return 0
    
    def get_counter(self, key: str) -> int:
        """Get counter value"""
        try:
            full_key = f"{self.key_prefixes['metrics']}{key}"
            value = self.redis_client.get(full_key)
            
            return int(value) if value else 0
            
        except Exception as e:
            self.logger.error(f"Failed to get counter {key}: {e}")
            return 0
    
    def set_configuration(self, config_key: str, config_value: Any, ttl: Optional[int] = None) -> bool:
        """Set configuration value"""
        try:
            full_key = f"{self.key_prefixes['config']}{config_key}"
            serialized_value = json.dumps(config_value, default=str)
            
            if ttl:
                result = self.redis_client.setex(full_key, ttl, serialized_value)
            else:
                result = self.redis_client.set(full_key, serialized_value)
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to set configuration {config_key}: {e}")
            return False
    
    def get_configuration(self, config_key: str, default_value: Any = None) -> Any:
        """Get configuration value"""
        try:
            full_key = f"{self.key_prefixes['config']}{config_key}"
            data = self.redis_client.get(full_key)
            
            if data:
                return json.loads(data)
            
            return default_value
            
        except Exception as e:
            self.logger.error(f"Failed to get configuration {config_key}: {e}")
            return default_value
    
    def cleanup_expired_keys(self, pattern: str = "*", max_age_seconds: int = 3600) -> int:
        """Clean up expired keys older than max_age_seconds"""
        try:
            cleaned_count = 0
            current_time = time.time()
            
            for prefix in self.key_prefixes.values():
                full_pattern = f"{prefix}{pattern}"
                keys = self.redis_client.keys(full_pattern)
                
                for key in keys:
                    try:
                        # Check key TTL
                        ttl = self.redis_client.ttl(key)
                        
                        # If key has no TTL (-1) or is expired (-2), check last modified time
                        if ttl == -1:
                            # Key exists but has no TTL, check if it's old
                            key_info = self.redis_client.object('IDLETIME', key)
                            if key_info and key_info > max_age_seconds:
                                self.redis_client.delete(key)
                                cleaned_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to check key {key}: {e}")
                        continue
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired keys")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired keys: {e}")
            return 0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics"""
        try:
            info = self.redis_client.info()
            
            stats = {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
            
            # Calculate hit rate
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            total_requests = hits + misses
            
            if total_requests > 0:
                stats['hit_rate'] = hits / total_requests
            else:
                stats['hit_rate'] = 0.0
            
            # Get key counts by prefix
            stats['key_counts'] = {}
            for prefix_name, prefix in self.key_prefixes.items():
                keys = self.redis_client.keys(f"{prefix}*")
                stats['key_counts'][prefix_name] = len(keys)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on ElastiCache connection"""
        health_status = {
            'healthy': False,
            'response_time': None,
            'error': None,
            'cluster_info': None
        }
        
        try:
            # Test Redis connection
            start_time = time.time()
            self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            health_status['healthy'] = True
            health_status['response_time'] = response_time
            
            # Get cluster information
            try:
                cluster_info = self._get_cluster_info()
                health_status['cluster_info'] = cluster_info
            except Exception as e:
                self.logger.warning(f"Failed to get cluster info: {e}")
            
        except Exception as e:
            health_status['error'] = str(e)
            self.logger.error(f"ElastiCache health check failed: {e}")
        
        return health_status
    
    def _get_cluster_info(self) -> Dict[str, Any]:
        """Get ElastiCache cluster information"""
        try:
            response = self.elasticache.describe_cache_clusters(
                CacheClusterId=self.cluster_id,
                ShowCacheNodeInfo=True
            )
            
            clusters = response.get('CacheClusters', [])
            if clusters:
                cluster = clusters[0]
                return {
                    'cluster_id': cluster['CacheClusterId'],
                    'status': cluster['CacheClusterStatus'],
                    'node_type': cluster['CacheNodeType'],
                    'engine': cluster['Engine'],
                    'engine_version': cluster['EngineVersion'],
                    'num_cache_nodes': cluster['NumCacheNodes'],
                    'preferred_availability_zone': cluster.get('PreferredAvailabilityZone'),
                    'creation_time': cluster['CacheClusterCreateTime'].isoformat() if cluster.get('CacheClusterCreateTime') else None
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get cluster info: {e}")
            return {}
    
    def close_connection(self):
        """Close Redis connection"""
        try:
            if self.connection_pool:
                self.connection_pool.disconnect()
            
            self.logger.info("ElastiCache connection closed")
            
        except Exception as e:
            self.logger.error(f"Failed to close ElastiCache connection: {e}")