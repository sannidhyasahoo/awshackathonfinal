#!/usr/bin/env python3
import os
import boto3
import requests
from datetime import datetime

class ThreatIntelligenceManager:
    def __init__(self):
        self.otx_api_key = os.getenv('OTX_API_KEY')
        self.abuseipdb_api_key = os.getenv('ABUSEIPDB_API_KEY')
        self.dynamodb = boto3.resource('dynamodb')
        
    def test_otx_connection(self):
        """Test AlienVault OTX API connection"""
        try:
            headers = {'X-OTX-API-KEY': self.otx_api_key}
            response = requests.get('https://otx.alienvault.com/api/v1/user/me', headers=headers)
            if response.status_code == 200:
                return True, "OTX API connection successful"
            return False, f"OTX API error: {response.status_code}"
        except Exception as e:
            return False, f"OTX connection failed: {str(e)}"
    
    def test_abuseipdb_connection(self):
        """Test AbuseIPDB API connection"""
        try:
            headers = {'Key': self.abuseipdb_api_key, 'Accept': 'application/json'}
            params = {'ipAddress': '8.8.8.8', 'maxAgeInDays': 90}
            response = requests.get('https://api.abuseipdb.com/api/v2/check', headers=headers, params=params)
            if response.status_code == 200:
                return True, "AbuseIPDB API connection successful"
            return False, f"AbuseIPDB API error: {response.status_code}"
        except Exception as e:
            return False, f"AbuseIPDB connection failed: {str(e)}"
    
    def validate_integration(self):
        """Validate all threat intelligence integrations"""
        results = {}
        
        # Test OTX
        otx_success, otx_msg = self.test_otx_connection()
        results['otx'] = {'success': otx_success, 'message': otx_msg}
        
        # Test AbuseIPDB  
        abuse_success, abuse_msg = self.test_abuseipdb_connection()
        results['abuseipdb'] = {'success': abuse_success, 'message': abuse_msg}
        
        return results

if __name__ == "__main__":
    manager = ThreatIntelligenceManager()
    results = manager.validate_integration()
    
    print("=== Threat Intelligence Integration Validation ===")
    for service, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {service.upper()}: {result['message']}")
    
    all_success = all(r['success'] for r in results.values())
    if all_success:
        print("\n🎉 All threat intelligence APIs integrated successfully!")
        print("System ready for full deployment with threat intelligence")
    else:
        print("\n⚠️ Some integrations failed - check API keys")