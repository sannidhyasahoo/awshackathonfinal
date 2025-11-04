#!/usr/bin/env python3
import boto3
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import random

def generate_load_test():
    """Generate high-volume test data for performance testing"""
    print("=== Load Testing VPC Flow Log System ===")
    
    kinesis = boto3.client('kinesis')
    
    def send_batch(batch_id):
        records = []
        for i in range(100):
            # Generate realistic flow log data
            record = {
                'source_ip': f'10.0.{random.randint(1,255)}.{random.randint(1,255)}',
                'dest_ip': f'172.16.{random.randint(1,255)}.{random.randint(1,255)}',
                'dest_port': random.choice([80, 443, 22, 3389, 1433, 3306]),
                'packets': random.randint(1, 1000),
                'bytes': random.randint(64, 65536),
                'timestamp': datetime.now().isoformat(),
                'batch_id': batch_id
            }
            
            # Inject some anomalies
            if i % 50 == 0:  # 2% anomaly rate
                record['dest_port'] = random.randint(1000, 65535)  # Unusual port
                record['packets'] = random.randint(10000, 50000)  # High packet count
            
            records.append({
                'Data': json.dumps(record),
                'PartitionKey': str(i % 10)
            })
        
        try:
            kinesis.put_records(
                StreamName='vpc-flow-logs-stream',
                Records=records
            )
            print(f"   ✅ Batch {batch_id}: 100 records sent")
        except Exception as e:
            print(f"   ❌ Batch {batch_id} failed: {e}")
    
    # Send 10,000 records using thread pool
    print("Sending 10,000 flow log records...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_batch, i) for i in range(100)]
        for future in futures:
            future.result()
    
    print("✅ Load test completed - 10,000 records sent")
    print("Monitor CloudWatch metrics for processing results")

if __name__ == "__main__":
    generate_load_test()