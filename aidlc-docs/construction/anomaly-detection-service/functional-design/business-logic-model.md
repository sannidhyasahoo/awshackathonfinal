# Business Logic Model - Anomaly Detection Service

## Detection Architecture Overview

Based on individual algorithms with specialized ML models, multi-dimensional correlation, and tiered processing for optimal accuracy and performance.

## Individual Detection Algorithms

### Port Scanning Detection Algorithm

```python
def detect_port_scanning(flow_logs, time_window=60):
    """
    Individual algorithm optimized for port scanning detection
    Threshold: >20 unique destination ports in 60 seconds
    """
    port_scan_candidates = {}
    
    for log in flow_logs:
        source_ip = log.source_ip
        dest_port = log.destination_port
        timestamp = log.timestamp
        
        # Initialize tracking for new source IPs
        if source_ip not in port_scan_candidates:
            port_scan_candidates[source_ip] = {
                'unique_ports': set(),
                'first_seen': timestamp,
                'connections': []
            }
        
        candidate = port_scan_candidates[source_ip]
        
        # Add port to unique set
        candidate['unique_ports'].add(dest_port)
        candidate['connections'].append({
            'dest_ip': log.destination_ip,
            'dest_port': dest_port,
            'timestamp': timestamp,
            'action': log.action
        })
        
        # Check if within time window and threshold exceeded
        time_diff = (timestamp - candidate['first_seen']).total_seconds()
        if time_diff <= time_window and len(candidate['unique_ports']) > 20:
            
            # Multi-stage validation
            validation_score = validate_port_scan_indicators(candidate)
            if validation_score > PORT_SCAN_CONFIDENCE_THRESHOLD:
                
                return PortScanAnomaly(
                    source_ip=source_ip,
                    unique_ports=len(candidate['unique_ports']),
                    time_window=time_diff,
                    connections=candidate['connections'],
                    confidence_score=validation_score,
                    threat_type="PORT_SCANNING"
                )
    
    return None

def validate_port_scan_indicators(candidate):
    """
    Multi-stage validation for port scanning
    """
    score = 0.0
    
    # Indicator 1: Port diversity (higher diversity = more suspicious)
    port_diversity = calculate_port_diversity(candidate['unique_ports'])
    score += port_diversity * 0.3
    
    # Indicator 2: Connection success rate (low success = scanning)
    success_rate = calculate_connection_success_rate(candidate['connections'])
    if success_rate < 0.1:  # Less than 10% successful connections
        score += 0.4
    
    # Indicator 3: Sequential port patterns (common in scanning)
    sequential_score = detect_sequential_patterns(candidate['unique_ports'])
    score += sequential_score * 0.3
    
    return min(score, 1.0)
```

### DDoS Detection Algorithm

```python
def detect_ddos_patterns(flow_logs, time_window=60):
    """
    Individual algorithm optimized for DDoS detection
    Focus: High packet rate to single destination
    """
    destination_traffic = {}
    
    for log in flow_logs:
        dest_key = f"{log.destination_ip}:{log.destination_port}"
        timestamp = log.timestamp
        
        if dest_key not in destination_traffic:
            destination_traffic[dest_key] = {
                'packet_count': 0,
                'byte_count': 0,
                'source_ips': set(),
                'first_packet': timestamp,
                'connections': []
            }
        
        traffic = destination_traffic[dest_key]
        traffic['packet_count'] += log.packets
        traffic['byte_count'] += log.bytes
        traffic['source_ips'].add(log.source_ip)
        traffic['connections'].append(log)
        
        # Check for DDoS patterns
        time_diff = (timestamp - traffic['first_packet']).total_seconds()
        if time_diff <= time_window:
            
            # Calculate packet rate
            packet_rate = traffic['packet_count'] / time_diff
            
            # Multi-stage validation for DDoS
            if packet_rate > DDOS_PACKET_RATE_THRESHOLD:
                validation_score = validate_ddos_indicators(traffic, packet_rate)
                
                if validation_score > DDOS_CONFIDENCE_THRESHOLD:
                    return DDoSAnomaly(
                        target_ip=log.destination_ip,
                        target_port=log.destination_port,
                        packet_rate=packet_rate,
                        source_count=len(traffic['source_ips']),
                        attack_type=classify_ddos_type(traffic),
                        confidence_score=validation_score,
                        threat_type="DDOS"
                    )
    
    return None

def validate_ddos_indicators(traffic, packet_rate):
    """
    Multi-stage validation for DDoS attacks
    """
    score = 0.0
    
    # Indicator 1: Packet rate severity
    if packet_rate > DDOS_CRITICAL_THRESHOLD:
        score += 0.5
    elif packet_rate > DDOS_HIGH_THRESHOLD:
        score += 0.3
    
    # Indicator 2: Source IP diversity (distributed attack)
    source_diversity = len(traffic['source_ips'])
    if source_diversity > 100:  # Highly distributed
        score += 0.3
    elif source_diversity > 10:  # Moderately distributed
        score += 0.2
    
    # Indicator 3: Traffic pattern analysis
    pattern_score = analyze_ddos_patterns(traffic['connections'])
    score += pattern_score * 0.2
    
    return min(score, 1.0)
```

