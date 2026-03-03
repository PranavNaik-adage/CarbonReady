"""
Dashboard API Lambda
Serves carbon intelligence data to web dashboard
"""
import json
import os
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

CARBON_CALCULATIONS_TABLE = os.environ['CARBON_CALCULATIONS_TABLE']
SENSOR_DATA_TABLE = os.environ['SENSOR_DATA_TABLE']
CRI_WEIGHTS_TABLE = os.environ['CRI_WEIGHTS_TABLE']
CRITICAL_ALERTS_TOPIC = os.environ.get('CRITICAL_ALERTS_TOPIC', '')
WARNINGS_TOPIC = os.environ.get('WARNINGS_TOPIC', '')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Main handler for dashboard API
    Routes requests to appropriate handlers
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        path_parameters = event.get('pathParameters', {})
        farm_id = path_parameters.get('farmId')
        
        # Log incoming request
        print(json.dumps({
            "level": "INFO",
            "message": "Dashboard API request",
            "httpMethod": http_method,
            "path": path,
            "farmId": farm_id,
            "requestId": context.aws_request_id
        }))
        
        # Route to appropriate handler
        if 'carbon-position' in path:
            return get_carbon_position(farm_id, context)
        elif 'carbon-readiness-index' in path:
            return get_carbon_readiness_index(farm_id, context)
        elif 'sensor-data/latest' in path:
            return get_latest_sensor_data(farm_id, context)
        elif 'historical-trends' in path:
            query_params = event.get('queryStringParameters', {}) or {}
            days = int(query_params.get('days', 365))
            return get_historical_trends(farm_id, days, context)
        elif 'admin/cri-weights' in path:
            if http_method == 'GET':
                return get_cri_weights(context)
            elif http_method == 'PUT':
                body = json.loads(event['body'])
                return update_cri_weights(body, event, context)
        else:
            return error_response(404, 'ENDPOINT_NOT_FOUND', 'The requested endpoint was not found', context)
            
    except ValueError as e:
        return error_response(400, 'INVALID_INPUT', str(e), context)
    except Exception as e:
        # Log error with full context
        print(json.dumps({
            "level": "ERROR",
            "message": "Error in dashboard API",
            "error": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc(),
            "httpMethod": event.get('httpMethod'),
            "path": event.get('path'),
            "functionName": context.function_name,
            "requestId": context.aws_request_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Send SNS notification for critical errors
        if CRITICAL_ALERTS_TOPIC:
            send_sns_notification(
                CRITICAL_ALERTS_TOPIC,
                "Dashboard API Lambda Error",
                f"Function: {context.function_name}\nError: {str(e)}\nPath: {event.get('path')}\nRequestId: {context.aws_request_id}"
            )
        
        return error_response(500, 'INTERNAL_ERROR', 'An unexpected error occurred. Please try again later.', context)


def error_response(status_code, error_code, message, context, details=None):
    """Generate standardized error response"""
    error_body = {
        'error': {
            'code': error_code,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    }
    if details:
        error_body['error']['details'] = details
    
    # Log error
    print(json.dumps({
        "level": "WARNING" if status_code < 500 else "ERROR",
        "message": "API error response",
        "statusCode": status_code,
        "errorCode": error_code,
        "errorMessage": message,
        "requestId": context.aws_request_id
    }))
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(error_body)
    }


def success_response(data, context):
    """Generate standardized success response"""
    print(json.dumps({
        "level": "INFO",
        "message": "API success response",
        "requestId": context.aws_request_id
    }))
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data, cls=DecimalEncoder)
    }


def get_carbon_position(farm_id, context):
    """
    Get latest carbon position for farm
    Returns net carbon position, sequestration, and emissions
    """
    try:
        table = dynamodb.Table(CARBON_CALCULATIONS_TABLE)
        
        # Query for latest calculation
        response = table.query(
            KeyConditionExpression=Key('farmId').eq(farm_id),
            ScanIndexForward=False,  # Sort descending by calculatedAt
            Limit=1
        )
        
        if not response['Items']:
            return error_response(404, 'NO_DATA', f'No carbon calculations found for farm {farm_id}', context)
        
        calculation = response['Items'][0]
        
        # Check data staleness (> 24 hours)
        calculated_at = datetime.fromisoformat(calculation['calculatedAt'].replace('Z', '+00:00'))
        is_stale = (datetime.utcnow() - calculated_at.replace(tzinfo=None)) > timedelta(hours=24)
        
        result = {
            'farmId': farm_id,
            'netCarbonPosition': calculation['netCarbonPosition'],
            'annualSequestration': calculation['annualSequestration'],
            'emissions': calculation['emissions'],
            'classification': 'Net Carbon Sink' if calculation['netCarbonPosition'] > 0 else 'Net Carbon Source',
            'carbonStock': calculation['carbonStock'],
            'co2EquivalentStock': calculation['co2EquivalentStock'],
            'calculatedAt': calculation['calculatedAt'],
            'isStale': is_stale,
            'unit': 'kg CO2e/year'
        }
        
        return success_response(result, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error getting carbon position",
            "error": str(e),
            "errorType": type(e).__name__,
            "farmId": farm_id,
            "requestId": context.aws_request_id
        }))
        return error_response(500, 'QUERY_ERROR', 'Unable to retrieve carbon position data', context)


