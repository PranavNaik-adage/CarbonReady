"""
Unit tests for Data Ingestion Lambda
"""
import json
import os
import hashlib
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Set environment variables before importing
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['SENSOR_DATA_TABLE'] = 'test-sensor-data'
os.environ['SENSOR_CALIBRATION_TABLE'] = 'test-sensor-calibration'
os.environ['SENSOR_DATA_BUCKET'] = 'test-sensor-bucket'
os.environ['CRITICAL_ALERTS_TOPIC'] = 'arn:aws:sns:us-east-1:123456789012:test-critical'
os.environ['WARNINGS_TOPIC'] = 'arn:aws:sns:us-east-1:123456789012:test-warnings'

from index import (
    lambda_handler,
    verify_hash,
    validate_sensor_data,
    check_calibration_status
)


def create_mock_context():
    """Create a mock Lambda context object"""
    context = Mock()
    context.request_id = 'test-request-id-12345'
    context.function_name = 'test-data-ingestion'
    context.function_version = '$LATEST'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
    context.memory_limit_in_mb = 512
    context.aws_request_id = 'test-request-id-12345'
    return context


def create_test_payload(readings=None):
    """Helper to create test payload with valid hash"""
    if readings is None:
        readings = {
            'soilMoisture': 45.5,
            'soilTemperature': 25.3,
            'airTemperature': 28.7,
            'humidity': 65.2
        }
    
    payload = {
        'farmId': 'farm-001',
        'deviceId': 'esp32-farm-001',
        'timestamp': '2025-01-15T10:30:00Z',
        'readings': readings
    }
    
    # Compute hash
    payload_str = json.dumps(payload, sort_keys=True)
    payload['hash'] = hashlib.sha256(payload_str.encode()).hexdigest()
    
    return payload


def test_verify_hash_valid():
    """Test hash verification with valid hash"""
    payload = create_test_payload()
    assert verify_hash(payload) is True


def test_verify_hash_invalid():
    """Test hash verification with invalid hash"""
    payload = create_test_payload()
    payload['hash'] = 'invalid_hash'
    assert verify_hash(payload) is False


def test_verify_hash_missing():
    """Test hash verification with missing hash"""
    payload = create_test_payload()
    del payload['hash']
    assert verify_hash(payload) is False


def test_validate_sensor_data_valid():
    """Test validation with valid sensor data"""
    payload = create_test_payload()
    result = validate_sensor_data(payload)
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_sensor_data_soil_moisture_out_of_range():
    """Test validation with soil moisture out of range"""
    # Test below range
    payload = create_test_payload({'soilMoisture': -5, 'soilTemperature': 25, 'airTemperature': 28, 'humidity': 65})
    result = validate_sensor_data(payload)
    assert result['valid'] is False
    assert any('soilMoisture' in error for error in result['errors'])
    
    # Test above range
    payload = create_test_payload({'soilMoisture': 105, 'soilTemperature': 25, 'airTemperature': 28, 'humidity': 65})
    result = validate_sensor_data(payload)
    assert result['valid'] is False
    assert any('soilMoisture' in error for error in result['errors'])


def test_validate_sensor_data_temperature_out_of_range():
    """Test validation with temperature out of range"""
    # Soil temperature below range
    payload = create_test_payload({'soilMoisture': 45, 'soilTemperature': -15, 'airTemperature': 28, 'humidity': 65})
    result = validate_sensor_data(payload)
    assert result['valid'] is False
    assert any('soilTemperature' in error for error in result['errors'])
    
    # Air temperature above range
    payload = create_test_payload({'soilMoisture': 45, 'soilTemperature': 25, 'airTemperature': 65, 'humidity': 65})
    result = validate_sensor_data(payload)
    assert result['valid'] is False
    assert any('airTemperature' in error for error in result['errors'])


def test_validate_sensor_data_humidity_out_of_range():
    """Test validation with humidity out of range"""
    payload = create_test_payload({'soilMoisture': 45, 'soilTemperature': 25, 'airTemperature': 28, 'humidity': 105})
    result = validate_sensor_data(payload)
    assert result['valid'] is False
    assert any('humidity' in error for error in result['errors'])


@patch('index.dynamodb')
def test_check_calibration_status_valid(mock_dynamodb):
    """Test calibration check with valid calibration"""
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock recent calibration
    mock_table.query.return_value = {
        'Items': [{
            'deviceId': 'esp32-farm-001',
            'calibrationDate': datetime.utcnow().isoformat()
        }]
    }
    
    result = check_calibration_status('esp32-farm-001')
    assert result['status'] == 'valid'


@patch('index.dynamodb')
def test_check_calibration_status_uncalibrated(mock_dynamodb):
    """Test calibration check with uncalibrated sensor"""
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock no calibration records
    mock_table.query.return_value = {'Items': []}
    
    result = check_calibration_status('esp32-farm-001')
    assert result['status'] == 'uncalibrated'


@patch('index.dynamodb')
def test_check_calibration_status_expired(mock_dynamodb):
    """Test calibration check with expired calibration"""
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock old calibration (400 days ago)
    from datetime import timedelta
    old_date = datetime.utcnow() - timedelta(days=400)
    mock_table.query.return_value = {
        'Items': [{
            'deviceId': 'esp32-farm-001',
            'calibrationDate': old_date.isoformat()
        }]
    }
    
    result = check_calibration_status('esp32-farm-001')
    assert result['status'] == 'expired'


@patch('index.sns')
@patch('index.s3')
@patch('index.dynamodb')
def test_lambda_handler_success(mock_dynamodb, mock_s3, mock_sns):
    """Test successful data ingestion"""
    # Setup mocks
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock calibration check
    mock_table.query.return_value = {
        'Items': [{
            'deviceId': 'esp32-farm-001',
            'calibrationDate': datetime.utcnow().isoformat()
        }]
    }
    
    # Create valid payload
    event = create_test_payload()
    context = create_mock_context()
    
    result = lambda_handler(event, context)
    
    assert result['status'] == 'success'
    mock_table.put_item.assert_called_once()
    mock_s3.put_object.assert_called_once()


@patch('index.sns')
@patch('index.dynamodb')
def test_lambda_handler_hash_mismatch(mock_dynamodb, mock_sns):
    """Test data ingestion with hash mismatch"""
    event = create_test_payload()
    event['hash'] = 'invalid_hash'
    
    context = create_mock_context()
    
    result = lambda_handler(event, context)
    
    assert result['status'] == 'rejected'
    assert result['reason'] == 'hash_mismatch'
    mock_sns.publish.assert_called_once()


@patch('index.dynamodb')
def test_lambda_handler_validation_failed(mock_dynamodb):
    """Test data ingestion with validation failure"""
    event = create_test_payload({'soilMoisture': 150, 'soilTemperature': 25, 'airTemperature': 28, 'humidity': 65})
    context = create_mock_context()
    
    result = lambda_handler(event, context)
    
    assert result['status'] == 'rejected'
    assert result['reason'] == 'validation_failed'


@patch('index.dynamodb')
def test_lambda_handler_calibration_invalid(mock_dynamodb):
    """Test data ingestion with invalid calibration"""
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock uncalibrated sensor
    mock_table.query.return_value = {'Items': []}
    
    event = create_test_payload()
    context = create_mock_context()
    
    result = lambda_handler(event, context)
    
    assert result['status'] == 'rejected'
    assert result['reason'] == 'calibration_invalid'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
