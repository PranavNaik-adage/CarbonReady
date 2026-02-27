#!/usr/bin/env python3
"""
Verify Production Deployment
Checks that all CarbonReady infrastructure components are deployed correctly
"""
import boto3
import sys
import argparse
from typing import Dict, List, Tuple
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
apigateway = boto3.client('apigateway')
iot = boto3.client('iot')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')
cognito = boto3.client('cognito-idp')


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_status(message: str, status: str):
    """Print colored status message"""
    if status == 'OK':
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == 'FAIL':
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == 'WARN':
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
    else:
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


def check_dynamodb_tables() -> Tuple[int, int]:
    """Check DynamoDB tables exist and are active"""
    print("\n" + "=" * 60)
    print("Checking DynamoDB Tables")
    print("=" * 60)
    
    expected_tables = [
        'SensorDataTable',
        'FarmMetadataTable',
        'CarbonCalculationsTable',
        'AIModelRegistryTable',
        'SensorCalibrationTable',
        'CRIWeightsTable',
        'GrowthCurvesTable'
    ]
    
    success = 0
    failed = 0
    
    try:
        response = dynamodb.list_tables()
        all_tables = response['TableNames']
        
        for expected in expected_tables:
            found = False
            for table in all_tables:
                if expected in table:
                    # Check table status
                    try:
                        table_info = dynamodb.describe_table(TableName=table)
                        status = table_info['Table']['TableStatus']
                        
                        if status == 'ACTIVE':
                            print_status(f"{expected}: {table} ({status})", 'OK')
                            success += 1
                        else:
                            print_status(f"{expected}: {table} ({status})", 'WARN')
                            failed += 1
                        
                        found = True
                        break
                    except ClientError as e:
                        print_status(f"{expected}: Error checking table - {e}", 'FAIL')
                        failed += 1
                        found = True
                        break
            
            if not found:
                print_status(f"{expected}: Not found", 'FAIL')
                failed += 1
    
    except ClientError as e:
        print_status(f"Error listing tables: {e}", 'FAIL')
        return 0, len(expected_tables)
    
    return success, failed


def check_s3_buckets() -> Tuple[int, int]:
    """Check S3 buckets exist and are configured"""
    print("\n" + "=" * 60)
    print("Checking S3 Buckets")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    try:
        response = s3.list_buckets()
        buckets = [b['Name'] for b in response['Buckets']]
        
        # Find sensor data bucket
        sensor_bucket = None
        for bucket in buckets:
            if 'sensordatabucket' in bucket.lower():
                sensor_bucket = bucket
                break
        
        if sensor_bucket:
            print_status(f"Sensor data bucket: {sensor_bucket}", 'OK')
            
            # Check lifecycle policies
            try:
                lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=sensor_bucket)
                rules = lifecycle.get('Rules', [])
                
                if len(rules) >= 2:
                    print_status(f"  Lifecycle policies: {len(rules)} rules configured", 'OK')
                    success += 1
                else:
                    print_status(f"  Lifecycle policies: Only {len(rules)} rules found", 'WARN')
                    failed += 1
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                    print_status("  Lifecycle policies: Not configured", 'FAIL')
                    failed += 1
                else:
                    print_status(f"  Lifecycle policies: Error - {e}", 'FAIL')
                    failed += 1
            
            # Check encryption
            try:
                encryption = s3.get_bucket_encryption(Bucket=sensor_bucket)
                print_status("  Encryption: Enabled", 'OK')
                success += 1
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    print_status("  Encryption: Not enabled", 'FAIL')
                    failed += 1
                else:
                    print_status(f"  Encryption: Error - {e}", 'FAIL')
                    failed += 1
        else:
            print_status("Sensor data bucket: Not found", 'FAIL')
            failed += 2
    
    except ClientError as e:
        print_status(f"Error listing buckets: {e}", 'FAIL')
        return 0, 2
    
    return success, failed


def check_lambda_functions() -> Tuple[int, int]:
    """Check Lambda functions are deployed"""
    print("\n" + "=" * 60)
    print("Checking Lambda Functions")
    print("=" * 60)
    
    expected_functions = [
        'carbonready-data-ingestion',
        'carbonready-ai-processing',
        'carbonready-dashboard-api',
        'carbonready-farm-metadata-api'
    ]
    
    success = 0
    failed = 0
    
    for function_name in expected_functions:
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            state = response['Configuration']['State']
            
            if state == 'Active':
                runtime = response['Configuration']['Runtime']
                memory = response['Configuration']['MemorySize']
                timeout = response['Configuration']['Timeout']
                print_status(
                    f"{function_name}: {state} ({runtime}, {memory}MB, {timeout}s timeout)",
                    'OK'
                )
                success += 1
            else:
                print_status(f"{function_name}: {state}", 'WARN')
                failed += 1
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print_status(f"{function_name}: Not found", 'FAIL')
            else:
                print_status(f"{function_name}: Error - {e}", 'FAIL')
            failed += 1
    
    return success, failed


