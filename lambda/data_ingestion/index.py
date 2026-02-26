"""
Data Ingestion Lambda
Processes incoming sensor data from IoT Core
"""
import json
import os
import hashlib
import gzip
from datetime import datetime, timedelta
import boto3

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sns = boto3.client('sns')

SENSOR_DATA_TABLE = os.environ['SENSOR_DATA_TABLE']
SENSOR_CALIBRATION_TABLE = os.environ['SENSOR_CALIBRATION_TABLE']
SENSOR_DATA_BUCKET = os.environ['SENSOR_DATA_BUCKET']
CRITICAL_ALERTS_TOPIC = os.environ['CRITICAL_ALERTS_TOPIC']
WARNINGS_TOPIC = os.environ['WARNINGS_TOPIC']


def lambda_handler(event, context):
    """
    Main handler for data ingestion
    Validates sensor data, verifies hash, stores in DynamoDB and S3
    """
    try:
        # Parse incoming message
        payload = event
        
        # Verify cryptographic hash
        if not verify_hash(payload):
            log_tampering_alert(payload)
            send_sns_notification(
                CRITICAL_ALERTS_TOPIC,
                "Data tampering detected",
                f"Hash mismatch for farmId: {payload.get('farmId')}"
            )
            return {"status": "rejected", "reason": "hash_mismatch"}
        
        # Validate data ranges
        validation_result = validate_sensor_data(payload)
        if not validation_result['valid']:
            print(f"Validation failed: {validation_result['errors']}")
            return {"status": "rejected", "reason": "validation_failed", "errors": validation_result['errors']}
        
        # Check calibration status
        calibration_status = check_calibration_status(payload.get('deviceId'))
        if calibration_status['status'] != 'valid':
            print(f"Calibration check failed: {calibration_status}")
            return {"status": "rejected", "reason": "calibration_invalid"}
        
        # Store in DynamoDB (hot storage)
        store_in_dynamodb(payload)
        
        # Archive to S3 (cold storage)
        archive_to_s3(payload)
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Error processing sensor data: {str(e)}")
        send_sns_notification(
            CRITICAL_ALERTS_TOPIC,
            "Data Ingestion Lambda Error",
            f"Error: {str(e)}"
        )
        raise


def verify_hash(payload):
    """Verify SHA-256 hash of payload"""
    if 'hash' not in payload:
        return False
    
    received_hash = payload['hash']
    
    # Compute hash of payload (excluding hash field)
    payload_copy = payload.copy()
    payload_copy.pop('hash', None)
    payload_str = json.dumps(payload_copy, sort_keys=True)
    computed_hash = hashlib.sha256(payload_str.encode()).hexdigest()
    
    return received_hash == computed_hash


def validate_sensor_data(payload):
    """Validate sensor data ranges"""
    errors = []
    readings = payload.get('readings', {})
    
    # Soil moisture: 0-100%
    soil_moisture = readings.get('soilMoisture')
    if soil_moisture is not None and (soil_moisture < 0 or soil_moisture > 100):
        errors.append(f"soilMoisture out of range: {soil_moisture}")
    
    # Soil temperature: -10°C to 60°C
    soil_temp = readings.get('soilTemperature')
    if soil_temp is not None and (soil_temp < -10 or soil_temp > 60):
        errors.append(f"soilTemperature out of range: {soil_temp}")
    
    # Air temperature: -10°C to 60°C
    air_temp = readings.get('airTemperature')
    if air_temp is not None and (air_temp < -10 or air_temp > 60):
        errors.append(f"airTemperature out of range: {air_temp}")
    
    # Humidity: 0-100%
    humidity = readings.get('humidity')
    if humidity is not None and (humidity < 0 or humidity > 100):
        errors.append(f"humidity out of range: {humidity}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def check_calibration_status(device_id):
    """Check if sensor is calibrated"""
    table = dynamodb.Table(SENSOR_CALIBRATION_TABLE)
    
    try:
        response = table.query(
            KeyConditionExpression='deviceId = :device_id',
            ExpressionAttributeValues={':device_id': device_id},
            ScanIndexForward=False,
            Limit=1
        )
        
        if not response.get('Items'):
            return {"status": "uncalibrated", "action": "reject_data"}
        
        latest_calibration = response['Items'][0]
        calibration_date = datetime.fromisoformat(latest_calibration['calibrationDate'])
        days_since_calibration = (datetime.utcnow() - calibration_date).days
        
        if days_since_calibration > 365:
            return {"status": "expired", "action": "flag_data"}
        
        return {"status": "valid", "action": "accept_data"}
        
    except Exception as e:
        print(f"Error checking calibration: {str(e)}")
        return {"status": "error", "action": "reject_data"}


def store_in_dynamodb(payload):
    """Store sensor data in DynamoDB"""
    table = dynamodb.Table(SENSOR_DATA_TABLE)
    
    timestamp = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
    timestamp_unix = int(timestamp.timestamp())
    
    # Calculate TTL (90 days from now)
    ttl = int((datetime.utcnow() + timedelta(days=90)).timestamp())
    
    item = {
        'farmId': payload['farmId'],
        'timestamp': timestamp_unix,
        'deviceId': payload['deviceId'],
        'soilMoisture': payload['readings']['soilMoisture'],
        'soilTemperature': payload['readings']['soilTemperature'],
        'airTemperature': payload['readings']['airTemperature'],
        'humidity': payload['readings']['humidity'],
        'hash': payload['hash'],
        'validationStatus': 'valid',
        'ttl': ttl
    }
    
    table.put_item(Item=item)


def archive_to_s3(payload):
    """Archive sensor data to S3"""
    timestamp = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
    
    # Create S3 key with year/month/day partitioning
    s3_key = (
        f"raw/year={timestamp.year}/month={timestamp.month:02d}/day={timestamp.day:02d}/"
        f"farm-{payload['farmId']}-{int(timestamp.timestamp())}.json.gz"
    )
    
    # Compress data
    compressed_data = gzip.compress(json.dumps(payload).encode())
    
    # Upload to S3
    s3.put_object(
        Bucket=SENSOR_DATA_BUCKET,
        Key=s3_key,
        Body=compressed_data,
        ContentType='application/json',
        ContentEncoding='gzip'
    )


def log_tampering_alert(payload):
    """Log data tampering alert"""
    print(f"TAMPERING ALERT: Hash mismatch for farmId: {payload.get('farmId')}, deviceId: {payload.get('deviceId')}")


def send_sns_notification(topic_arn, subject, message):
    """Send SNS notification"""
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"Error sending SNS notification: {str(e)}")