def get_carbon_readiness_index(farm_id, context):
    """
    Get Carbon Readiness Index with full breakdown
    Shows component contributions and weights for transparency
    """
    try:
        table = dynamodb.Table(CARBON_CALCULATIONS_TABLE)
        
        # Query for latest calculation
        response = table.query(
            KeyConditionExpression=Key('farmId').eq(farm_id),
            ScanIndexForward=False,
            Limit=1
        )
        
        if not response['Items']:
            return error_response(404, 'NO_DATA', f'No carbon calculations found for farm {farm_id}', context)
        
        calculation = response['Items'][0]
        
        # CRI is stored as a simple number, not a map
        cri_score = calculation.get('carbonReadinessIndex')
        if not cri_score:
            return error_response(404, 'NO_CRI_DATA', 'Carbon Readiness Index not yet calculated for this farm', context)
        
        # Get components and weights
        cri_components = calculation.get('criComponents', {})
        cri_weights = calculation.get('criWeights', {})
        cri_classification = calculation.get('criClassification', 'Unknown')
        
        # Build detailed breakdown response
        result = {
            'farmId': farm_id,
            'carbonReadinessIndex': {
                'score': float(cri_score),
                'classification': cri_classification,
                'components': {
                    'netCarbonPosition': {
                        'score': float(cri_components.get('netCarbonPosition', 0)),
                        'weight': float(cri_weights.get('netCarbonPosition', 0)),
                        'contribution': round(
                            float(cri_components.get('netCarbonPosition', 0)) * 
                            float(cri_weights.get('netCarbonPosition', 0)), 
                            2
                        )
                    },
                    'socTrend': {
                        'score': float(cri_components.get('socTrend', 0)),
                        'weight': float(cri_weights.get('socTrend', 0)),
                        'contribution': round(
                            float(cri_components.get('socTrend', 0)) * 
                            float(cri_weights.get('socTrend', 0)), 
                            2
                        )
                    },
                    'managementPractices': {
                        'score': float(cri_components.get('managementPractices', 0)),
                        'weight': float(cri_weights.get('managementPractices', 0)),
                        'contribution': round(
                            float(cri_components.get('managementPractices', 0)) * 
                            float(cri_weights.get('managementPractices', 0)), 
                            2
                        )
                    }
                },
                'scoringLogicVersion': calculation.get('modelVersions', {}).get('cri', 'v1.0.0'),
                'calculatedAt': calculation['calculatedAt']
            },
            'socTrend': {
                'status': calculation.get('socTrend', 'Unknown'),
                'score': 0,
                'biomassReturn': 0,
                'managementScore': 0,
                'dataSpanDays': 0
            },
            'netCarbonPosition': float(calculation.get('netCarbonPosition', 0))
        }
        
        return success_response(result, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error getting CRI",
            "error": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc(),
            "farmId": farm_id,
            "requestId": context.aws_request_id
        }))
        return error_response(500, 'QUERY_ERROR', 'Unable to retrieve Carbon Readiness Index data', context)


