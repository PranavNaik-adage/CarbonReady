"""
Farm Metadata API Lambda
Handles farm metadata CRUD operations
"""
import json
import os
import traceback
from datetime import datetime
import boto3

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

FARM_METADATA_TABLE = os.environ['FARM_METADATA_TABLE']
CRITICAL_ALERTS_TOPIC = os.environ.get('CRITICAL_ALERTS_TOPIC', '')
WARNINGS_TOPIC = os.environ.get('WARNINGS_TOPIC', '')


def lambda_handler(event, context):
    """
    Main handler for farm metadata API
    Routes requests to appropriate handlers
    """
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {})
        farm_id = path_parameters.get('farmId')
        
        # Log incoming request
        print(json.dumps({
            "level": "INFO",
            "message": "Farm Metadata API request",
            "httpMethod": http_method,
            "farmId": farm_id,
            "requestId": context.request_id
        }))
        
        if not farm_id:
            return create_response(400, {'error': 'farmId is required'}, context)
        
        if http_method == 'GET':
            return get_farm_metadata(farm_id, context)
        elif http_method == 'POST':
            body = json.loads(event['body'])
            return create_farm_metadata(farm_id, body, context)
        elif http_method == 'PUT':
            body = json.loads(event['body'])
            return update_farm_metadata(farm_id, body, context)
        else:
            return create_response(405, {'error': 'Method not allowed'}, context)
            
    except json.JSONDecodeError:
        print(json.dumps({
            "level": "WARNING",
            "message": "Invalid JSON in request body",
            "requestId": context.request_id
        }))
        return create_response(400, {'error': 'Invalid JSON in request body'}, context)
    except Exception as e:
        # Log error with full context
        print(json.dumps({
            "level": "ERROR",
            "message": "Error in farm metadata API",
            "error": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc(),
            "httpMethod": event.get('httpMethod'),
            "farmId": event.get('pathParameters', {}).get('farmId'),
            "functionName": context.function_name,
            "requestId": context.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Send SNS notification for critical errors
        if CRITICAL_ALERTS_TOPIC:
            send_sns_notification(
                CRITICAL_ALERTS_TOPIC,
                "Farm Metadata API Lambda Error",
                f"Function: {context.function_name}\nError: {str(e)}\nRequestId: {context.request_id}"
            )
        
        return create_response(500, {'error': 'Internal server error'}, context)


def create_response(status_code, body, context):
    """Create HTTP response with CORS headers"""
    # Log response
    print(json.dumps({
        "level": "INFO" if status_code < 400 else "WARNING",
        "message": "API response",
        "statusCode": status_code,
        "requestId": context.request_id
    }))
    
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


def get_farm_metadata(farm_id, context):
    """Get latest farm metadata"""
    try:
        table = dynamodb.Table(FARM_METADATA_TABLE)
        
        response = table.query(
            KeyConditionExpression='farmId = :farm_id',
            ExpressionAttributeValues={':farm_id': farm_id},
            ScanIndexForward=False,
            Limit=1
        )
        
        if not response.get('Items'):
            return create_response(404, {'error': 'Farm not found'}, context)
        
        return create_response(200, response['Items'][0], context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error getting farm metadata",
            "error": str(e),
            "errorType": type(e).__name__,
            "farmId": farm_id,
            "requestId": context.request_id
        }))
        return create_response(500, {'error': 'Unable to retrieve farm metadata'}, context)


def create_farm_metadata(farm_id, metadata, context):
    """Create new farm metadata"""
    # Validate metadata
    validation_result = validate_metadata(metadata)
    if not validation_result['valid']:
        # Log validation errors
        print(json.dumps({
            "level": "WARNING",
            "message": "Farm metadata validation failed",
            "farmId": farm_id,
            "validationErrors": validation_result['errors'],
            "requestId": context.request_id
        }))
        
        return create_response(400, {
            'error': 'Validation failed',
            'details': validation_result['errors']
        }, context)
    
    try:
        table = dynamodb.Table(FARM_METADATA_TABLE)
        
        item = {
            'farmId': farm_id,
            'version': 1,
            'updatedAt': datetime.utcnow().isoformat(),
            **metadata
        }
        
        table.put_item(Item=item)
        
        # Log successful creation
        print(json.dumps({
            "level": "INFO",
            "message": "Farm metadata created successfully",
            "farmId": farm_id,
            "version": 1,
            "requestId": context.request_id
        }))
        
        return create_response(201, item, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error creating farm metadata",
            "error": str(e),
            "errorType": type(e).__name__,
            "farmId": farm_id,
            "requestId": context.request_id
        }))
        return create_response(500, {'error': 'Unable to create farm metadata'}, context)


def update_farm_metadata(farm_id, metadata, context):
    """Update farm metadata (creates new version)"""
    # Validate metadata
    validation_result = validate_metadata(metadata)
    if not validation_result['valid']:
        # Log validation errors
        print(json.dumps({
            "level": "WARNING",
            "message": "Farm metadata validation failed",
            "farmId": farm_id,
            "validationErrors": validation_result['errors'],
            "requestId": context.request_id
        }))
        
        return create_response(400, {
            'error': 'Validation failed',
            'details': validation_result['errors']
        }, context)
    
    try:
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
        
        # Log successful update
        print(json.dumps({
            "level": "INFO",
            "message": "Farm metadata updated successfully",
            "farmId": farm_id,
            "version": latest_version + 1,
            "requestId": context.request_id
        }))
        
        return create_response(200, item, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error updating farm metadata",
            "error": str(e),
            "errorType": type(e).__name__,
            "farmId": farm_id,
            "requestId": context.request_id
        }))
        return create_response(500, {'error': 'Unable to update farm metadata'}, context)


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
