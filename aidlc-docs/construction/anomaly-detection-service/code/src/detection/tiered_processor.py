"""
Tiered Processing Orchestrator
Orchestrates the 4-tier anomaly detection process with fallback patterns.
"""

import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .statistical.port_scanning_detector import PortScanningDetector
from .statistical.ddos_detector import DDoSDetector
from .statistical.c2_beaconing_detector import C2BeaconingDetector
from .statistical.crypto_mining_detector import CryptoMiningDetector
from .statistical.tor_usage_detector import TorUsageDetector
from .ml.ml_model_manager import MLModelManager
from .correlation.correlation_engine import MultiDimensionalCorrelationEngine
from .validation.validation_engine import MultiStageValidationEngine

class ProcessingResult:
    def __init__(self):
        self.anomalies = []
        self.total_processing_time = 0.0
        self.tier_timings = {}
        self.tier1_count = 0
        self.tier2_count = 0
        self.correlation_groups = 0
        self.validated_count = 0
        self.processing_metadata = {}

class TieredAnomalyProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize tier 1 processors (statistical)
        self.tier1_processors = {
            'port_scanning': PortScanningDetector(
                port_threshold=config.get('port_scan_threshold', 20),
                time_window=config.get('port_scan_window', 60)
            ),
            'ddos': DDoSDetector(
                packet_rate_threshold=config.get('ddos_threshold', 1000),
                time_window=config.get('ddos_window', 60)
            ),
            'c2_beaconing': C2BeaconingDetector(
                min_connections=config.get('c2_min_connections', 10),
                cv_threshold=config.get('c2_cv_threshold', 15.0)
            ),
            'crypto_mining': CryptoMiningDetector(
                min_connections=config.get('crypto_min_connections', 5),
                data_threshold=config.get('crypto_data_threshold', 1024*1024)
            ),
            'tor_usage': TorUsageDetector(
                min_connections=config.get('tor_min_connections', 3)
            )
        }
        
        # Initialize tier 2 processor (ML)
        self.ml_model_manager = MLModelManager(config.get('ml_config', {}))
        
        # Initialize tier 3 processor (correlation)
        self.correlation_engine = MultiDimensionalCorrelationEngine(
            config.get('correlation_config', {})
        )
        
        # Initialize tier 4 processor (validation)
        self.validation_engine = MultiStageValidationEngine(
            config.get('validation_config', {})
        )
        
        # Processing configuration
        self.tier1_timeout = config.get('tier1_timeout', 30)
        self.tier2_timeout = config.get('tier2_timeout', 120)
        self.tier3_timeout = config.get('tier3_timeout', 180)
        self.tier4_timeout = config.get('tier4_timeout', 120)
        
        # Thread pools for parallel processing
        self.tier1_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="tier1")
        self.tier2_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="tier2")
        
    def process_flow_logs(self, flow_logs: List[Dict]) -> ProcessingResult:
        """Process flow logs through tiered detection system"""
        processing_start = time.time()
        result = ProcessingResult()
        
        try:
            # Tier 1: Fast statistical screening
            tier1_start = time.time()
            tier1_anomalies = self._tier1_fast_screening(flow_logs)
            tier1_time = time.time() - tier1_start
            
            result.tier1_count = len(tier1_anomalies)
            result.tier_timings['tier1'] = tier1_time
            
            self.logger.info(f"Tier 1 completed: {len(tier1_anomalies)} anomalies in {tier1_time:.2f}s")
            
            # Early exit if no anomalies found
            if not tier1_anomalies:
                result.total_processing_time = time.time() - processing_start
                return result
            
            # Tier 2: ML-based analysis (only if Tier 1 found potential threats)
            tier2_start = time.time()
            tier2_anomalies = self._tier2_ml_analysis(flow_logs, tier1_anomalies)
            tier2_time = time.time() - tier2_start
            
            result.tier2_count = len(tier2_anomalies)
            result.tier_timings['tier2'] = tier2_time
            
            self.logger.info(f"Tier 2 completed: {len(tier2_anomalies)} anomalies in {tier2_time:.2f}s")
            
            # Combine tier 1 and tier 2 anomalies
            all_anomalies = tier1_anomalies + tier2_anomalies
            
            # Tier 3: Multi-dimensional correlation
            tier3_start = time.time()
            correlation_groups = self._tier3_correlation_analysis(all_anomalies)
            tier3_time = time.time() - tier3_start
            
            result.correlation_groups = len(correlation_groups)
            result.tier_timings['tier3'] = tier3_time
            
            self.logger.info(f"Tier 3 completed: {len(correlation_groups)} groups in {tier3_time:.2f}s")
            
            # Tier 4: Multi-stage validation
            tier4_start = time.time()
            validated_anomalies = self._tier4_validation(correlation_groups)
            tier4_time = time.time() - tier4_start
            
            result.validated_count = len(validated_anomalies)
            result.tier_timings['tier4'] = tier4_time
            
            self.logger.info(f"Tier 4 completed: {len(validated_anomalies)} validated in {tier4_time:.2f}s")
            
            # Final results
            result.anomalies = validated_anomalies
            result.total_processing_time = time.time() - processing_start
            
            # Processing metadata
            result.processing_metadata = {
                'input_logs': len(flow_logs),
                'processing_timestamp': datetime.utcnow().isoformat(),
                'sla_compliance': result.total_processing_time <= 300,  # 5 minutes
                'efficiency_ratio': len(validated_anomalies) / max(len(flow_logs), 1)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            result.total_processing_time = time.time() - processing_start
            result.processing_metadata = {'error': str(e)}
            return result
    
    def _tier1_fast_screening(self, flow_logs: List[Dict]) -> List[Any]:
        """Tier 1: Fast statistical detection algorithms"""
        anomalies = []
        
        # Convert dict logs to FlowLog objects for detectors
        from .statistical.port_scanning_detector import FlowLog
        
        flow_log_objects = []
        for log in flow_logs:
            try:
                timestamp = log.get('timestamp')
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.utcnow()
                
                flow_log = FlowLog(
                    timestamp=timestamp,
                    source_ip=log.get('source_ip', ''),
                    destination_ip=log.get('destination_ip', ''),
                    destination_port=int(log.get('destination_port', 0)),
                    protocol=log.get('protocol', 'TCP'),
                    action=log.get('action', 'ACCEPT'),
                    packets=int(log.get('packets', 1)),
                    bytes=int(log.get('bytes', 0))
                )
                flow_log_objects.append(flow_log)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to parse flow log: {e}")
                continue
        
        if not flow_log_objects:
            return []
        
        # Run detection algorithms in parallel
        futures = {}
        
        for detector_name, detector in self.tier1_processors.items():
            future = self.tier1_pool.submit(detector.detect, flow_log_objects)
            futures[future] = detector_name
        
        # Collect results with timeout
        for future in as_completed(futures, timeout=self.tier1_timeout):
            detector_name = futures[future]
            try:
                result = future.result()
                if result:
                    if isinstance(result, list):
                        anomalies.extend(result)
                    else:
                        anomalies.append(result)
                    
                    self.logger.debug(f"{detector_name} found {len(result) if isinstance(result, list) else 1} anomalies")
                    
            except Exception as e:
                self.logger.error(f"Tier 1 detector {detector_name} failed: {e}")
        
        return anomalies
    
    def _tier2_ml_analysis(self, flow_logs: List[Dict], tier1_anomalies: List[Any]) -> List[Any]:
        """Tier 2: ML-based behavioral analysis"""
        if not tier1_anomalies:
            return []
        
        try:
            # Use ML model manager for detection
            ml_anomalies = self.ml_model_manager.detect_ml_anomalies(flow_logs)
            
            self.logger.debug(f"ML analysis found {len(ml_anomalies)} anomalies")
            return ml_anomalies
            
        except Exception as e:
            self.logger.error(f"Tier 2 ML analysis failed: {e}")
            # Graceful degradation - return empty list, continue with tier 1 results
            return []
    
    def _tier3_correlation_analysis(self, anomalies: List[Any]) -> List[Any]:
        """Tier 3: Multi-dimensional correlation analysis"""
        if len(anomalies) < 2:
            # Single anomaly - create individual correlation group
            if anomalies:
                return [self.correlation_engine._create_single_anomaly_group(anomalies[0])]
            return []
        
        try:
            correlation_groups = self.correlation_engine.correlate_anomalies(anomalies)
            
            self.logger.debug(f"Correlation analysis created {len(correlation_groups)} groups")
            return correlation_groups
            
        except Exception as e:
            self.logger.error(f"Tier 3 correlation analysis failed: {e}")
            # Fallback - create individual groups for each anomaly
            fallback_groups = []
            for anomaly in anomalies:
                group = self.correlation_engine._create_single_anomaly_group(anomaly)
                fallback_groups.append(group)
            return fallback_groups
    
    def _tier4_validation(self, correlation_groups: List[Any]) -> List[Any]:
        """Tier 4: Multi-stage validation"""
        if not correlation_groups:
            return []
        
        try:
            validated_anomalies = self.validation_engine.validate_correlation_groups(correlation_groups)
            
            self.logger.debug(f"Validation approved {len(validated_anomalies)} anomalies")
            return validated_anomalies
            
        except Exception as e:
            self.logger.error(f"Tier 4 validation failed: {e}")
            # Fallback - return groups with basic validation
            fallback_validated = []
            for group in correlation_groups:
                # Basic confidence check
                confidence = getattr(group.primary_anomaly, 'confidence_score', 0.5)
                if confidence > 0.7:  # Basic threshold
                    from .validation.validation_engine import ValidatedAnomaly, ValidationResult
                    
                    basic_validation = ValidationResult(
                        is_valid=True,
                        confidence_score=confidence,
                        validation_stages={'basic': True},
                        failure_reasons=[],
                        validation_metadata={'fallback': True}
                    )
                    
                    validated = ValidatedAnomaly(
                        correlation_group=group,
                        confidence_score=confidence,
                        validation_result=basic_validation,
                        final_threat_assessment={
                            'severity': 'MEDIUM',
                            'priority': 5,
                            'threat_type': getattr(group.primary_anomaly, 'threat_type', 'UNKNOWN'),
                            'confidence': confidence
                        }
                    )
                    fallback_validated.append(validated)
            
            return fallback_validated
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing performance statistics"""
        return {
            'tier1_processors': list(self.tier1_processors.keys()),
            'ml_model_status': self.ml_model_manager.get_model_status(),
            'processing_timeouts': {
                'tier1': self.tier1_timeout,
                'tier2': self.tier2_timeout,
                'tier3': self.tier3_timeout,
                'tier4': self.tier4_timeout
            }
        }
    
    def health_check(self) -> Dict[str, bool]:
        """Perform health check on all tiers"""
        health_status = {}
        
        # Tier 1 - always healthy (statistical algorithms)
        health_status['tier1'] = True
        
        # Tier 2 - ML models
        ml_status = self.ml_model_manager.get_model_status()
        health_status['tier2'] = any(status['is_healthy'] for status in ml_status.values())
        
        # Tier 3 - correlation engine (always healthy)
        health_status['tier3'] = True
        
        # Tier 4 - validation engine (always healthy)
        health_status['tier4'] = True
        
        return health_status