### C2 Beaconing Detection Algorithm

```python
def detect_c2_beaconing(flow_logs, min_connections=10):
    """
    Individual algorithm optimized for C2 beaconing detection
    Focus: Regular periodic connections with low coefficient of variation
    """
    connection_patterns = {}
    
    # Group connections by source-destination pair
    for log in flow_logs:
        conn_key = f"{log.source_ip}->{log.destination_ip}:{log.destination_port}"
        
        if conn_key not in connection_patterns:
            connection_patterns[conn_key] = []
        
        connection_patterns[conn_key].append(log.timestamp)
    
    # Analyze each connection pattern
    for conn_key, timestamps in connection_patterns.items():
        if len(timestamps) >= min_connections:
            
            # Calculate intervals between connections
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            # Calculate coefficient of variation
            if len(intervals) > 1:
                mean_interval = statistics.mean(intervals)
                std_interval = statistics.stdev(intervals)
                coefficient_variation = (std_interval / mean_interval) * 100
                
                # Check for beaconing pattern
                if coefficient_variation < C2_BEACONING_CV_THRESHOLD:
                    
                    # Multi-stage validation
                    validation_score = validate_beaconing_indicators(
                        intervals, mean_interval, coefficient_variation
                    )
                    
                    if validation_score > C2_CONFIDENCE_THRESHOLD:
                        source_ip, dest_info = conn_key.split('->')
                        dest_ip, dest_port = dest_info.split(':')
                        
                        return C2BeaconingAnomaly(
                            source_ip=source_ip,
                            destination_ip=dest_ip,
                            destination_port=int(dest_port),
                            connection_count=len(timestamps),
                            mean_interval=mean_interval,
                            coefficient_variation=coefficient_variation,
                            confidence_score=validation_score,
                            threat_type="C2_BEACONING"
                        )
    
    return None

def validate_beaconing_indicators(intervals, mean_interval, cv):
    """
    Multi-stage validation for C2 beaconing
    """
    score = 0.0
    
    # Indicator 1: Regularity (lower CV = more regular = more suspicious)
    if cv < 5:  # Very regular
        score += 0.5
    elif cv < 10:  # Moderately regular
        score += 0.3
    
    # Indicator 2: Reasonable beacon interval (not too fast/slow)
    if 60 <= mean_interval <= 3600:  # 1 minute to 1 hour
        score += 0.3
    elif 30 <= mean_interval <= 7200:  # 30 seconds to 2 hours
        score += 0.2
    
    # Indicator 3: Persistence (long-running pattern)
    total_duration = len(intervals) * mean_interval
    if total_duration > 3600:  # More than 1 hour
        score += 0.2
    
    return min(score, 1.0)
```

## Specialized ML Models

### Isolation Forest Model for Network Anomalies

```python
class NetworkIsolationForestModel:
    """
    Specialized Isolation Forest model for network traffic anomalies
    """
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        self.feature_scaler = StandardScaler()
        self.is_trained = False
    
    def extract_features(self, flow_logs):
        """
        Extract network-specific features for anomaly detection
        """
        features = []
        
        for log in flow_logs:
            feature_vector = [
                log.bytes,
                log.packets,
                log.bytes / max(log.packets, 1),  # Bytes per packet
                log.destination_port,
                self.encode_protocol(log.protocol),
                self.encode_time_features(log.timestamp),
                self.calculate_flow_duration(log),
                self.encode_action(log.action)
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def train_model(self, training_logs):
        """
        Train Isolation Forest on baseline network traffic
        """
        features = self.extract_features(training_logs)
        scaled_features = self.feature_scaler.fit_transform(features)
        
        self.model.fit(scaled_features)
        self.is_trained = True
        
        return ModelTrainingResult(
            model_type="IsolationForest",
            training_samples=len(training_logs),
            contamination_rate=0.1,
            training_timestamp=datetime.now()
        )
    
    def detect_anomalies(self, flow_logs):
        """
        Detect anomalies using trained Isolation Forest
        """
        if not self.is_trained:
            raise ModelNotTrainedException("Model must be trained before detection")
        
        features = self.extract_features(flow_logs)
        scaled_features = self.feature_scaler.transform(features)
        
        # Get anomaly scores (-1 = anomaly, 1 = normal)
        anomaly_labels = self.model.predict(scaled_features)
        anomaly_scores = self.model.decision_function(scaled_features)
        
        anomalies = []
        for i, (log, label, score) in enumerate(zip(flow_logs, anomaly_labels, anomaly_scores)):
            if label == -1:  # Anomaly detected
                anomalies.append(MLAnomaly(
                    flow_log=log,
                    anomaly_score=abs(score),
                    model_type="IsolationForest",
                    confidence=self.calculate_confidence(score),
                    threat_type="ML_BEHAVIORAL_ANOMALY"
                ))
        
        return anomalies
```

