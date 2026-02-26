"""
Farm Metadata API Lambda
Handles farm metadata CRUD operations
"""
import json
import os
from datetime import datetime
import boto3

dynamodb = boto3.resource('dynamodb')

FARM_METADATA_TABLE = os.environ['FARM_METADATA_TABLE']


def lambda_handler(event, context):
    """
    Main handler for farm metadata API
    Routes requests to appropriate handlers
    """
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {})
        farm_id = path_parameters.get('farmId')
        
        if not farm_id:
            return create_response(400, {'error': 'farmId is required'})
        
        if http_method == 'GET':
            return get_farm_metadata(farm_id)
        elif http_method == 'POST':
            body = json.loads(event['body'])
            return create_farm_metadata(farm_id, body)
        elif http_method == 'PUT':
            body = json.loads(event['body'])
            return update_farm_metadata(farm_id, body)
        else:
            return create_response(405, {'error': 'Method not allowed'})
            
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        print(f"Error in farm metadata API: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def create_response(status_code, body):
    """Create HTTP response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }


def get_farm_metadata(farm_id):
    """Get latest farm metadata"""
    table = dynamodb.Table(FARM_METADATA_TABLE)
    
    response = table.query(
        KeyConditionExpression='farmId = :farm_id',
        ExpressionAttributeValues={':farm_id': farm_id},
        ScanIndexForward=False,
        Limit=1
    )
    
    if not response.get('Items'):
        return create_response(404, {'error': 'Farm not found'})
    
    return create_response(200, response['Items'][0])


def create_farm_metadata(farm_id, metadata):
    """Create new farm metadata"""
    # Validate metadata
    validation_result = validate_metadata(metadata)
    if not validation_result['valid']:
        return create_response(400, {
            'error': 'Validation failed',
            'details': validation_result['errors']
        })
    
    table = dynamodb.Table(FARM_METADATA_TABLE)
    
    item = {
        'farmId': farm_id,
        'version': 1,
        'updatedAt': datetime.utcnow().isoformat(),
        **metadata
    }
    
    table.put_item(Item=item)
    
    return create_response(201, item)


def update_farm_metadata(farm_id, metadata):
    """Update farm metadata (creates new version)"""
    # Validate metadata
    validation_result = validate_metadata(metadata)
    if not validation_result['valid']:
        return create_response(400, {
            'error': 'Validation failed',
            'details': validation_result['errors']
        })
    
    table = dynamodb.Table(FARM_METADATA_TABLE)
    
    # Get latest version
    response = table.query(
        KeyConditionExpression='farmId = :farm_id',
        ExpressionAttributeValues={':farm_id': farm_id},
        ScanIndexForward=False,
        Limit=1
    )
    
    latest_version = response['Items'][0]['version'] if response.get('Items') else 0
    
    item = {
        'farmId': farm_id,
        'version': latest_version + 1,
        'updatedAt': datetime.utcnow().isoformat(),
        **metadata
    }
    
    table.put_item(Item=item)
    
    return create_response(200, item)


def validate_metadata(metadata):
    """Validate farm metadata ranges"""
    errors = []
    
    # Required fields check
    crop_type = metadata.get('cropType')
    if not crop_type:
        errors.append('cropType is required (cashew or coconut)')
    elif crop_type not in ['cashew', 'coconut']:
        errors.append('cropType must be either "cashew" or "coconut"')
    
    # Farm size: > 0 (required)
    farm_size = metadata.get('farmSizeHectares')
    if farm_size is None:
        errors.append('farmSizeHectares is required')
    elif farm_size <= 0:
        errors.append('farmSizeHectares must be greater than 0')
    
    # Tree age: 1-100 years (required)
    tree_age = metadata.get('treeAge')
    if tree_age is None:
        errors.append('treeAge is required')
    elif tree_age < 1 or tree_age > 100:
        errors.append('treeAge must be between 1 and 100 years')
    
    # Plantation density (required)
    density = metadata.get('plantationDensity')
    if density is None:
        errors.append('plantationDensity is required')
    elif density <= 0:
        errors.append('plantationDensity must be greater than 0')
    
    # Crop-specific validations
    if crop_type == 'cashew':
        # DBH: 1-200 cm (required for cashew)
        dbh = metadata.get('dbh')
        if dbh is None:
            errors.append('dbh is required for cashew trees')
        elif dbh < 1 or dbh > 200:
            errors.append('dbh must be between 1 and 200 cm')
    
    elif crop_type == 'coconut':
        # Tree height: 1-40 meters (required for coconut)
        tree_height = metadata.get('treeHeight')
        if tree_height is None:
            errors.append('treeHeight is required for coconut trees')
        elif tree_height < 1 or tree_height > 40:
            errors.append('treeHeight must be between 1 and 40 meters')
    
    # Fertilizer usage: >= 0 (optional)
    fertilizer = metadata.get('fertilizerUsage')
    if fertilizer is not None and fertilizer < 0:
        errors.append('fertilizerUsage must be >= 0 kg/hectare/year')
    
    # Irrigation activity: >= 0 (optional)
    irrigation = metadata.get('irrigationActivity')
    if irrigation is not None and irrigation < 0:
        errors.append('irrigationActivity must be >= 0 liters/hectare/year')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
