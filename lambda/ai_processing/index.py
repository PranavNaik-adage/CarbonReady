"""
AI Processing Lambda
Performs carbon calculations on a scheduled basis
"""
import json
import os
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

# Import calculation modules
from biomass_calculator import (
    calculate_farm_biomass,
    convert_biomass_to_co2e,
    calculate_annual_sequestration,
    calculate_emissions,
    calculate_net_carbon_position,
    calculate_carbon_readiness_index,
)

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

FARM_METADATA_TABLE = os.environ['FARM_METADATA_TABLE']
CARBON_CALCULATIONS_TABLE = os.environ['CARBON_CALCULATIONS_TABLE']
AI_MODEL_REGISTRY_TABLE = os.environ['AI_MODEL_REGISTRY_TABLE']
CRI_WEIGHTS_TABLE = os.environ['CRI_WEIGHTS_TABLE']
SENSOR_DATA_TABLE = os.environ['SENSOR_DATA_TABLE']
GROWTH_CURVES_TABLE = os.environ.get('GROWTH_CURVES_TABLE', 'CarbonReady-GrowthCurvesTable')
CRITICAL_ALERTS_TOPIC = os.environ.get('CRITICAL_ALERTS_TOPIC', '')
WARNINGS_TOPIC = os.environ.get('WARNINGS_TOPIC', '')

# Model versions for tracking
MODEL_VERSIONS = {
    "biomass": "v1.0.0",
    "sequestration": "v1.0.0",
    "emissions": "v1.0.0",
    "soc": "v1.0.0",
    "cri": "v1.0.0"
}