### LSTM Model for Behavioral Baseline

```python
class NetworkLSTMModel:
    """
    Specialized LSTM model for behavioral baseline analysis
    """
    
    def __init__(self, sequence_length=50):
        self.sequence_length = sequence_length
        self.model = None
        self.feature_scaler = MinMaxScaler()
        self.is_trained = False
    
    def build_model(self, feature_dim):
        """
        Build LSTM model architecture for network behavior
        """
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.sequence_length, feature_dim)),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(feature_dim, activation='linear')  # Reconstruction
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def prepare_sequences(self, flow_logs):
        """
        Prepare time series sequences for LSTM training
        """
        features = self.extract_temporal_features(flow_logs)
        scaled_features = self.feature_scaler.fit_transform(features)
        
        sequences = []
        for i in range(len(scaled_features) - self.sequence_length):
            sequence = scaled_features[i:i + self.sequence_length]
            sequences.append(sequence)
        
        return np.array(sequences)
    
    def train_baseline(self, baseline_logs):
        """
        Train LSTM on baseline network behavior
        """
        sequences = self.prepare_sequences(baseline_logs)
        
        if self.model is None:
            self.model = self.build_model(sequences.shape[2])
        
        # Train autoencoder (input = output for normal behavior)
        history = self.model.fit(
            sequences, sequences,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        self.is_trained = True
        
        return ModelTrainingResult(
            model_type="LSTM",
            training_samples=len(sequences),
            training_loss=history.history['loss'][-1],
            validation_loss=history.history['val_loss'][-1],
            training_timestamp=datetime.now()
        )
    
    def detect_baseline_deviations(self, flow_logs):
        """
        Detect deviations from learned baseline behavior
        """
        if not self.is_trained:
            raise ModelNotTrainedException("LSTM model must be trained before detection")
        
        sequences = self.prepare_sequences(flow_logs)
        
        # Get reconstruction errors
        reconstructions = self.model.predict(sequences)
        reconstruction_errors = np.mean(np.square(sequences - reconstructions), axis=(1, 2))
        
        # Calculate threshold for anomalies (e.g., 95th percentile)
        threshold = np.percentile(reconstruction_errors, 95)
        
        anomalies = []
        for i, error in enumerate(reconstruction_errors):
            if error > threshold:
                # Map back to original flow log
                log_index = i + self.sequence_length
                if log_index < len(flow_logs):
                    anomalies.append(MLAnomaly(
                        flow_log=flow_logs[log_index],
                        anomaly_score=error,
                        model_type="LSTM",
                        confidence=min(error / threshold, 1.0),
                        threat_type="BEHAVIORAL_DEVIATION"
                    ))
        
        return anomalies
```

## Multi-Dimensional Correlation Engine

