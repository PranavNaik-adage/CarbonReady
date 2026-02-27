"""
Create Sensor Calibration Record
"""
import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')

# Auto-discover calibration table
def get_calibration_table():
    """Find the sensor calibration table"""
    client = boto3.client('dynamodb')
    tables = client.list_tables()['TableNames']
    matching = [t for t in tables if 'SensorCalibrationTable' in t]
    if matching:
        return matching[0]
    raise Exception("Sensor calibration table not found. Make sure infrastructure is deployed.")

print("Creating sensor calibration...")

try:
    SENSOR_CALIBRATION_TABLE = get_calibration_table()
    print(f"Using table: {SENSOR_CALIBRATION_TABLE}")
    
    table = dynamodb.Table(SENSOR_CALIBRATION_TABLE)
    
    # Create calibration record
    calibration = {
        'deviceId': 'test-esp32-001',
        'calibrationDate': datetime.now(timezone.utc).isoformat(),
        'calibrationType': 'initial',
        'farmId': 'farm-001',
        'calibrationParameters': {
            'soilMoistureDry': 3200,
            'soilMoistureWet': 1200
        }
    }
    
    table.put_item(Item=calibration)
    print("✓ Calibration created successfully")
    print(f"  Device ID: {calibration['deviceId']}")
    print(f"  Farm ID: {calibration['farmId']}")
    print(f"  Calibration Date: {calibration['calibrationDate']}")
    
    # Verify it was created
    print("\nVerifying calibration...")
    response = table.query(
        KeyConditionExpression='deviceId = :device_id',
        ExpressionAttributeValues={':device_id': 'test-esp32-001'}
    )
    
    if response['Items']:
        print(f"✓ Found {len(response['Items'])} calibration record(s)")
        for item in response['Items']:
            print(f"  - {item['deviceId']} calibrated on {item['calibrationDate']}")
    else:
        print("✗ Calibration not found after creation!")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