def check_api_gateway() -> Tuple[int, int]:
    """Check API Gateway is deployed"""
    print("\n" + "=" * 60)
    print("Checking API Gateway")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    try:
        response = apigateway.get_rest_apis()
        
        api = None
        for item in response['items']:
            if 'CarbonReady' in item['name']:
                api = item
                break
        
        if api:
            api_id = api['id']
            api_name = api['name']
            print_status(f"API: {api_name} ({api_id})", 'OK')
            success += 1
            
            # Check stages
            try:
                stages = apigateway.get_stages(restApiId=api_id)
                if stages['item']:
                    stage_names = [s['stageName'] for s in stages['item']]
                    print_status(f"  Stages: {', '.join(stage_names)}", 'OK')
                    success += 1
                else:
                    print_status("  Stages: No stages deployed", 'FAIL')
                    failed += 1
            except ClientError as e:
                print_status(f"  Stages: Error - {e}", 'FAIL')
                failed += 1
            
            # Check authorizers
            try:
                authorizers = apigateway.get_authorizers(restApiId=api_id)
                if authorizers['items']:
                    print_status(f"  Authorizers: {len(authorizers['items'])} configured", 'OK')
                    success += 1
                else:
                    print_status("  Authorizers: None configured", 'FAIL')
                    failed += 1
            except ClientError as e:
                print_status(f"  Authorizers: Error - {e}", 'FAIL')
                failed += 1
        else:
            print_status("API: Not found", 'FAIL')
            failed += 3
    
    except ClientError as e:
        print_status(f"Error checking API Gateway: {e}", 'FAIL')
        return 0, 3
    
    return success, failed


def check_iot_core() -> Tuple[int, int]:
    """Check IoT Core configuration"""
    print("\n" + "=" * 60)
    print("Checking AWS IoT Core")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    # Check IoT endpoint
    try:
        endpoint = iot.describe_endpoint(endpointType='iot:Data-ATS')
        print_status(f"IoT Endpoint: {endpoint['endpointAddress']}", 'OK')
        success += 1
    except ClientError as e:
        print_status(f"IoT Endpoint: Error - {e}", 'FAIL')
        failed += 1
    
    # Check IoT policy
    try:
        policies = iot.list_policies()
        policy_found = False
        for policy in policies['policies']:
            if 'CarbonReadyESP32SensorPolicy' in policy['policyName']:
                print_status(f"IoT Policy: {policy['policyName']}", 'OK')
                policy_found = True
                success += 1
                break
        
        if not policy_found:
            print_status("IoT Policy: CarbonReadyESP32SensorPolicy not found", 'FAIL')
            failed += 1
    except ClientError as e:
        print_status(f"IoT Policy: Error - {e}", 'FAIL')
        failed += 1
    
    # Check IoT rules
    try:
        rules = iot.list_topic_rules()
        rule_found = False
        for rule in rules['rules']:
            if 'CarbonReadySensorDataRule' in rule['ruleName']:
                print_status(f"IoT Rule: {rule['ruleName']}", 'OK')
                rule_found = True
                success += 1
                break
        
        if not rule_found:
            print_status("IoT Rule: CarbonReadySensorDataRule not found", 'FAIL')
            failed += 1
    except ClientError as e:
        print_status(f"IoT Rule: Error - {e}", 'FAIL')
        failed += 1
    
    return success, failed


def check_sns_topics() -> Tuple[int, int]:
    """Check SNS topics are configured"""
    print("\n" + "=" * 60)
    print("Checking SNS Topics")
    print("=" * 60)
    
    expected_topics = [
        'carbonready-critical-alerts',
        'carbonready-warnings'
    ]
    
    success = 0
    failed = 0
    
    try:
        response = sns.list_topics()
        all_topics = [t['TopicArn'] for t in response['Topics']]
        
        for expected in expected_topics:
            found = False
            for topic_arn in all_topics:
                if expected in topic_arn:
                    print_status(f"{expected}: {topic_arn}", 'OK')
                    
                    # Check subscriptions
                    try:
                        subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
                        sub_count = len(subs['Subscriptions'])
                        if sub_count > 0:
                            print_status(f"  Subscriptions: {sub_count} configured", 'OK')
                        else:
                            print_status("  Subscriptions: None configured", 'WARN')
                    except ClientError as e:
                        print_status(f"  Subscriptions: Error - {e}", 'WARN')
                    
                    success += 1
                    found = True
                    break
            
            if not found:
                print_status(f"{expected}: Not found", 'FAIL')
                failed += 1
    
    except ClientError as e:
        print_status(f"Error listing SNS topics: {e}", 'FAIL')
        return 0, len(expected_topics)
    
    return success, failed


