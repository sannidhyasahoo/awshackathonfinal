"""
Hierarchical Context Management System
DynamoDB-based context storage with multi-level access patterns
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class ContextLevel(Enum):
    GLOBAL = "global"
    INVESTIGATION = "investigation"
    AGENT = "agent"

class ContextType(Enum):
    THREAT_INTEL = "threat_intel"
    BASELINE = "baseline"
    CLASSIFICATION = "classification"
    INVESTIGATION = "investigation"
    RESPONSE = "response"
    AUDIT = "audit"

@dataclass
class ContextEntry:
    """Context entry data structure"""
    context_id: str
    level: ContextLevel
    context_type: ContextType
    anomaly_id: Optional[str]
    investigation_id: Optional[str]
    agent_id: Optional[str]
    data: Dict[str, Any]
    timestamp: str
    ttl: int
    access_permissions: List[str]

class HierarchicalContextManager:
    """Manages hierarchical context storage and retrieval"""
    
    def __init__(self, table_name: str = 'ai-agent-context'):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        
    def store_global_context(self, context_type: ContextType, data: Dict[str, Any], 
                           ttl_hours: int = 168) -> str:
        """Store global context accessible to all agents"""
        
        context_id = f"global_{context_type.value}_{uuid.uuid4().hex[:8]}"
        
        entry = ContextEntry(
            context_id=context_id,
            level=ContextLevel.GLOBAL,
            context_type=context_type,
            anomaly_id=None,
            investigation_id=None,
            agent_id=None,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            ttl=int((datetime.utcnow() + timedelta(hours=ttl_hours)).timestamp()),
            access_permissions=['all_agents']
        )
        
        self._store_context_entry(entry)
        return context_id
    
    def store_investigation_context(self, investigation_id: str, anomaly_id: str,
                                  context_type: ContextType, data: Dict[str, Any],
                                  ttl_hours: int = 720) -> str:
        """Store investigation-specific context"""
        
        context_id = f"inv_{investigation_id}_{context_type.value}_{uuid.uuid4().hex[:8]}"
        
        entry = ContextEntry(
            context_id=context_id,
            level=ContextLevel.INVESTIGATION,
            context_type=context_type,
            anomaly_id=anomaly_id,
            investigation_id=investigation_id,
            agent_id=None,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            ttl=int((datetime.utcnow() + timedelta(hours=ttl_hours)).timestamp()),
            access_permissions=[f'investigation_{investigation_id}']
        )
        
        self._store_context_entry(entry)
        return context_id
    
    def store_agent_context(self, agent_id: str, investigation_id: Optional[str],
                          context_type: ContextType, data: Dict[str, Any],
                          ttl_hours: int = 24) -> str:
        """Store agent-specific context"""
        
        context_id = f"agent_{agent_id}_{context_type.value}_{uuid.uuid4().hex[:8]}"
        
        entry = ContextEntry(
            context_id=context_id,
            level=ContextLevel.AGENT,
            context_type=context_type,
            anomaly_id=None,
            investigation_id=investigation_id,
            agent_id=agent_id,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            ttl=int((datetime.utcnow() + timedelta(hours=ttl_hours)).timestamp()),
            access_permissions=[f'agent_{agent_id}']
        )
        
        self._store_context_entry(entry)
        return context_id
    
    def get_context_hierarchy(self, investigation_id: str, agent_id: str) -> Dict[str, List[ContextEntry]]:
        """Get complete context hierarchy for an agent in an investigation"""
        
        context_hierarchy = {
            'global': [],
            'investigation': [],
            'agent': []
        }
        
        # Get global context
        global_contexts = self._query_global_context()
        context_hierarchy['global'] = global_contexts
        
        # Get investigation context
        if investigation_id:
            inv_contexts = self._query_investigation_context(investigation_id)
            context_hierarchy['investigation'] = inv_contexts
        
        # Get agent context
        agent_contexts = self._query_agent_context(agent_id, investigation_id)
        context_hierarchy['agent'] = agent_contexts
        
        return context_hierarchy
    
    def get_context_by_type(self, context_type: ContextType, 
                          investigation_id: Optional[str] = None,
                          agent_id: Optional[str] = None) -> List[ContextEntry]:
        """Get context entries by type with hierarchical access"""
        
        contexts = []
        
        # Global context of this type
        global_contexts = self._query_context_by_type(ContextLevel.GLOBAL, context_type)
        contexts.extend(global_contexts)
        
        # Investigation context if specified
        if investigation_id:
            inv_contexts = self._query_context_by_type(ContextLevel.INVESTIGATION, context_type, investigation_id)
            contexts.extend(inv_contexts)
        
        # Agent context if specified
        if agent_id:
            agent_contexts = self._query_context_by_type(ContextLevel.AGENT, context_type, agent_id)
            contexts.extend(agent_contexts)
        
        return contexts
    
    def update_context(self, context_id: str, data_updates: Dict[str, Any]) -> bool:
        """Update existing context entry"""
        
        try:
            # Get existing entry
            response = self.table.get_item(Key={'context_id': context_id})
            
            if 'Item' not in response:
                return False
            
            # Update data field
            existing_data = response['Item'].get('data', {})
            existing_data.update(data_updates)
            
            # Update entry
            self.table.update_item(
                Key={'context_id': context_id},
                UpdateExpression='SET #data = :data, last_updated = :timestamp',
                ExpressionAttributeNames={'#data': 'data'},
                ExpressionAttributeValues={
                    ':data': existing_data,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error updating context {context_id}: {e}")
            return False
    
    def delete_context(self, context_id: str) -> bool:
        """Delete context entry"""
        
        try:
            self.table.delete_item(Key={'context_id': context_id})
            return True
        except Exception as e:
            print(f"Error deleting context {context_id}: {e}")
            return False
    
    def cleanup_expired_context(self) -> int:
        """Clean up expired context entries"""
        
        current_timestamp = int(datetime.utcnow().timestamp())
        deleted_count = 0
        
        try:
            # Scan for expired entries
            response = self.table.scan(
                FilterExpression='#ttl < :current_time',
                ExpressionAttributeNames={'#ttl': 'ttl'},
                ExpressionAttributeValues={':current_time': current_timestamp}
            )
            
            # Delete expired entries
            for item in response.get('Items', []):
                self.table.delete_item(Key={'context_id': item['context_id']})
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up expired context: {e}")
            return 0
    
    def _store_context_entry(self, entry: ContextEntry):
        """Store context entry in DynamoDB"""
        
        item = {
            'context_id': entry.context_id,
            'level': entry.level.value,
            'context_type': entry.context_type.value,
            'data': entry.data,
            'timestamp': entry.timestamp,
            'ttl': entry.ttl,
            'access_permissions': entry.access_permissions
        }
        
        # Add optional fields
        if entry.anomaly_id:
            item['anomaly_id'] = entry.anomaly_id
        if entry.investigation_id:
            item['investigation_id'] = entry.investigation_id
        if entry.agent_id:
            item['agent_id'] = entry.agent_id
        
        self.table.put_item(Item=item)
    
    def _query_global_context(self) -> List[ContextEntry]:
        """Query global context entries"""
        
        response = self.table.query(
            IndexName='level-timestamp-index',
            KeyConditionExpression='#level = :level',
            ExpressionAttributeNames={'#level': 'level'},
            ExpressionAttributeValues={':level': ContextLevel.GLOBAL.value},
            ScanIndexForward=False,
            Limit=50
        )
        
        return [self._item_to_context_entry(item) for item in response.get('Items', [])]
    
    def _query_investigation_context(self, investigation_id: str) -> List[ContextEntry]:
        """Query investigation-specific context"""
        
        response = self.table.query(
            IndexName='investigation-id-index',
            KeyConditionExpression='investigation_id = :inv_id',
            ExpressionAttributeValues={':inv_id': investigation_id},
            ScanIndexForward=False,
            Limit=100
        )
        
        return [self._item_to_context_entry(item) for item in response.get('Items', [])]
    
    def _query_agent_context(self, agent_id: str, investigation_id: Optional[str]) -> List[ContextEntry]:
        """Query agent-specific context"""
        
        if investigation_id:
            # Query agent context for specific investigation
            response = self.table.query(
                IndexName='agent-investigation-index',
                KeyConditionExpression='agent_id = :agent_id AND investigation_id = :inv_id',
                ExpressionAttributeValues={
                    ':agent_id': agent_id,
                    ':inv_id': investigation_id
                },
                ScanIndexForward=False,
                Limit=50
            )
        else:
            # Query all agent context
            response = self.table.query(
                IndexName='agent-id-index',
                KeyConditionExpression='agent_id = :agent_id',
                ExpressionAttributeValues={':agent_id': agent_id},
                ScanIndexForward=False,
                Limit=50
            )
        
        return [self._item_to_context_entry(item) for item in response.get('Items', [])]
    
    def _query_context_by_type(self, level: ContextLevel, context_type: ContextType,
                             filter_id: Optional[str] = None) -> List[ContextEntry]:
        """Query context by level and type"""
        
        key_condition = '#level = :level AND context_type = :type'
        expression_values = {
            ':level': level.value,
            ':type': context_type.value
        }
        
        if filter_id and level == ContextLevel.INVESTIGATION:
            key_condition += ' AND investigation_id = :filter_id'
            expression_values[':filter_id'] = filter_id
        elif filter_id and level == ContextLevel.AGENT:
            key_condition += ' AND agent_id = :filter_id'
            expression_values[':filter_id'] = filter_id
        
        response = self.table.query(
            IndexName='level-type-index',
            KeyConditionExpression=key_condition,
            ExpressionAttributeNames={'#level': 'level'},
            ExpressionAttributeValues=expression_values,
            ScanIndexForward=False,
            Limit=50
        )
        
        return [self._item_to_context_entry(item) for item in response.get('Items', [])]
    
    def _item_to_context_entry(self, item: Dict[str, Any]) -> ContextEntry:
        """Convert DynamoDB item to ContextEntry"""
        
        return ContextEntry(
            context_id=item['context_id'],
            level=ContextLevel(item['level']),
            context_type=ContextType(item['context_type']),
            anomaly_id=item.get('anomaly_id'),
            investigation_id=item.get('investigation_id'),
            agent_id=item.get('agent_id'),
            data=item.get('data', {}),
            timestamp=item['timestamp'],
            ttl=item['ttl'],
            access_permissions=item.get('access_permissions', [])
        )

class ContextAccessController:
    """Controls access to context based on permissions"""
    
    def __init__(self, context_manager: HierarchicalContextManager):
        self.context_manager = context_manager
    
    def check_access(self, agent_id: str, investigation_id: Optional[str], 
                    context_entry: ContextEntry) -> bool:
        """Check if agent has access to context entry"""
        
        permissions = context_entry.access_permissions
        
        # Global access
        if 'all_agents' in permissions:
            return True
        
        # Agent-specific access
        if f'agent_{agent_id}' in permissions:
            return True
        
        # Investigation-specific access
        if investigation_id and f'investigation_{investigation_id}' in permissions:
            return True
        
        return False
    
    def filter_accessible_contexts(self, agent_id: str, investigation_id: Optional[str],
                                 contexts: List[ContextEntry]) -> List[ContextEntry]:
        """Filter contexts based on access permissions"""
        
        return [
            context for context in contexts
            if self.check_access(agent_id, investigation_id, context)
        ]