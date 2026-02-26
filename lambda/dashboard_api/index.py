"""
Dashboard API Lambda
Serves carbon intelligence data to web dashboard
"""
import json
import os
from datetime import datetime, timedelta
import boto3

dynamodb = boto3.resource('dynamodb')

CARBON_CALCULATIONS_TABLE = os.environ['CARBON_CALCULATIONS_TABLE']
SENSOR_DATA_TABLE = os.environ['SENSOR_DATA_TABLE']
CRI_WEIGHTS_TABLE = os.environ['CRI_WEIGHTS_TABLE']


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
        
        if 'carbon-position' in path:
            return get_carbon_position(farm_id)
        elif 'carbon-readiness-index' in path:
            return get_carbon_readiness_index(farm_id)
        elif 'sensor-data/latest' in path:
            return get_latest_sensor_data(farm_id)
        elif 'historical-trends' in path:
            query_params = event.get('queryStringParameters', {})
            days = int(query_params.get('days', 365))
            return get_historical_trends(farm_id, days)
        elif 'admin/cri-weights' in path:
            if http_method == 'GET':
                return get_cri_weights()
            elif http_method == 'PUT':
                body = json.loads(event['body'])
                return update_cri_weights(body, event)
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        print(f"Error in dashboard API: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def get_carbon_position(farm_id):
    """Get latest carbon position for farm"""
    # Placeholder - will query CarbonCalculations table
    return {
        'statusCode': 200,
        'body': json.dumps({
            'farmId': farm_id,
            'message': 'Carbon position endpoint - to be implemented'
        })
    }


def get_carbon_readiness_index(farm_id):
    """Get Carbon Readiness Index with breakdown"""
    # Placeholder - will query CarbonCalculations table
    return {
        'statusCode': 200,
        'body': json.dumps({
            'farmId': farm_id,
            'message': 'CRI endpoint - to be implemented'
        })
    }


def get_latest_sensor_data(farm_id):
    """Get latest sensor readings for farm"""
    # Placeholder - will query SensorData table
    return {
        'statusCode': 200,
        'body': json.dumps({
            'farmId': farm_id,
            'message': 'Latest sensor data endpoint - to be implemented'
        })
    }


def get_historical_trends(farm_id, days):
    """Get historical carbon trends"""
    # Placeholder - will query CarbonCalculations table
    return {
        'statusCode': 200,
        'body': json.dumps({
            'farmId': farm_id,
            'days': days,
            'message': 'Historical trends endpoint - to be implemented'
        })
    }


def get_cri_weights():
    """Get current CRI weights"""
    # Placeholder - will query CRIWeights table
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'CRI weights endpoint - to be implemented'
        })
    }


def update_cri_weights(weights, event):
    """Update CRI weights (admin only)"""
    # Placeholder - will validate admin role and update CRIWeights table
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Update CRI weights endpoint - to be implemented'
        })
    }