def check_cognito() -> Tuple[int, int]:
    """Check Cognito user pool"""
    print("\n" + "=" * 60)
    print("Checking Cognito User Pool")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    try:
        response = cognito.list_user_pools(MaxResults=50)
        
        user_pool = None
        for pool in response['UserPools']:
            if 'carbonready' in pool['Name'].lower():
                user_pool = pool
                break
        
        if user_pool:
            pool_id = user_pool['Id']
            pool_name = user_pool['Name']
            print_status(f"User Pool: {pool_name} ({pool_id})", 'OK')
            success += 1
            
            # Check user pool clients
            try:
                clients = cognito.list_user_pool_clients(
                    UserPoolId=pool_id,
                    MaxResults=50
                )
                if clients['UserPoolClients']:
                    print_status(f"  Clients: {len(clients['UserPoolClients'])} configured", 'OK')
                    success += 1
                else:
                    print_status("  Clients: None configured", 'FAIL')
                    failed += 1
            except ClientError as e:
                print_status(f"  Clients: Error - {e}", 'FAIL')
                failed += 1
            
            # Check groups
            try:
                groups = cognito.list_groups(UserPoolId=pool_id)
                if groups['Groups']:
                    group_names = [g['GroupName'] for g in groups['Groups']]
                    print_status(f"  Groups: {', '.join(group_names)}", 'OK')
                    success += 1
                else:
                    print_status("  Groups: None configured", 'WARN')
            except ClientError as e:
                print_status(f"  Groups: Error - {e}", 'WARN')
        else:
            print_status("User Pool: Not found", 'FAIL')
            failed += 3
    
    except ClientError as e:
        print_status(f"Error checking Cognito: {e}", 'FAIL')
        return 0, 3
    
    return success, failed


def check_cloudwatch_logs() -> Tuple[int, int]:
    """Check CloudWatch log groups"""
    print("\n" + "=" * 60)
    print("Checking CloudWatch Log Groups")
    print("=" * 60)
    
    expected_log_groups = [
        '/aws/lambda/carbonready-data-ingestion',
        '/aws/lambda/carbonready-ai-processing',
        '/aws/lambda/carbonready-dashboard-api',
        '/aws/lambda/carbonready-farm-metadata-api'
    ]
    
    success = 0
    failed = 0
    
    logs_client = boto3.client('logs')
    
    for log_group in expected_log_groups:
        try:
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=log_group
            )
            
            if response['logGroups']:
                retention = response['logGroups'][0].get('retentionInDays', 'Never expire')
                print_status(f"{log_group}: Exists (retention: {retention} days)", 'OK')
                success += 1
            else:
                print_status(f"{log_group}: Not found", 'FAIL')
                failed += 1
        
        except ClientError as e:
            print_status(f"{log_group}: Error - {e}", 'FAIL')
            failed += 1
    
    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description='Verify CarbonReady production deployment'
    )
    parser.add_argument(
        '--env',
        default='production',
        help='Environment to verify (default: production)'
    )
    parser.add_argument(
        '--region',
        default='ap-south-1',
        help='AWS region (default: ap-south-1)'
    )
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print(f"CarbonReady Deployment Verification - {args.env.upper()}")
    print("=" * 60)
    
    total_success = 0
    total_failed = 0
    
    # Run all checks
    checks = [
        check_dynamodb_tables,
        check_s3_buckets,
        check_lambda_functions,
        check_api_gateway,
        check_iot_core,
        check_sns_topics,
        check_cognito,
        check_cloudwatch_logs
    ]
    
    for check in checks:
        success, failed = check()
        total_success += success
        total_failed += failed
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    print(f"{Colors.GREEN}✓ Passed:{Colors.END} {total_success}")
    print(f"{Colors.RED}✗ Failed:{Colors.END} {total_failed}")
    
    total_checks = total_success + total_failed
    if total_checks > 0:
        success_rate = (total_success / total_checks) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    print()
    
    if total_failed == 0:
        print(f"{Colors.GREEN}✓ All checks passed! Deployment is healthy.{Colors.END}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}✗ Some checks failed. Please review the output above.{Colors.END}")
        sys.exit(1)


if __name__ == '__main__':
    main()