def get_latest_sensor_data(farm_id, context):
    """
    Get latest sensor readings for farm
    Returns most recent readings for all sensor types
    """
    try:
        table = dynamodb.Table(SENSOR_DATA_TABLE)
        
        # Query for latest sensor data
        response = table.query(
            KeyConditionExpression=Key('farmId').eq(farm_id),
            ScanIndexForward=False,  # Sort descending by timestamp
            Limit=1
        )
        
        if not response['Items']:
            return error_response(404, 'NO_DATA', f'No sensor data found for farm {farm_id}', context)
        
        sensor_data = response['Items'][0]
        
        # Convert timestamp to ISO format (handle Decimal)
        timestamp_value = float(sensor_data['timestamp'])
        timestamp = datetime.utcfromtimestamp(timestamp_value).isoformat() + 'Z'
        
        result = {
            'farmId': farm_id,
            'deviceId': sensor_data.get('deviceId'),
            'timestamp': timestamp,
            'readings': {
                'soilMoisture': float(sensor_data.get('soilMoisture', 0)),
                'soilTemperature': float(sensor_data.get('soilTemperature', 0)),
                'airTemperature': float(sensor_data.get('airTemperature', 0)),
                'humidity': float(sensor_data.get('humidity', 0))
            },
            'validationStatus': sensor_data.get('validationStatus', 'valid')
        }
        
        return success_response(result, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error getting sensor data",
            "error": str(e),
            "errorType": type(e).__name__,
            "farmId": farm_id,
            "requestId": context.aws_request_id
        }))
        return error_response(500, 'QUERY_ERROR', 'Unable to retrieve sensor data', context)


def get_historical_trends(farm_id, days, context):
    """
    Get historical carbon trends for specified time period
    Returns time series of carbon calculations
    """
    try:
        if days < 1 or days > 365:
            return error_response(400, 'INVALID_DAYS', 'Days parameter must be between 1 and 365', context)
        
        table = dynamodb.Table(CARBON_CALCULATIONS_TABLE)
        
        # Calculate cutoff date
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
        
        # Query for calculations within time range
        response = table.query(
            KeyConditionExpression=Key('farmId').eq(farm_id) & Key('calculatedAt').gte(cutoff_date),
            ScanIndexForward=True  # Sort ascending by date
        )
        
        if not response['Items']:
            return error_response(404, 'NO_DATA', f'No historical data found for farm {farm_id} in the last {days} days', context)
        
        # Build time series data
        trends = []
        for item in response['Items']:
            # Handle both old and new data structures
            cri_score = item.get('carbonReadinessIndex')
            if isinstance(cri_score, dict):
                cri_score = cri_score.get('score')
            
            soc_trend = item.get('socTrend')
            if isinstance(soc_trend, dict):
                soc_trend = soc_trend.get('status')
            
            # Get emissions - handle both structures
            emissions = item.get('emissions')
            if isinstance(emissions, dict):
                total_emissions = emissions.get('totalEmissions', 0)
            else:
                total_emissions = emissions or 0
            
            trends.append({
                'date': item['calculatedAt'],
                'netCarbonPosition': float(item.get('netCarbonPosition', 0)),
                'annualSequestration': float(item.get('annualSequestration', 0)),
                'totalEmissions': float(total_emissions),
                'carbonReadinessIndex': float(cri_score) if cri_score else None,
                'socTrend': soc_trend
            })
        
        result = {
            'farmId': farm_id,
            'days': days,
            'dataPoints': len(trends),
            'trends': trends
        }
        
        return success_response(result, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error getting historical trends",
            "error": str(e),
            "errorType": type(e).__name__,
            "farmId": farm_id,
            "days": days,
            "requestId": context.aws_request_id
        }))
        return error_response(500, 'QUERY_ERROR', 'Unable to retrieve historical trends', context)