```python
class MultiDimensionalCorrelationEngine:
    """
    Correlate anomalies by time, entity, and threat type
    """
    
    def __init__(self):
        self.time_window = 300  # 5 minutes
        self.entity_correlation_threshold = 0.7
        self.threat_correlation_weights = {
            'PORT_SCANNING': {'DDOS': 0.8, 'C2_BEACONING': 0.3},
            'DDOS': {'PORT_SCANNING': 0.8, 'CRYPTO_MINING': 0.2},
            'C2_BEACONING': {'CRYPTO_MINING': 0.6, 'TOR_USAGE': 0.7}
        }
    
    def correlate_anomalies(self, anomalies):
        """
        Perform multi-dimensional correlation of detected anomalies
        """
        correlated_groups = []
        processed_anomalies = set()
        
        for i, anomaly in enumerate(anomalies):
            if i in processed_anomalies:
                continue
            
            # Start new correlation group
            correlation_group = CorrelationGroup(primary_anomaly=anomaly)
            processed_anomalies.add(i)
            
            # Find related anomalies
            for j, other_anomaly in enumerate(anomalies[i+1:], i+1):
                if j in processed_anomalies:
                    continue
                
                correlation_score = self.calculate_correlation_score(anomaly, other_anomaly)
                
                if correlation_score > self.entity_correlation_threshold:
                    correlation_group.add_related_anomaly(other_anomaly, correlation_score)
                    processed_anomalies.add(j)
            
            correlated_groups.append(correlation_group)
        
        return correlated_groups
    
    def calculate_correlation_score(self, anomaly1, anomaly2):
        """
        Calculate multi-dimensional correlation score
        """
        score = 0.0
        
        # Time correlation (closer in time = higher correlation)
        time_diff = abs((anomaly1.timestamp - anomaly2.timestamp).total_seconds())
        if time_diff <= self.time_window:
            time_score = 1.0 - (time_diff / self.time_window)
            score += time_score * 0.4
        
        # Entity correlation (same source/destination)
        entity_score = self.calculate_entity_similarity(anomaly1, anomaly2)
        score += entity_score * 0.4
        
        # Threat type correlation (related threat types)
        threat_score = self.calculate_threat_correlation(anomaly1.threat_type, anomaly2.threat_type)
        score += threat_score * 0.2
        
        return min(score, 1.0)
    
    def calculate_entity_similarity(self, anomaly1, anomaly2):
        """
        Calculate entity-based similarity score
        """
        similarity = 0.0
        
        # Source IP similarity
        if anomaly1.source_ip == anomaly2.source_ip:
            similarity += 0.5
        
        # Destination IP similarity
        if hasattr(anomaly1, 'destination_ip') and hasattr(anomaly2, 'destination_ip'):
            if anomaly1.destination_ip == anomaly2.destination_ip:
                similarity += 0.3
        
        # Port similarity
        if hasattr(anomaly1, 'destination_port') and hasattr(anomaly2, 'destination_port'):
            if anomaly1.destination_port == anomaly2.destination_port:
                similarity += 0.2
        
        return similarity
```

## Tiered Processing Architecture

```python
class TieredAnomalyProcessor:
    """
    Tiered processing: Fast screening followed by detailed analysis
    """
    
    def __init__(self):
        self.tier1_processors = [
            PortScanningDetector(),
            DDoSDetector(),
            C2BeaconingDetector(),
            CryptoMiningDetector(),
            TorUsageDetector()
        ]
        self.tier2_ml_models = [
            NetworkIsolationForestModel(),
            NetworkLSTMModel()
        ]
        self.correlation_engine = MultiDimensionalCorrelationEngine()
    
    def process_flow_logs(self, flow_logs):
        """
        Process flow logs through tiered detection system
        """
        processing_start = time.time()
        
        # Tier 1: Fast statistical screening
        tier1_anomalies = self.tier1_fast_screening(flow_logs)
        
        # Tier 2: Detailed ML analysis (only if Tier 1 found potential threats)
        if tier1_anomalies:
            tier2_anomalies = self.tier2_detailed_analysis(flow_logs)
            all_anomalies = tier1_anomalies + tier2_anomalies
        else:
            all_anomalies = tier1_anomalies
        
        # Tier 3: Multi-dimensional correlation
        correlated_anomalies = self.correlation_engine.correlate_anomalies(all_anomalies)
        
        # Tier 4: Multi-stage validation and scoring
        validated_anomalies = self.tier4_validation(correlated_anomalies)
        
        processing_time = time.time() - processing_start
        
        return ProcessingResult(
            anomalies=validated_anomalies,
            processing_time=processing_time,
            tier1_count=len(tier1_anomalies),
            tier2_count=len(tier2_anomalies) if tier1_anomalies else 0,
            correlation_groups=len(correlated_anomalies)
        )
    
    def tier1_fast_screening(self, flow_logs):
        """
        Tier 1: Fast statistical detection algorithms
        """
        anomalies = []
        
        # Run individual detection algorithms in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for processor in self.tier1_processors:
                future = executor.submit(processor.detect, flow_logs)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    anomalies.extend(result if isinstance(result, list) else [result])
        
        return anomalies
    
    def tier4_validation(self, correlation_groups):
        """
        Tier 4: Multi-stage validation before flagging as anomaly
        """
        validated_anomalies = []
        
        for group in correlation_groups:
            # Calculate group confidence score
            group_confidence = self.calculate_group_confidence(group)
            
            # Apply multi-stage validation
            validation_result = self.apply_multistage_validation(group)
            
            if validation_result.is_valid and group_confidence > ANOMALY_CONFIDENCE_THRESHOLD:
                validated_anomalies.append(ValidatedAnomaly(
                    correlation_group=group,
                    confidence_score=group_confidence,
                    validation_result=validation_result,
                    final_threat_assessment=self.assess_threat_level(group, group_confidence)
                ))
        
        return validated_anomalies
```