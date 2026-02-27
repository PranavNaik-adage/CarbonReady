#!/usr/bin/env python3
"""
Setup Production CloudWatch Alarms
Creates comprehensive monitoring alarms for CarbonReady production environment
"""
import boto3
import sys
import argparse
from typing import List, Dict

# Initialize AWS clients
cloudwatch = boto3.client('cloudwatch')
lambda_client = boto3.client('lambda')
dynamodb = boto3.client('dynamodb')
apigateway = boto3.client('apigateway')
sns = boto3.client('sns')


def get_sns_topic_arn(topic_name: str) -> str:
    """Get SNS topic ARN by name"""
    try:
        response = sns.list_topics()
        for topic in response['Topics']:
            if topic_name in topic['TopicArn']:
                return topic['TopicArn']
        raise ValueError(f"SNS topic {topic_name} not found")
    except Exception as e:
        print(f"Error finding SNS topic: {e}")
        sys.exit(1)


def create_lambda_error_alarms(critical_topic_arn: str) -> None:
    """Create alarms for Lambda function errors"""
    lambda_functions = [
        'carbonready-data-ingestion',
        'carbonready-ai-processing',
        'carbonready-dashboard-api',
        'carbonready-farm-metadata-api'
    ]
    
    for function_name in lambda_functions:
        # Error rate alarm (> 5%)
        cloudwatch.put_metric_alarm(
            AlarmName=f'{function_name}-error-rate',
            AlarmDescription=f'Error rate > 5% for {function_name}',
            ActionsEnabled=True,
            AlarmActions=[critical_topic_arn],
            MetricName='Errors',
            Namespace='AWS/Lambda',
            Statistic='Sum',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            Period=300,  # 5 minutes
            EvaluationPeriods=2,
            Threshold=5.0,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        print(f"✓ Created error rate alarm for {function_name}")
        
        # Throttle alarm
        cloudwatch.put_metric_alarm(
            AlarmName=f'{function_name}-throttles',
            AlarmDescription=f'Throttling detected for {function_name}',
            ActionsEnabled=True,
            AlarmActions=[critical_topic_arn],
            MetricName='Throttles',
            Namespace='AWS/Lambda',
            Statistic='Sum',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            Period=300,
            EvaluationPeriods=1,
            Threshold=1.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='notBreaching'
        )
        print(f"✓ Created throttle alarm for {function_name}")
        
        # Duration alarm (> 80% of timeout)
        try:
            response = lambda_client.get_function_configuration(
                FunctionName=function_name
            )
            timeout = response['Timeout']
            threshold = timeout * 0.8 * 1000  # Convert to milliseconds
            
            cloudwatch.put_metric_alarm(
                AlarmName=f'{function_name}-high-duration',
                AlarmDescription=f'Duration > 80% of timeout for {function_name}',
                ActionsEnabled=True,
                AlarmActions=[critical_topic_arn],
                MetricName='Duration',
                Namespace='AWS/Lambda',
                Statistic='Average',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': function_name}
                ],
                Period=300,
                EvaluationPeriods=2,
                Threshold=threshold,
                ComparisonOperator='GreaterThanThreshold',
                TreatMissingData='notBreaching'
            )
            print(f"✓ Created duration alarm for {function_name}")
        except Exception as e:
            print(f"⚠ Could not create duration alarm for {function_name}: {e}")


def create_dynamodb_alarms(critical_topic_arn: str, warnings_topic_arn: str) -> None:
    """Create alarms for DynamoDB tables"""
    tables = [
        'SensorDataTable',
        'FarmMetadataTable',
        'CarbonCalculationsTable',
        'AIModelRegistryTable',
        'SensorCalibrationTable',
        'CRIWeightsTable',
        'GrowthCurvesTable'
    ]
    
    for table_name in tables:
        # Find full table name (includes stack prefix)
        try:
            response = dynamodb.list_tables()
            full_table_name = None
            for name in response['TableNames']:
                if table_name in name:
                    full_table_name = name
                    break
            
            if not full_table_name:
                print(f"⚠ Table {table_name} not found, skipping")
                continue
            
            # Read throttle alarm
            cloudwatch.put_metric_alarm(
                AlarmName=f'{table_name}-read-throttles',
                AlarmDescription=f'Read throttling detected for {table_name}',
                ActionsEnabled=True,
                AlarmActions=[warnings_topic_arn],
                MetricName='ReadThrottleEvents',
                Namespace='AWS/DynamoDB',
                Statistic='Sum',
                Dimensions=[
                    {'Name': 'TableName', 'Value': full_table_name}
                ],
                Period=300,
                EvaluationPeriods=1,
                Threshold=5.0,
                ComparisonOperator='GreaterThanThreshold',
                TreatMissingData='notBreaching'
            )
            print(f"✓ Created read throttle alarm for {table_name}")
            
            # Write throttle alarm
            cloudwatch.put_metric_alarm(
                AlarmName=f'{table_name}-write-throttles',
                AlarmDescription=f'Write throttling detected for {table_name}',
                ActionsEnabled=True,
                AlarmActions=[warnings_topic_arn],
                MetricName='WriteThrottleEvents',
                Namespace='AWS/DynamoDB',
                Statistic='Sum',
                Dimensions=[
                    {'Name': 'TableName', 'Value': full_table_name}
                ],
                Period=300,
                EvaluationPeriods=1,
                Threshold=5.0,
                ComparisonOperator='GreaterThanThreshold',
                TreatMissingData='notBreaching'
            )
            print(f"✓ Created write throttle alarm for {table_name}")
            
        except Exception as e:
            print(f"⚠ Error creating alarms for {table_name}: {e}")