def get_cri_weights(context):
    """
    Get current CRI weighting configuration
    Returns the active weights used for CRI calculation
    """
    try:
        table = dynamodb.Table(CRI_WEIGHTS_TABLE)
        
        # Query for latest weights configuration
        response = table.query(
            KeyConditionExpression=Key('configId').eq('default'),
            ScanIndexForward=False,  # Sort descending by version
            Limit=1
        )
        
        if not response['Items']:
            # Return default weights if none configured
            result = {
                'configId': 'default',
                'version': 0,
                'weights': {
                    'netCarbonPosition': 0.5,
                    'socTrend': 0.3,
                    'managementPractices': 0.2
                },
                'updatedAt': None,
                'updatedBy': 'system'
            }
        else:
            weights_config = response['Items'][0]
            result = {
                'configId': weights_config['configId'],
                'version': weights_config['version'],
                'weights': {
                    'netCarbonPosition': weights_config['netCarbonPosition'],
                    'socTrend': weights_config['socTrend'],
                    'managementPractices': weights_config['managementPractices']
                },
                'updatedAt': weights_config.get('updatedAt'),
                'updatedBy': weights_config.get('updatedBy')
            }
        
        return success_response(result, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error getting CRI weights",
            "error": str(e),
            "errorType": type(e).__name__,
            "requestId": context.aws_request_id
        }))
        return error_response(500, 'QUERY_ERROR', 'Unable to retrieve CRI weights', context)


def update_cri_weights(weights, event, context):
    """
    Update CRI weights (admin only)
    Validates admin role and weight sum before updating
    """
    try:
        # Extract user information from Cognito authorizer
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        # Check for admin role
        user_groups = claims.get('cognito:groups', '')
        if isinstance(user_groups, str):
            user_groups = user_groups.split(',') if user_groups else []
        
        if 'admin' not in user_groups:
            # Log unauthorized attempt
            username = claims.get('cognito:username', 'unknown')
            print(json.dumps({
                "level": "WARNING",
                "message": "Unauthorized CRI weight modification attempt",
                "username": username,
                "requestId": context.aws_request_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
            return error_response(
                403, 
                'UNAUTHORIZED', 
                'Administrative privileges required to modify CRI weights',
                context
            )
        
        # Validate weights structure
        required_keys = {'netCarbonPosition', 'socTrend', 'managementPractices'}
        if not all(key in weights for key in required_keys):
            return error_response(
                400,
                'INVALID_WEIGHTS',
                'All weight components must be provided',
                context,
                {'required': list(required_keys), 'provided': list(weights.keys())}
            )
        
        # Validate weights are numeric and positive
        for key in required_keys:
            if not isinstance(weights[key], (int, float)) or weights[key] < 0:
                return error_response(
                    400,
                    'INVALID_WEIGHT_VALUE',
                    f'Weight {key} must be a non-negative number',
                    context
                )
        
        # Validate weights sum to 1.0 (with tolerance for floating point)
        weight_sum = sum(weights[key] for key in required_keys)
        if abs(weight_sum - 1.0) > 0.001:
            return error_response(
                400,
                'INVALID_WEIGHT_SUM',
                'Weights must sum to 1.0 (100%)',
                context,
                {'sum': weight_sum, 'expected': 1.0}
            )
        
        # Get current version
        table = dynamodb.Table(CRI_WEIGHTS_TABLE)
        response = table.query(
            KeyConditionExpression=Key('configId').eq('default'),
            ScanIndexForward=False,
            Limit=1
        )
        
        current_version = response['Items'][0]['version'] if response['Items'] else 0
        new_version = current_version + 1
        
        # Store new weights configuration
        username = claims.get('cognito:username', 'unknown')
        table.put_item(
            Item={
                'configId': 'default',
                'version': new_version,
                'netCarbonPosition': Decimal(str(weights['netCarbonPosition'])),
                'socTrend': Decimal(str(weights['socTrend'])),
                'managementPractices': Decimal(str(weights['managementPractices'])),
                'updatedAt': datetime.utcnow().isoformat() + 'Z',
                'updatedBy': username
            }
        )
        
        # Log successful update
        print(json.dumps({
            "level": "INFO",
            "message": "CRI weights updated successfully",
            "username": username,
            "version": new_version,
            "weights": weights,
            "requestId": context.aws_request_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        result = {
            'configId': 'default',
            'version': new_version,
            'weights': weights,
            'updatedAt': datetime.utcnow().isoformat() + 'Z',
            'updatedBy': username,
            'message': 'CRI weights updated successfully'
        }
        
        return success_response(result, context)
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": "Error updating CRI weights",
            "error": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc(),
            "requestId": context.aws_request_id
        }))
        return error_response(500, 'UPDATE_ERROR', 'Unable to update CRI weights', context)


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

