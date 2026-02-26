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
        
        if http_method == 'GET':
            return get_farm_metadata(farm_id)
        elif http_method == 'POST':
            body = json.loads(event['body'])
            return create_farm_metadata(farm_id, body)
        elif http_method == 'PUT':
            body = json.loads(event['body'])
            return update_farm_metadata(farm_id, body)
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        print(f"Error in farm metadata API: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
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
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Farm not found'})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps(response['Items'][0], default=str)
    }


def create_farm_metadata(farm_id, metadata):
    """Create new farm metadata"""
    # Validate metadata
    validation_result = validate_metadata(metadata)
    if not validation_result['valid']:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Validation failed',
                'details': validation_result['errors']
            })
        }
    
    table = dynamodb.Table(FARM_METADATA_TABLE)
    
    item = {
        'farmId': farm_id,
        'version': 1,
        'updatedAt': datetime.utcnow().isoformat(),
        **metadata
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 201,
        'body': json.dumps(item, default=str)
    }


def update_farm_metadata(farm_id, metadata):
    """Update farm metadata (creates new version)"""
    # Validate metadata
    validation_result = validate_metadata(metadata)
    if not validation_result['valid']:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Validation failed',
                'details': validation_result['errors']
            })
        }
    
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
    
    return {
        'statusCode': 200,
        'body': json.dumps(item, default=str)
    }


def validate_metadata(metadata):
    """Validate farm metadata ranges"""
    errors = []
    
    # Tree age: 1-100 years
    tree_age = metadata.get('treeAge')
    if tree_age is not None and (tree_age < 1 or tree_age > 100):
        errors.append('treeAge must be between 1 and 100 years')
    
    # DBH: 1-200 cm (for cashew)
    dbh = metadata.get('dbh')
    if dbh is not None and (dbh < 1 or dbh > 200):
        errors.append('dbh must be between 1 and 200 cm')
    
    # Tree height: 1-40 meters (for coconut)
    tree_height = metadata.get('treeHeight')
    if tree_height is not None and (tree_height < 1 or tree_height > 40):
        errors.append('treeHeight must be between 1 and 40 meters')
    
    # Farm size: > 0
    farm_size = metadata.get('farmSizeHectares')
    if farm_size is not None and farm_size <= 0:
        errors.append('farmSizeHectares must be greater than 0')
    
    # Fertilizer usage: >= 0
    fertilizer = metadata.get('fertilizerUsage')
    if fertilizer is not None and fertilizer < 0:
        errors.append('fertilizerUsage must be >= 0')
    
    # Irrigation activity: >= 0
    irrigation = metadata.get('irrigationActivity')
    if irrigation is not None and irrigation < 0:
        errors.append('irrigationActivity must be >= 0')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
