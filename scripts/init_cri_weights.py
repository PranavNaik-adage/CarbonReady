#!/usr/bin/env python3
"""
Initialize CRI Weights in DynamoDB
Sets default weights for Carbon Readiness Index calculation
"""
import boto3
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Table name - can be passed as command line argument
# Usage: python init_cri_weights.py [table-name]
TABLE_NAME = sys.argv[1] if len(sys.argv) > 1 else 'carbonready-cri-weights'


def init_cri_weights():
    """Initialize default CRI weights"""
    table = dynamodb.Table(TABLE_NAME)
    
    # Default weights as per design document
    # Note: DynamoDB requires Decimal type for numbers
    default_weights = {
        'configId': 'default',
        'version': 1,
        'netCarbonPosition': Decimal('0.5'),  # 50%
        'socTrend': Decimal('0.3'),            # 30%
        'managementPractices': Decimal('0.2'), # 20%
        'updatedAt': datetime.now(timezone.utc).isoformat(),
        'updatedBy': 'system-init'
    }
    
    try:
        # Put item in DynamoDB
        table.put_item(Item=default_weights)
        print("✓ Successfully initialized default CRI weights")
        print(f"  - Net Carbon Position: {default_weights['netCarbonPosition']} (50%)")
        print(f"  - SOC Trend: {default_weights['socTrend']} (30%)")
        print(f"  - Management Practices: {default_weights['managementPractices']} (20%)")
        
    except Exception as e:
        print(f"✗ Error initializing CRI weights: {str(e)}")
        raise


if __name__ == '__main__':
    print("Initializing CRI weights...")
    print(f"Table name: {TABLE_NAME}")
    
    # List available tables to help with debugging
    try:
        tables = dynamodb.meta.client.list_tables()['TableNames']
        cri_tables = [t for t in tables if 'cri' in t.lower() or 'weight' in t.lower()]
        if cri_tables:
            print(f"Found CRI-related tables: {', '.join(cri_tables)}")
    except Exception as e:
        print(f"Could not list tables: {e}")
    
    init_cri_weights()
