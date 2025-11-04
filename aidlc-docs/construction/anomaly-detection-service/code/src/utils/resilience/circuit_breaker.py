"""
Circuit Breaker and Fallback Patterns
Implements resilience patterns for ML model failures and service degradation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Union
from enum import Enum
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures before opening circuit
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes needed to close circuit
    timeout: int = 30                   # Operation timeout in seconds
    expected_exception: type = Exception # Exception type that triggers circuit

class CircuitBreakerError(Exception):
    """Circuit breaker is open"""
    pass

class CircuitBreaker:
    """Circuit breaker implementation for service resilience"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            await self._on_success()
            return result
            
        except self.config.expected_exception as e:
            await self._on_failure()
            raise e
        except asyncio.TimeoutError:
            await self._on_failure()
            raise CircuitBreakerError(f"Circuit breaker {self.name} timeout")
    
    async def _on_success(self):
        """Handle successful operation"""
        async with self._lock:
            self.failure_count = 0
            self.last_success_time = datetime.utcnow()
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} CLOSED after recovery")
    
    async def _on_failure(self):
        """Handle failed operation"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning(f"Circuit breaker {self.name} OPENED after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if not self.last_failure_time:
            return True
        
        return (datetime.utcnow() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }

class FallbackHandler:
    """Handles fallback strategies when primary services fail"""
    
    def __init__(self):
        self.fallback_strategies: Dict[str, Callable] = {}
        self.fallback_metrics: Dict[str, int] = {}
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """Register fallback function for a service"""
        self.fallback_strategies[service_name] = fallback_func
        self.fallback_metrics[service_name] = 0
        logger.info(f"Registered fallback for service: {service_name}")
    
    async def execute_fallback(self, service_name: str, *args, **kwargs) -> Any:
        """Execute fallback strategy"""
        if service_name not in self.fallback_strategies:
            raise ValueError(f"No fallback strategy registered for {service_name}")
        
        try:
            fallback_func = self.fallback_strategies[service_name]
            result = await fallback_func(*args, **kwargs) if asyncio.iscoroutinefunction(fallback_func) else fallback_func(*args, **kwargs)
            
            self.fallback_metrics[service_name] += 1
            logger.info(f"Executed fallback for {service_name}")
            return result
            
        except Exception as e:
            logger.error(f"Fallback failed for {service_name}: {e}")
            raise
    
    def get_metrics(self) -> Dict[str, int]:
        """Get fallback execution metrics"""
        return self.fallback_metrics.copy()

class ResilientService:
    """Combines circuit breaker with fallback patterns"""
    
    def __init__(self, name: str, primary_func: Callable, 
                 circuit_config: Optional[CircuitBreakerConfig] = None,
                 fallback_func: Optional[Callable] = None):
        self.name = name
        self.primary_func = primary_func
        self.fallback_func = fallback_func
        
        # Initialize circuit breaker
        config = circuit_config or CircuitBreakerConfig()
        self.circuit_breaker = CircuitBreaker(name, config)
        
        # Initialize fallback handler
        self.fallback_handler = FallbackHandler()
        if fallback_func:
            self.fallback_handler.register_fallback(name, fallback_func)
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute with circuit breaker and fallback protection"""
        try:
            # Try primary function with circuit breaker
            return await self.circuit_breaker.call(self.primary_func, *args, **kwargs)
            
        except (CircuitBreakerError, Exception) as e:
            logger.warning(f"Primary service {self.name} failed: {e}")
            
            # Try fallback if available
            if self.fallback_func:
                logger.info(f"Executing fallback for {self.name}")
                return await self.fallback_handler.execute_fallback(self.name, *args, **kwargs)
            else:
                # No fallback available, re-raise exception
                raise e
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status including circuit breaker and fallback metrics"""
        return {
            'service_name': self.name,
            'circuit_breaker': self.circuit_breaker.get_status(),
            'fallback_metrics': self.fallback_handler.get_metrics(),
            'has_fallback': self.fallback_func is not None
        }

class MLModelFallbackStrategies:
    """Specific fallback strategies for ML model failures"""
    
    @staticmethod
    async def statistical_only_fallback(flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to statistical detection only"""
        logger.info("Using statistical-only fallback for ML model failure")
        
        # Simple statistical anomaly detection
        # This would integrate with the statistical detection algorithms
        return {
            'anomaly_detected': False,
            'confidence_score': 0.5,
            'detection_method': 'statistical_fallback',
            'threat_type': 'unknown',
            'fallback_reason': 'ml_model_unavailable'
        }
    
    @staticmethod
    async def cached_model_fallback(flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to cached/local model predictions"""
        logger.info("Using cached model fallback")
        
        # This would use a locally cached model or pre-computed results
        return {
            'anomaly_detected': False,
            'confidence_score': 0.3,
            'detection_method': 'cached_model_fallback',
            'threat_type': 'unknown',
            'fallback_reason': 'using_cached_model'
        }
    
    @staticmethod
    async def rule_based_fallback(flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to rule-based detection"""
        logger.info("Using rule-based fallback")
        
        # Simple rule-based anomaly detection
        suspicious_ports = [22, 23, 135, 139, 445, 1433, 3389]
        dest_port = flow_data.get('destination_port', 0)
        
        anomaly_detected = dest_port in suspicious_ports
        
        return {
            'anomaly_detected': anomaly_detected,
            'confidence_score': 0.6 if anomaly_detected else 0.1,
            'detection_method': 'rule_based_fallback',
            'threat_type': 'suspicious_port' if anomaly_detected else 'normal',
            'fallback_reason': 'rule_based_detection'
        }

class ServiceResilienceManager:
    """Manages resilience patterns for all services"""
    
    def __init__(self):
        self.resilient_services: Dict[str, ResilientService] = {}
        self.global_metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'fallback_calls': 0,
            'circuit_breaker_trips': 0
        }
    
    def register_service(self, name: str, primary_func: Callable,
                        circuit_config: Optional[CircuitBreakerConfig] = None,
                        fallback_func: Optional[Callable] = None) -> ResilientService:
        """Register a resilient service"""
        service = ResilientService(name, primary_func, circuit_config, fallback_func)
        self.resilient_services[name] = service
        logger.info(f"Registered resilient service: {name}")
        return service
    
    async def execute_service(self, service_name: str, *args, **kwargs) -> Any:
        """Execute service with resilience patterns"""
        if service_name not in self.resilient_services:
            raise ValueError(f"Service {service_name} not registered")
        
        service = self.resilient_services[service_name]
        self.global_metrics['total_calls'] += 1
        
        try:
            result = await service.execute(*args, **kwargs)
            self.global_metrics['successful_calls'] += 1
            return result
            
        except Exception as e:
            self.global_metrics['failed_calls'] += 1
            
            # Check if fallback was used
            if service.fallback_func and 'fallback' in str(e).lower():
                self.global_metrics['fallback_calls'] += 1
            
            # Check if circuit breaker tripped
            if isinstance(e, CircuitBreakerError):
                self.global_metrics['circuit_breaker_trips'] += 1
            
            raise e
    
    def get_global_status(self) -> Dict[str, Any]:
        """Get global resilience status"""
        service_statuses = {}
        for name, service in self.resilient_services.items():
            service_statuses[name] = service.get_status()
        
        return {
            'global_metrics': self.global_metrics,
            'services': service_statuses,
            'total_services': len(self.resilient_services)
        }