#!/usr/bin/env python3
"""
Initialize CRI Weights in DynamoDB
Sets default weights for Carbon Readiness Index calculation
"""
import boto3
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Table name (update if different)
TABLE_NAME = 'CarbonReadyCRIWeightsTable'


def init_cri_weights():
    """Initialize default CRI weights"""
    table = dynamodb.Table(TABLE_NAME)
    
    # Default weights as per design document
    default_weights = {
        'configId': 'default',
        'version': 1,
        'netCarbonPosition': 0.5,  # 50%
        'socTrend': 0.3,            # 30%
        'managementPractices': 0.2, # 20%
        'updatedAt': datetime.utcnow().isoformat(),
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
    init_cri_weights()