def create_api_gateway_alarms(critical_topic_arn: str) -> None:
    """Create alarms for API Gateway"""
    try:
        # Find API Gateway by name
        response = apigateway.get_rest_apis()
        api_id = None
        for api in response['items']:
            if 'CarbonReady' in api['name']:
                api_id = api['id']
                break
        
        if not api_id:
            print("⚠ API Gateway not found, skipping API alarms")
            return
        
        # 5xx error rate alarm
        cloudwatch.put_metric_alarm(
            AlarmName='api-gateway-5xx-errors',
            AlarmDescription='API Gateway 5xx error rate > 1%',
            ActionsEnabled=True,
            AlarmActions=[critical_topic_arn],
            MetricName='5XXError',
            Namespace='AWS/ApiGateway',
            Statistic='Sum',
            Dimensions=[
                {'Name': 'ApiName', 'Value': 'CarbonReady API'}
            ],
            Period=300,
            EvaluationPeriods=2,
            Threshold=10.0,  # 10 errors in 5 minutes
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        print("✓ Created API Gateway 5xx error alarm")
        
        # High latency alarm
        cloudwatch.put_metric_alarm(
            AlarmName='api-gateway-high-latency',
            AlarmDescription='API Gateway latency > 3 seconds',
            ActionsEnabled=True,
            AlarmActions=[critical_topic_arn],
            MetricName='Latency',
            Namespace='AWS/ApiGateway',
            Statistic='Average',
            Dimensions=[
                {'Name': 'ApiName', 'Value': 'CarbonReady API'}
            ],
            Period=300,
            EvaluationPeriods=2,
            Threshold=3000.0,  # 3 seconds in milliseconds
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        print("✓ Created API Gateway latency alarm")
        
    except Exception as e:
        print(f"⚠ Error creating API Gateway alarms: {e}")


def create_iot_alarms(warnings_topic_arn: str) -> None:
    """Create alarms for IoT Core"""
    try:
        # Connection failure alarm
        cloudwatch.put_metric_alarm(
            AlarmName='iot-connection-failures',
            AlarmDescription='IoT Core connection failures detected',
            ActionsEnabled=True,
            AlarmActions=[warnings_topic_arn],
            MetricName='Connect.ClientError',
            Namespace='AWS/IoT',
            Statistic='Sum',
            Period=300,
            EvaluationPeriods=1,
            Threshold=10.0,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        print("✓ Created IoT connection failure alarm")
        
        # Message publish failure alarm
        cloudwatch.put_metric_alarm(
            AlarmName='iot-publish-failures',
            AlarmDescription='IoT Core message publish failures detected',
            ActionsEnabled=True,
            AlarmActions=[warnings_topic_arn],
            MetricName='PublishIn.ClientError',
            Namespace='AWS/IoT',
            Statistic='Sum',
            Period=300,
            EvaluationPeriods=1,
            Threshold=10.0,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching'
        )
        print("✓ Created IoT publish failure alarm")
        
    except Exception as e:
        print(f"⚠ Error creating IoT alarms: {e}")


def create_composite_alarms(critical_topic_arn: str) -> None:
    """Create composite alarms for overall system health"""
    try:
        # System health composite alarm
        cloudwatch.put_composite_alarm(
            AlarmName='carbonready-system-health',
            AlarmDescription='Overall CarbonReady system health',
            ActionsEnabled=True,
            AlarmActions=[critical_topic_arn],
            AlarmRule=(
                "ALARM(carbonready-data-ingestion-error-rate) OR "
                "ALARM(carbonready-ai-processing-error-rate) OR "
                "ALARM(api-gateway-5xx-errors)"
            )
        )
        print("✓ Created system health composite alarm")
        
    except Exception as e:
        print(f"⚠ Error creating composite alarms: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Setup production CloudWatch alarms for CarbonReady'
    )
    parser.add_argument(
        '--region',
        default='ap-south-1',
        help='AWS region (default: ap-south-1)'
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("CarbonReady Production Alarm Setup")
    print("=" * 60)
    print()
    
    # Get SNS topic ARNs
    print("Finding SNS topics...")
    try:
        critical_topic_arn = get_sns_topic_arn('carbonready-critical-alerts')
        warnings_topic_arn = get_sns_topic_arn('carbonready-warnings')
        print(f"✓ Critical alerts topic: {critical_topic_arn}")
        print(f"✓ Warnings topic: {warnings_topic_arn}")
        print()
    except Exception as e:
        print(f"✗ Error finding SNS topics: {e}")
        print("Please ensure the monitoring stack is deployed.")
        sys.exit(1)
    
    # Create alarms
    print("Creating Lambda function alarms...")
    create_lambda_error_alarms(critical_topic_arn)
    print()
    
    print("Creating DynamoDB alarms...")
    create_dynamodb_alarms(critical_topic_arn, warnings_topic_arn)
    print()
    
    print("Creating API Gateway alarms...")
    create_api_gateway_alarms(critical_topic_arn)
    print()
    
    print("Creating IoT Core alarms...")
    create_iot_alarms(warnings_topic_arn)
    print()
    
    print("Creating composite alarms...")
    create_composite_alarms(critical_topic_arn)
    print()
    
    print("=" * 60)
    print("✓ Production alarm setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Verify alarms in CloudWatch console")
    print("2. Test alarm notifications")
    print("3. Subscribe email addresses to SNS topics")
    print()


if __name__ == '__main__':
    main()
