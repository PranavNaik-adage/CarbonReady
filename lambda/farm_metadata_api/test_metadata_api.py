"""
Unit tests for Farm Metadata API
"""
import json
import os
import pytest
from unittest.mock import Mock, patch

# Set environment variables before importing
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['FARM_METADATA_TABLE'] = 'test-farm-metadata'

from index import (
    lambda_handler,
    validate_metadata,
    create_response
)


def test_validate_metadata_valid_cashew():
    """Test validation with valid cashew metadata"""
    metadata = {
        'cropType': 'cashew',
        'farmSizeHectares': 2.5,
        'treeAge': 15,
        'dbh': 25.5,
        'plantationDensity': 200,
        'fertilizerUsage': 50.0,
        'irrigationActivity': 10000.0
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_metadata_valid_coconut():
    """Test validation with valid coconut metadata"""
    metadata = {
        'cropType': 'coconut',
        'farmSizeHectares': 3.0,
        'treeAge': 20,
        'treeHeight': 12.5,
        'plantationDensity': 150,
        'fertilizerUsage': 60.0,
        'irrigationActivity': 15000.0
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_metadata_missing_crop_type():
    """Test validation with missing crop type"""
    metadata = {
        'farmSizeHectares': 2.5,
        'treeAge': 15,
        'plantationDensity': 200
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is False
    assert any('cropType is required' in error for error in result['errors'])


def test_validate_metadata_invalid_tree_age():
    """Test validation with invalid tree age"""
    metadata = {
        'cropType': 'cashew',
        'farmSizeHectares': 2.5,
        'treeAge': 150,  # Invalid: > 100
        'dbh': 25.5,
        'plantationDensity': 200
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is False
    assert any('treeAge' in error for error in result['errors'])


def test_validate_metadata_invalid_dbh():
    """Test validation with invalid DBH"""
    metadata = {
        'cropType': 'cashew',
        'farmSizeHectares': 2.5,
        'treeAge': 15,
        'dbh': 250,  # Invalid: > 200
        'plantationDensity': 200
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is False
    assert any('dbh' in error for error in result['errors'])


def test_validate_metadata_invalid_tree_height():
    """Test validation with invalid tree height"""
    metadata = {
        'cropType': 'coconut',
        'farmSizeHectares': 3.0,
        'treeAge': 20,
        'treeHeight': 50,  # Invalid: > 40
        'plantationDensity': 150
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is False
    assert any('treeHeight' in error for error in result['errors'])


def test_validate_metadata_invalid_farm_size():
    """Test validation with invalid farm size"""
    metadata = {
        'cropType': 'cashew',
        'farmSizeHectares': -1,  # Invalid: <= 0
        'treeAge': 15,
        'dbh': 25.5,
        'plantationDensity': 200
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is False
    assert any('farmSizeHectares' in error for error in result['errors'])


def test_validate_metadata_missing_dbh_for_cashew():
    """Test validation with missing DBH for cashew"""
    metadata = {
        'cropType': 'cashew',
        'farmSizeHectares': 2.5,
        'treeAge': 15,
        'plantationDensity': 200
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is False
    assert any('dbh is required' in error for error in result['errors'])


def test_validate_metadata_missing_height_for_coconut():
    """Test validation with missing height for coconut"""
    metadata = {
        'cropType': 'coconut',
        'farmSizeHectares': 3.0,
        'treeAge': 20,
        'plantationDensity': 150
    }
    
    result = validate_metadata(metadata)
    assert result['valid'] is False
    assert any('treeHeight is required' in error for error in result['errors'])


def test_create_response():
    """Test response creation with CORS headers"""
    response = create_response(200, {'message': 'success'})
    
    assert response['statusCode'] == 200
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    assert 'Content-Type' in response['headers']
    
    body = json.loads(response['body'])
    assert body['message'] == 'success'


@patch('index.dynamodb')
def test_lambda_handler_missing_farm_id(mock_dynamodb):
    """Test handler with missing farmId"""
    event = {
        'httpMethod': 'GET',
        'pathParameters': {}
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
    
    body = json.loads(response['body'])
    assert 'farmId is required' in body['error']


@patch('index.dynamodb')
def test_lambda_handler_invalid_method(mock_dynamodb):
    """Test handler with invalid HTTP method"""
    event = {
        'httpMethod': 'DELETE',
        'pathParameters': {'farmId': 'farm-001'}
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 405


@patch('index.dynamodb')
def test_lambda_handler_invalid_json(mock_dynamodb):
    """Test handler with invalid JSON body"""
    event = {
        'httpMethod': 'POST',
        'pathParameters': {'farmId': 'farm-001'},
        'body': 'invalid json'
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
    
    body = json.loads(response['body'])
    assert 'Invalid JSON' in body['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
