"""
Data Ingestion Lambda
Processes incoming sensor data from IoT Core
"""
import json
import os
import hashlib
import gzip
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal
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
        
        # Log incoming request
        print(json.dumps({
            "level": "INFO",
            "message": "Processing sensor data",
            "farmId": payload.get('farmId'),
            "deviceId": payload.get('deviceId'),
            "timestamp": payload.get('timestamp'),
            "requestId": context.request_id
        }))
        
        # Verify cryptographic hash
        if not verify_hash(payload):
            log_tampering_alert(payload, context)
            send_sns_notification(
                CRITICAL_ALERTS_TOPIC,
                "Data tampering detected",
                f"Hash mismatch for farmId: {payload.get('farmId')}, deviceId: {payload.get('deviceId')}"
            )
            return {"status": "rejected", "reason": "hash_mismatch"}
        
        # Validate data ranges
        validation_result = validate_sensor_data(payload)
        if not validation_result['valid']:
            log_validation_error(payload, validation_result['errors'], context)
            return {"status": "rejected", "reason": "validation_failed", "errors": validation_result['errors']}
        
        # Check calibration status
        calibration_status = check_calibration_status(payload.get('deviceId'))
        if calibration_status['status'] != 'valid':
            log_calibration_error(payload, calibration_status, context)
            return {"status": "rejected", "reason": "calibration_invalid"}
        
        # Store in DynamoDB (hot storage)
        store_in_dynamodb(payload)
        
        # Archive to S3 (cold storage)
        archive_to_s3(payload)
        
        # Log success
        print(json.dumps({
            "level": "INFO",
            "message": "Successfully processed sensor data",
            "farmId": payload.get('farmId'),
            "deviceId": payload.get('deviceId'),
            "requestId": context.request_id
        }))
        
        return {"status": "success"}
        
    except Exception as e:
        # Log error with full context
        error_details = {
            "level": "ERROR",
            "message": "Error processing sensor data",
            "error": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc(),
            "farmId": event.get('farmId'),
            "deviceId": event.get('deviceId'),
            "functionName": context.function_name,
            "requestId": context.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(json.dumps(error_details))
        
        # Send SNS notification for critical errors
        send_sns_notification(
            CRITICAL_ALERTS_TOPIC,
            "Data Ingestion Lambda Error",
            f"Function: {context.function_name}\nError: {str(e)}\nFarmId: {event.get('farmId')}\nRequestId: {context.request_id}"
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
        
        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        if calibration_date.tzinfo is None:
            calibration_date = calibration_date.replace(tzinfo=timezone.utc)
        
        days_since_calibration = (now - calibration_date).days
        
        if days_since_calibration > 365:
            # Send notification for calibration expiry
            send_sns_notification(
                WARNINGS_TOPIC,
                "Sensor Calibration Expired",
                f"Device {device_id} requires recalibration. Last calibrated {days_since_calibration} days ago."
            )
            return {"status": "expired", "action": "flag_data"}
        
        return {"status": "valid", "action": "accept_data"}
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error checking calibration",
            "error": str(e),
            "errorType": type(e).__name__,
            "deviceId": device_id
        }))
        return {"status": "error", "action": "reject_data"}


def store_in_dynamodb(payload):
    """Store sensor data in DynamoDB"""
    table = dynamodb.Table(SENSOR_DATA_TABLE)
    
    timestamp = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
    timestamp_unix = int(timestamp.timestamp())
    
    # Calculate TTL (90 days from now)
    ttl = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
    
    # Convert float values to Decimal for DynamoDB
    item = {
        'farmId': payload['farmId'],
        'timestamp': timestamp_unix,
        'deviceId': payload['deviceId'],
        'soilMoisture': Decimal(str(payload['readings']['soilMoisture'])),
        'soilTemperature': Decimal(str(payload['readings']['soilTemperature'])),
        'airTemperature': Decimal(str(payload['readings']['airTemperature'])),
        'humidity': Decimal(str(payload['readings']['humidity'])),
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


def log_tampering_alert(payload, context):
    """Log data tampering alert with full context"""
    alert_details = {
        "level": "CRITICAL",
        "message": "Data tampering detected - hash mismatch",
        "farmId": payload.get('farmId'),
        "deviceId": payload.get('deviceId'),
        "timestamp": payload.get('timestamp'),
        "receivedHash": payload.get('hash'),
        "functionName": context.function_name,
        "requestId": context.request_id,
        "alertTimestamp": datetime.utcnow().isoformat()
    }
    print(json.dumps(alert_details))


def log_validation_error(payload, errors, context):
    """Log data validation errors with full context"""
    error_details = {
        "level": "WARNING",
        "message": "Data validation failed",
        "farmId": payload.get('farmId'),
        "deviceId": payload.get('deviceId'),
        "timestamp": payload.get('timestamp'),
        "validationErrors": errors,
        "readings": payload.get('readings'),
        "functionName": context.function_name,
        "requestId": context.request_id,
        "alertTimestamp": datetime.utcnow().isoformat()
    }
    print(json.dumps(error_details))


def log_calibration_error(payload, calibration_status, context):
    """Log calibration errors with full context"""
    error_details = {
        "level": "WARNING",
        "message": "Calibration check failed",
        "farmId": payload.get('farmId'),
        "deviceId": payload.get('deviceId'),
        "calibrationStatus": calibration_status,
        "functionName": context.function_name,
        "requestId": context.request_id,
        "alertTimestamp": datetime.utcnow().isoformat()
    }
    print(json.dumps(error_details))


def send_sns_notification(topic_arn, subject, message):
    """Send SNS notification"""
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Failed to send SNS notification",
            "error": str(e),
            "errorType": type(e).__name__,
            "topicArn": topic_arn,
            "subject": subject
        }))
