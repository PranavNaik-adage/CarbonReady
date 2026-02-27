"""
Test Data Ingestion Pipeline
Tests the complete data flow from IoT to DynamoDB
"""
import boto3
import json
import time
import sys
from datetime import datetime, timezone

# AWS clients
dynamodb = boto3.resource('dynamodb')
iot_data = boto3.client('iot-data')
s3 = boto3.client('s3')
logs = boto3.client('logs')

# Get table names from command line or discover them
def get_table_name(prefix):
    """Get table name by prefix"""
    client = boto3.client('dynamodb')
    tables = client.list_tables()['TableNames']
    matching = [t for t in tables if prefix in t]
    if matching:
        return matching[0]
    raise Exception(f"No table found with prefix: {prefix}")

def get_bucket_name():
    """Get S3 bucket name"""
    s3_client = boto3.client('s3')
    buckets = s3_client.list_buckets()['Buckets']
    matching = [b['Name'] for b in buckets if 'carbonready' in b['Name'].lower() and 'sensor' in b['Name'].lower()]
    if matching:
        return matching[0]
    raise Exception("No CarbonReady sensor bucket found")

print("=" * 50)
print("Testing Data Ingestion Pipeline")
print("=" * 50)
print()

# Discover AWS resources
print("Discovering AWS resources...")
try:
    SENSOR_DATA_TABLE = get_table_name('SensorDataTable')
    SENSOR_CALIBRATION_TABLE = get_table_name('SensorCalibrationTable')
    BUCKET_NAME = get_bucket_name()
    print(f"✓ Found sensor data table: {SENSOR_DATA_TABLE}")
    print(f"✓ Found calibration table: {SENSOR_CALIBRATION_TABLE}")
    print(f"✓ Found S3 bucket: {BUCKET_NAME}")
except Exception as e:
    print(f"✗ Error discovering resources: {e}")
    print("Make sure AWS infrastructure is deployed")
    sys.exit(1)

print()
# Step 1: Create sensor calibration
print("Step 1: Creating sensor calibration...")
calibration_table = dynamodb.Table(SENSOR_CALIBRATION_TABLE)

try:
    calibration_table.put_item(Item={
        'deviceId': 'test-esp32-001',
        'calibrationDate': datetime.now(timezone.utc).isoformat(),
        'calibrationType': 'initial',
        'farmId': 'farm-001',
        'calibrationParameters': {
            'soilMoistureDry': 3200,
            'soilMoistureWet': 1200
        }
    })
    print("✓ Sensor calibration created")
except Exception as e:
    print(f"✗ Error creating calibration: {e}")

print()

# Step 2: Load and publish test data
print("Step 2: Publishing sensor data to IoT Core...")

try:
    with open('test-valid-sensor-data.json', 'r') as f:
        payload = json.load(f)
    
    response = iot_data.publish(
        topic='carbonready/farm/farm-001/sensor/data',
        qos=1,
        payload=json.dumps(payload)
    )
    print("✓ Data published successfully")
except FileNotFoundError:
    print("✗ test-valid-sensor-data.json not found")
    print("  Run: python scripts/test_system.py")
    exit(1)
except Exception as e:
    print(f"✗ Error publishing data: {e}")
    exit(1)

print()

# Step 3: Wait for Lambda to process
print("Step 3: Waiting for Lambda to process (5 seconds)...")
time.sleep(5)

# Step 4: Check CloudWatch Logs
print("Step 4: Checking CloudWatch Logs...")
try:
    log_group = '/aws/lambda/carbonready-data-ingestion'
    
    # Get log streams
    streams_response = logs.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    
    if streams_response['logStreams']:
        stream_name = streams_response['logStreams'][0]['logStreamName']
        
        # Get recent log events
        events_response = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=20,
            startFromHead=False
        )
        
        print("Recent logs:")
        for event in events_response['events'][-10:]:
            print(f"  {event['message'].strip()}")
    else:
        print("  No log streams found")
        
except Exception as e:
    print(f"  Could not fetch logs: {e}")

print()

# Step 5: Verify data in DynamoDB
print("Step 5: Checking DynamoDB for sensor data...")
sensor_table = dynamodb.Table(SENSOR_DATA_TABLE)

try:
    response = sensor_table.query(
        KeyConditionExpression='farmId = :farmId',
        ExpressionAttributeValues={':farmId': 'farm-001'},
        Limit=5,
        ScanIndexForward=False
    )
    
    if response['Items']:
        print(f"✓ Found {len(response['Items'])} sensor reading(s) in DynamoDB")
        print()
        print("Latest reading:")
        latest = response['Items'][0]
        print(f"  Farm ID: {latest.get('farmId')}")
        print(f"  Device ID: {latest.get('deviceId')}")
        print(f"  Timestamp: {latest.get('timestamp')}")
        print(f"  Soil Moisture: {latest.get('soilMoisture')}%")
        print(f"  Soil Temperature: {latest.get('soilTemperature')}°C")
        print(f"  Air Temperature: {latest.get('airTemperature')}°C")
        print(f"  Humidity: {latest.get('humidity')}%")
        print(f"  Validation Status: {latest.get('validationStatus')}")
    else:
        print("✗ No sensor data found in DynamoDB")
        print("  Check CloudWatch logs above for errors")
        
except Exception as e:
    print(f"✗ Error querying DynamoDB: {e}")

print()

# Step 6: Check S3 for archived data
print("Step 6: Checking S3 for archived data...")
try:
    now = datetime.now(timezone.utc)
    prefix = f"raw/year={now.year}/month={now.month:02d}/day={now.day:02d}/"
    
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=prefix,
        MaxKeys=10
    )
    
    if 'Contents' in response and response['Contents']:
        print(f"✓ Found {len(response['Contents'])} file(s) in S3")
        for obj in response['Contents']:
            print(f"  {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("⚠ No S3 data found yet (may take a moment)")
        
except Exception as e:
    print(f"⚠ Could not check S3: {e}")

print()
print("=" * 50)
print("Test Complete!")
print("=" * 50)