def lambda_handler(event, context):
    """
    Main handler for AI processing
    Processes carbon calculations for all farms
    """
    try:
        # Log start of processing
        print(json.dumps({
            "level": "INFO",
            "message": "Starting AI processing batch",
            "functionName": context.function_name,
            "requestId": context.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Get list of all farms
        farms = get_all_farms()
        
        print(json.dumps({
            "level": "INFO",
            "message": f"Processing carbon calculations for {len(farms)} farms",
            "farmCount": len(farms),
            "requestId": context.request_id
        }))
        
        results = []
        errors = []
        
        for farm_id in farms:
            try:
                result = process_farm_carbon(farm_id, context)
                results.append(result)
            except Exception as e:
                error_details = {
                    "farmId": farm_id,
                    "status": "error",
                    "error": str(e),
                    "errorType": type(e).__name__,
                    "stackTrace": traceback.format_exc()
                }
                
                # Log error with full context
                print(json.dumps({
                    "level": "ERROR",
                    "message": f"Error processing farm {farm_id}",
                    "error": str(e),
                    "errorType": type(e).__name__,
                    "stackTrace": traceback.format_exc(),
                    "farmId": farm_id,
                    "functionName": context.function_name,
                    "requestId": context.request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
                results.append(error_details)
                errors.append(error_details)
        
        # Log completion summary
        print(json.dumps({
            "level": "INFO",
            "message": "AI processing batch completed",
            "totalFarms": len(farms),
            "successfulFarms": len(results) - len(errors),
            "failedFarms": len(errors),
            "requestId": context.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Send notification if there were errors
        if errors and CRITICAL_ALERTS_TOPIC:
            send_sns_notification(
                CRITICAL_ALERTS_TOPIC,
                "AI Processing Errors",
                f"AI Processing completed with {len(errors)} errors out of {len(farms)} farms.\n\nFailed farms: {', '.join([e['farmId'] for e in errors])}"
            )
        
        return {
            "status": "success",
            "processed": len(results),
            "successful": len(results) - len(errors),
            "failed": len(errors),
            "results": results
        }
        
    except Exception as e:
        # Log critical error with full context
        error_details = {
            "level": "CRITICAL",
            "message": "Critical error in AI processing",
            "error": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc(),
            "functionName": context.function_name,
            "requestId": context.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(json.dumps(error_details))
        
        # Send SNS notification for critical errors
        if CRITICAL_ALERTS_TOPIC:
            send_sns_notification(
                CRITICAL_ALERTS_TOPIC,
                "AI Processing Lambda Critical Error",
                f"Function: {context.function_name}\nError: {str(e)}\nRequestId: {context.request_id}\n\nStack Trace:\n{traceback.format_exc()}"
            )
        
        raise


def get_all_farms():
    """
    Get list of all farm IDs from FarmMetadata table.
    
    Scans the FarmMetadata table and returns unique farm IDs.
    For pilot phase, supports up to 100 farms.
    
    Returns:
        list: List of farm IDs (strings)
    """
    try:
        table = dynamodb.Table(FARM_METADATA_TABLE)
        
        # Scan table to get all farms
        # In production, consider using a GSI for better performance
        response = table.scan(
            ProjectionExpression='farmId',
            Limit=100  # Pilot phase limit
        )
        
        # Extract unique farm IDs
        farm_ids = set()
        for item in response.get('Items', []):
            farm_ids.add(item['farmId'])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response and len(farm_ids) < 100:
            response = table.scan(
                ProjectionExpression='farmId',
                ExclusiveStartKey=response['LastEvaluatedKey'],
                Limit=100 - len(farm_ids)
            )
            for item in response.get('Items', []):
                farm_ids.add(item['farmId'])
        
        return list(farm_ids)
        
    except Exception as e:
        print(f"Error getting farm list: {str(e)}")
        return []


def get_farm_metadata(farm_id):
    """
    Retrieve latest farm metadata from DynamoDB.
    
    Args:
        farm_id (str): Farm identifier
        
    Returns:
        dict: Farm metadata or None if not found
    """
    try:
        table = dynamodb.Table(FARM_METADATA_TABLE)
        
        # Query for latest version of farm metadata
        response = table.query(
            KeyConditionExpression=Key('farmId').eq(farm_id),
            ScanIndexForward=False,  # Sort descending by version
            Limit=1
        )
        
        if response.get('Items'):
            return response['Items'][0]
        else:
            print(f"No metadata found for farm {farm_id}")
            return None
            
    except Exception as e:
        print(f"Error retrieving metadata for farm {farm_id}: {str(e)}")
        return None


def get_historical_biomass(farm_id):
    """
    Retrieve historical biomass data from previous carbon calculation.
    
    Args:
        farm_id (str): Farm identifier
        
    Returns:
        float: Previous biomass in kg, or None if not available
    """
    try:
        table = dynamodb.Table(CARBON_CALCULATIONS_TABLE)
        
        # Query for most recent calculation
        response = table.query(
            KeyConditionExpression=Key('farmId').eq(farm_id),
            ScanIndexForward=False,  # Sort descending by timestamp
            Limit=1
        )
        
        if response.get('Items'):
            item = response['Items'][0]
            # Return biomass if available
            biomass = item.get('biomass')
            if biomass is not None:
                return float(biomass)
        
        return None
        
    except Exception as e:
        print(f"Error retrieving historical biomass for farm {farm_id}: {str(e)}")
        return None


def analyze_soc_trend_stub(farm_id, metadata):
    """
    Stub for SOC trend analysis.
    
    Task 10 (SOC trend analysis module) is marked as optional and not yet implemented.
    This stub returns "Insufficient Data" status to allow the pipeline to continue.
    
    Args:
        farm_id (str): Farm identifier
        metadata (dict): Farm metadata
        
    Returns:
        dict: SOC trend result with status "Insufficient Data"
    """
    # TODO: Implement full SOC trend analysis in Task 10
    # For now, return insufficient data status
    return {
        "status": "Insufficient Data",
        "score": 0.0,
        "dataSpanDays": 0
    }


def process_farm_carbon(farm_id, context):
    """
    Process carbon calculations for a single farm.
    
    This is the main orchestration function that:
    1. Retrieves farm metadata and historical biomass data
    2. Calculates biomass, sequestration, emissions, SOC trend, net position, and CRI
    3. Stores results with model version metadata in DynamoDB
    4. Sets retention timestamp to +10 years
    
    Args:
        farm_id (str): Farm identifier
        context: Lambda context object
        
    Returns:
        dict: Processing result with status and calculated values
        
    Validates: Requirements 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 7.1, 8.1, 8.4, 9.1, 19.3, 19.4, 19.8
    """
    print(json.dumps({
        "level": "INFO",
        "message": f"Processing carbon calculations for farm: {farm_id}",
        "farmId": farm_id,
        "requestId": context.request_id
    }))
    
    try:
        # 1. Retrieve farm metadata
        metadata = get_farm_metadata(farm_id)
        if not metadata:
            return {
                "farmId": farm_id,
                "status": "error",
                "error": "Farm metadata not found"
            }
        
        # 2. Retrieve historical biomass data
        historical_biomass = get_historical_biomass(farm_id)
        
        # 3. Calculate aboveground biomass (in kg)
        biomass = calculate_farm_biomass(metadata)
        
        # 4. Calculate carbon stock and CO₂ equivalent for total biomass
        carbon_stock = biomass * 0.5
        co2_equivalent_stock = convert_biomass_to_co2e(biomass)
        
        # 5. Calculate annual sequestration increment
        sequestration_result = calculate_annual_sequestration(
            farm_id=farm_id,
            metadata=metadata,
            historical_biomass=historical_biomass,
            dynamodb_client=None  # Use default boto3 client
        )
        
        # 6. Analyze SOC trend (stub - Task 10 is optional)
        soc_trend = analyze_soc_trend_stub(farm_id, metadata)
        
        # 7. Calculate emissions (already in CO2e)
        emissions_result = calculate_emissions(metadata)
        
        # 8. Compute net carbon position (both in CO2e kg/year)
        net_position_result = calculate_net_carbon_position(
            annual_sequestration_co2e=sequestration_result['co2eSequestration'],
            annual_emissions_co2e=emissions_result['totalEmissions']
        )
        
        # 9. Generate Carbon Readiness Index
        cri_result = calculate_carbon_readiness_index(
            net_position=net_position_result['netPosition'],
            soc_trend=soc_trend,
            management_practices=metadata,
            weights=None,  # Use default weights from DynamoDB
            dynamodb_client=None
        )
        
        # 10. Prepare calculation result
        calculation_timestamp = datetime.utcnow()
        retention_timestamp = calculation_timestamp + timedelta(days=365 * 10)  # +10 years
        
        calculation_result = {
            "farmId": farm_id,
            "calculatedAt": calculation_timestamp.isoformat(),
            "biomass": round(biomass, 2),
            "carbonStock": round(carbon_stock, 2),
            "co2EquivalentStock": co2_equivalent_stock,
            "annualSequestration": sequestration_result['co2eSequestration'],
            "sequestrationMethod": sequestration_result['method'],
            "emissions": emissions_result['totalEmissions'],
            "emissionsBreakdown": {
                "fertilizer": emissions_result['fertilizerEmissions'],
                "irrigation": emissions_result['irrigationEmissions']
            },
            "netCarbonPosition": net_position_result['netPosition'],
            "netCarbonClassification": net_position_result['classification'],
            "socTrend": soc_trend['status'],
            "carbonReadinessIndex": cri_result['score'],
            "criClassification": cri_result['classification'],
            "criComponents": cri_result['components'],
            "criWeights": cri_result['weights'],
            "modelVersions": MODEL_VERSIONS,
            "retentionUntil": retention_timestamp.isoformat()
        }
        
        # 11. Store results in DynamoDB
        store_carbon_calculation(calculation_result)
        
        print(json.dumps({
            "level": "INFO",
            "message": f"Successfully processed farm {farm_id}",
            "farmId": farm_id,
            "carbonReadinessIndex": cri_result['score'],
            "netCarbonPosition": net_position_result['netPosition'],
            "requestId": context.request_id
        }))
        
        return {
            "farmId": farm_id,
            "status": "success",
            "calculatedAt": calculation_timestamp.isoformat(),
            "carbonReadinessIndex": cri_result['score'],
            "netCarbonPosition": net_position_result['netPosition']
        }
        
    except Exception as e:
        print(json.dumps({
            "level": "ERROR",
            "message": f"Error processing farm {farm_id}",
            "error": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc(),
            "farmId": farm_id,
            "requestId": context.request_id
        }))
        raise


def store_carbon_calculation(calculation_result):
    """
    Store carbon calculation results in DynamoDB.
    
    Args:
        calculation_result (dict): Calculation result to store
    """
    try:
        table = dynamodb.Table(CARBON_CALCULATIONS_TABLE)
        
        # Convert float values to Decimal for DynamoDB
        item = convert_floats_to_decimal(calculation_result)
        
        # Add timestamp as sort key (Unix epoch)
        calculated_at = datetime.fromisoformat(calculation_result['calculatedAt'].replace('Z', '+00:00'))
        item['timestamp'] = int(calculated_at.timestamp())
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        print(f"Stored calculation result for farm {calculation_result['farmId']}")
        
    except Exception as e:
        print(f"Error storing calculation result: {str(e)}")
        raise


def convert_floats_to_decimal(obj):
    """
    Recursively convert float values to Decimal for DynamoDB compatibility.
    
    Args:
        obj: Object to convert (dict, list, or primitive)
        
    Returns:
        Converted object with Decimals instead of floats
    """
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


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
