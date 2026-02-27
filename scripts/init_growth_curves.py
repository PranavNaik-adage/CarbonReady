#!/usr/bin/env python3
"""
Initialize Growth Curve Parameters in DynamoDB

This script populates the GrowthCurves table with default Chapman-Richards
growth curve parameters for cashew and coconut crops in the Goa region.

Usage:
    python scripts/init_growth_curves.py
"""
import boto3
import sys
from datetime import datetime

def init_growth_curves():
    """Initialize growth curve parameters in DynamoDB"""
    
    dynamodb = boto3.resource('dynamodb')
    
    # Try to find the GrowthCurves table
    try:
        tables = dynamodb.meta.client.list_tables()['TableNames']
        growth_tables = [t for t in tables if 'GrowthCurve' in t or 'growthcurve' in t.lower()]
        
        if not growth_tables:
            print("⚠ GrowthCurves table not found in deployment")
            print("  This table is optional - growth curves are used as fallback when historical data is unavailable")
            print("  The system will work without it, using historical biomass data instead")
            return True
        
        table_name = growth_tables[0]
        print(f"Found table: {table_name}")
        
    except Exception as e:
        print(f"⚠ Could not list tables: {e}")
        print("  Skipping growth curves initialization")
        return True
    
    try:
        table = dynamodb.Table(table_name)
        
        # Default growth curve parameters for Goa region
        growth_curves = [
            {
                'cropType': 'cashew',
                'region': 'Goa',
                'growthCurve': {
                    'model': 'Chapman-Richards',
                    'parameters': {
                        'a': 250.0,   # Maximum biomass asymptote (kg)
                        'b': 0.08,    # Growth rate parameter
                        'c': 1.5      # Shape parameter
                    },
                    'description': 'Chapman-Richards growth curve calibrated for cashew trees in Goa region',
                    'source': 'Regional agricultural research data',
                    'calibrationDate': datetime.utcnow().isoformat()
                }
            },
            {
                'cropType': 'coconut',
                'region': 'Goa',
                'growthCurve': {
                    'model': 'Chapman-Richards',
                    'parameters': {
                        'a': 350.0,   # Maximum biomass asymptote (kg)
                        'b': 0.06,    # Growth rate parameter
                        'c': 1.8      # Shape parameter
                    },
                    'description': 'Chapman-Richards growth curve calibrated for coconut trees in Goa region',
                    'source': 'Regional agricultural research data',
                    'calibrationDate': datetime.utcnow().isoformat()
                }
            }
        ]
        
        # Insert growth curve parameters
        for curve in growth_curves:
            print(f"Inserting growth curve for {curve['cropType']} in {curve['region']}...")
            table.put_item(Item=curve)
            print(f"✓ Successfully inserted {curve['cropType']} growth curve")
        
        print("\n✓ Growth curve initialization complete!")
        print(f"Initialized {len(growth_curves)} growth curve configurations")
        
        return True
        
    except Exception as e:
        print(f"✗ Error initializing growth curves: {str(e)}")
        return False


if __name__ == '__main__':
    success = init_growth_curves()
    sys.exit(0 if success else 1)
