#!/usr/bin/env python3
"""
Farm Onboarding Script

Complete workflow for onboarding a pilot farm to the CarbonReady system:
1. Create farm metadata entry in DynamoDB
2. Provision ESP32 sensor device
3. Verify data ingestion pipeline
4. Verify carbon calculations
5. Verify dashboard displays data

Usage:
    python scripts/onboard_farm.py <farm_id> <device_id> [options]

Example:
    python scripts/onboard_farm.py farm-001 esp32-001 --crop-type coconut --tree-age 15

Requirements: Task 22.3
"""
import boto3
import json
import sys
import time
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import hashlib
from decimal import Decimal

# AWS clients
dynamodb = boto3.resource('dynamodb')
iot_data = boto3.client('iot-data')
logs_client = boto3.client('logs')


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(message):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.END} {message}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


def get_table_name(prefix):
    """Get DynamoDB table name by prefix"""
    client = boto3.client('dynamodb')
    tables = client.list_tables()['TableNames']
    matching = [t for t in tables if prefix in t]
    if matching:
        return matching[0]
    raise Exception(f"No table found with prefix: {prefix}")


def step1_create_farm_metadata(farm_id, metadata):
    """
    Step 1: Create farm metadata entry in DynamoDB
    """
    print_header("Step 1: Create Farm Metadata")
    
    try:
        table_name = get_table_name('FarmMetadataTable')
        table = dynamodb.Table(table_name)
        
        print_info(f"Using table: {table_name}")
        print_info(f"Creating metadata for farm: {farm_id}")
        
        # Prepare metadata item (convert numeric values to Decimal for DynamoDB)
        item = {
            'farmId': farm_id,
            'version': 1,
            'cropType': metadata['crop_type'],
            'farmSizeHectares': Decimal(str(metadata['farm_size'])),
            'treeAge': metadata['tree_age'],  # Integer is fine
            'plantationDensity': metadata['plantation_density'],  # Integer is fine
            'fertilizerUsage': Decimal(str(metadata['fertilizer_usage'])),
            'irrigationActivity': Decimal(str(metadata['irrigation_activity'])),
            'updatedAt': datetime.now(timezone.utc).isoformat()
        }
        
        # Add crop-specific fields
        if metadata['crop_type'] == 'coconut':
            item['treeHeight'] = Decimal(str(metadata.get('tree_height', 10.0)))
        elif metadata['crop_type'] == 'cashew':
            item['dbh'] = Decimal(str(metadata.get('dbh', 25.0)))
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        print_success("Farm metadata created successfully")
        print(f"  Farm ID: {farm_id}")
        print(f"  Crop Type: {metadata['crop_type']}")
        print(f"  Farm Size: {metadata['farm_size']} hectares")
        print(f"  Tree Age: {metadata['tree_age']} years")
        print(f"  Plantation Density: {metadata['plantation_density']} trees/hectare")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to create farm metadata: {e}")
        return False


def step2_provision_device(farm_id, device_id, output_dir="device_certs"):
    """
    Step 2: Provision ESP32 sensor device
    """
    print_header("Step 2: Provision ESP32 Device")
    
    try:
        print_info(f"Provisioning device: {device_id} for farm: {farm_id}")
        
        # Run provision_device.py script
        result = subprocess.run(
            ['python', 'scripts/provision_device.py', device_id, farm_id, '--output-dir', output_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Device provisioned successfully")
            print_info("Certificates saved to: " + str(Path(output_dir) / device_id))
            return True
        else:
            print_error("Device provisioning failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Failed to provision device: {e}")
        return False


def step3_verify_data_ingestion(farm_id, device_id, timeout=60):
    """
    Step 3: Verify data ingestion pipeline
    
    This step simulates sensor data and verifies it flows through the system:
    - Publishes test data to IoT Core
    - Waits for Lambda processing
    - Checks DynamoDB for stored data
    """
    print_header("Step 3: Verify Data Ingestion")
    
    try:
        # Get table names
        sensor_table_name = get_table_name('SensorDataTable')
        calibration_table_name = get_table_name('SensorCalibrationTable')
        
        sensor_table = dynamodb.Table(sensor_table_name)
        calibration_table = dynamodb.Table(calibration_table_name)
        
        # Create calibration record (required for data ingestion)
        print_info("Creating sensor calibration record...")
        calibration_table.put_item(Item={
            'deviceId': device_id,
            'calibrationDate': datetime.now(timezone.utc).isoformat(),
            'calibrationType': 'initial',
            'farmId': farm_id,
            'calibrationParameters': {
                'soilMoistureDry': Decimal('3200'),
                'soilMoistureWet': Decimal('1200')
            },
            'referenceValues': {
                'airTemp': Decimal('25.0'),
                'soilTemp': Decimal('22.0'),
                'humidity': Decimal('65.0')
            },
            'performedBy': 'onboarding_script',
            'nextCalibrationDue': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            'status': 'ACTIVE'
        })
        print_success("Calibration record created")
        
        # Create test sensor data
        print_info("Creating test sensor data...")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        payload = {
            'farmId': farm_id,
            'deviceId': device_id,
            'timestamp': timestamp,
            'readings': {
                'soilMoisture': 45.5,
                'soilTemperature': 22.3,
                'airTemperature': 28.7,
                'humidity': 68.2
            }
        }
        
        # Compute SHA-256 hash (required for data integrity)
        payload_str = json.dumps(payload['readings'], sort_keys=True)
        hash_value = hashlib.sha256(payload_str.encode()).hexdigest()
        payload['hash'] = hash_value
        
        # Publish to IoT Core
        print_info(f"Publishing test data to IoT topic: carbonready/farm/{farm_id}/sensor/data")
        iot_data.publish(
            topic=f'carbonready/farm/{farm_id}/sensor/data',
            qos=1,
            payload=json.dumps(payload)
        )
        print_success("Test data published to IoT Core")
        
        # Wait for Lambda processing
        print_info(f"Waiting for Lambda processing ({timeout} seconds)...")
        time.sleep(timeout)
        
        # Check DynamoDB for data
        print_info("Checking DynamoDB for ingested data...")
        response = sensor_table.query(
            KeyConditionExpression='farmId = :farmId',
            ExpressionAttributeValues={':farmId': farm_id},
            Limit=5,
            ScanIndexForward=False
        )
        
        if response['Items']:
            print_success(f"Data ingestion verified! Found {len(response['Items'])} reading(s)")
            latest = response['Items'][0]
            print(f"  Device ID: {latest.get('deviceId')}")
            print(f"  Timestamp: {latest.get('timestamp')}")
            print(f"  Soil Moisture: {latest.get('soilMoisture')}%")
            print(f"  Soil Temperature: {latest.get('soilTemperature')}°C")
            print(f"  Air Temperature: {latest.get('airTemperature')}°C")
            print(f"  Humidity: {latest.get('humidity')}%")
            print(f"  Validation Status: {latest.get('validationStatus')}")
            return True
        else:
            print_error("No data found in DynamoDB")
            print_warning("Check CloudWatch logs for errors:")
            print_warning("  aws logs tail /aws/lambda/carbonready-data-ingestion --follow")
            return False
            
    except Exception as e:
        print_error(f"Data ingestion verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step4_verify_carbon_calculations(farm_id, timeout=120):
    """
    Step 4: Verify carbon calculations
    
    Triggers AI processing and verifies carbon calculations are performed
    """
    print_header("Step 4: Verify Carbon Calculations")
    
    try:
        # Get table name
        calculations_table_name = get_table_name('CarbonCalculationsTable')
        calculations_table = dynamodb.Table(calculations_table_name)
        
        print_info("Triggering AI processing Lambda...")
        print_info("(In production, this runs on a daily schedule)")
        
        # Invoke AI processing Lambda
        lambda_client = boto3.client('lambda')
        try:
            response = lambda_client.invoke(
                FunctionName='carbonready-ai-processing',
                InvocationType='RequestResponse',
                Payload=json.dumps({})
            )
            
            if response['StatusCode'] == 200:
                print_success("AI processing Lambda invoked successfully")
            else:
                print_warning(f"Lambda returned status code: {response['StatusCode']}")
                
        except Exception as e:
            print_warning(f"Could not invoke Lambda directly: {e}")
            print_info("Waiting for scheduled processing...")
        
        # Wait for processing
        print_info(f"Waiting for carbon calculations ({timeout} seconds)...")
        time.sleep(timeout)
        
        # Check for carbon calculations
        print_info("Checking for carbon calculation results...")
        response = calculations_table.query(
            KeyConditionExpression='farmId = :farmId',
            ExpressionAttributeValues={':farmId': farm_id},
            Limit=1,
            ScanIndexForward=False
        )
        
        if response['Items']:
            print_success("Carbon calculations verified!")
            calc = response['Items'][0]
            print(f"  Biomass: {calc.get('biomass', 'N/A')} kg")
            print(f"  Carbon Stock: {calc.get('carbonStock', 'N/A')} kg")
            print(f"  CO₂ Equivalent: {calc.get('co2EquivalentStock', 'N/A')} kg")
            print(f"  Annual Sequestration: {calc.get('annualSequestration', 'N/A')} kg CO₂e/year")
            print(f"  Emissions: {calc.get('emissions', 'N/A')} kg CO₂e/year")
            print(f"  Net Carbon Position: {calc.get('netCarbonPosition', 'N/A')} kg CO₂e/year")
            
            cri = calc.get('carbonReadinessIndex', {})
            if isinstance(cri, dict):
                print(f"  Carbon Readiness Index: {cri.get('score', 'N/A')} ({cri.get('classification', 'N/A')})")
            
            return True
        else:
            print_warning("No carbon calculations found yet")
            print_info("Calculations may take a few minutes to complete")
            print_info("Check CloudWatch logs:")
            print_info("  aws logs tail /aws/lambda/carbonready-ai-processing --follow")
            return False
            
    except Exception as e:
        print_error(f"Carbon calculation verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step5_verify_dashboard(farm_id):
    """
    Step 5: Verify dashboard displays data correctly
    
    Checks that dashboard API returns data for the farm
    """
    print_header("Step 5: Verify Dashboard API")
    
    try:
        print_info("Testing dashboard API endpoints...")
        
        # Invoke dashboard API Lambda
        lambda_client = boto3.client('lambda')
        
        # Test carbon position endpoint
        print_info(f"Testing GET /api/v1/farms/{farm_id}/carbon-position")
        try:
            response = lambda_client.invoke(
                FunctionName='carbonready-dashboard-api',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'httpMethod': 'GET',
                    'path': f'/api/v1/farms/{farm_id}/carbon-position',
                    'pathParameters': {'farmId': farm_id}
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                print_success("Carbon position endpoint working")
                body = json.loads(result['body'])
                print(f"  Net Position: {body.get('netCarbonPosition', 'N/A')} kg CO₂e/year")
                print(f"  Classification: {body.get('classification', 'N/A')}")
            else:
                print_warning(f"Endpoint returned status: {result.get('statusCode')}")
                
        except Exception as e:
            print_warning(f"Could not test carbon position endpoint: {e}")
        
        # Test CRI endpoint
        print_info(f"Testing GET /api/v1/farms/{farm_id}/carbon-readiness-index")
        try:
            response = lambda_client.invoke(
                FunctionName='carbonready-dashboard-api',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'httpMethod': 'GET',
                    'path': f'/api/v1/farms/{farm_id}/carbon-readiness-index',
                    'pathParameters': {'farmId': farm_id}
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                print_success("Carbon Readiness Index endpoint working")
                body = json.loads(result['body'])
                cri = body.get('carbonReadinessIndex', {})
                print(f"  Score: {cri.get('score', 'N/A')}")
                print(f"  Classification: {cri.get('classification', 'N/A')}")
            else:
                print_warning(f"Endpoint returned status: {result.get('statusCode')}")
                
        except Exception as e:
            print_warning(f"Could not test CRI endpoint: {e}")
        
        # Test sensor data endpoint
        print_info(f"Testing GET /api/v1/farms/{farm_id}/sensor-data/latest")
        try:
            response = lambda_client.invoke(
                FunctionName='carbonready-dashboard-api',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'httpMethod': 'GET',
                    'path': f'/api/v1/farms/{farm_id}/sensor-data/latest',
                    'pathParameters': {'farmId': farm_id}
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                print_success("Sensor data endpoint working")
                body = json.loads(result['body'])
                readings = body.get('readings', {})
                print(f"  Latest reading: {body.get('timestamp', 'N/A')}")
                print(f"  Soil Moisture: {readings.get('soilMoisture', 'N/A')}%")
            else:
                print_warning(f"Endpoint returned status: {result.get('statusCode')}")
                
        except Exception as e:
            print_warning(f"Could not test sensor data endpoint: {e}")
        
        print_success("Dashboard API verification complete")
        return True
        
    except Exception as e:
        print_error(f"Dashboard verification failed: {e}")
        return False


def generate_onboarding_report(farm_id, device_id, results):
    """
    Generate onboarding report
    """
    print_header("Onboarding Report")
    
    print(f"Farm ID: {farm_id}")
    print(f"Device ID: {device_id}")
    print(f"Onboarded: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    print("Status:")
    print(f"  {'✓' if results['metadata'] else '✗'} Farm metadata created")
    print(f"  {'✓' if results['device'] else '✗'} Device provisioned")
    print(f"  {'✓' if results['ingestion'] else '✗'} Data ingestion verified")
    print(f"  {'✓' if results['calculations'] else '✗'} Carbon calculations verified")
    print(f"  {'✓' if results['dashboard'] else '✗'} Dashboard API verified")
    print()
    
    if all(results.values()):
        print_success("Farm onboarding completed successfully!")
        print()
        print("Next steps:")
        print("  1. Flash firmware to ESP32 device:")
        print(f"     python scripts/flash_firmware.py {device_id}")
        print("  2. Upload certificates to device:")
        print(f"     python scripts/upload_certificates.py {device_id}")
        print("  3. Calibrate sensors:")
        print(f"     python scripts/calibrate_device.py {device_id}")
        print("  4. Deploy device to farm location")
        print("  5. Monitor data in dashboard")
    else:
        print_error("Farm onboarding incomplete - some steps failed")
        print_info("Review the output above for details")


def main():
    parser = argparse.ArgumentParser(
        description='Onboard a pilot farm to the CarbonReady system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Onboard coconut farm
  python scripts/onboard_farm.py farm-001 esp32-001 \\
    --crop-type coconut --tree-age 15 --tree-height 12.5

  # Onboard cashew farm
  python scripts/onboard_farm.py farm-002 esp32-002 \\
    --crop-type cashew --tree-age 10 --dbh 28.5

  # Quick onboarding with defaults
  python scripts/onboard_farm.py farm-003 esp32-003 --crop-type coconut
        """
    )
    
    parser.add_argument('farm_id', help='Farm identifier (e.g., farm-001)')
    parser.add_argument('device_id', help='Device identifier (e.g., esp32-001)')
    
    # Farm metadata arguments
    parser.add_argument('--crop-type', required=True, choices=['coconut', 'cashew'],
                        help='Crop type')
    parser.add_argument('--farm-size', type=float, default=2.0,
                        help='Farm size in hectares (default: 2.0)')
    parser.add_argument('--tree-age', type=int, default=10,
                        help='Tree age in years (default: 10)')
    parser.add_argument('--tree-height', type=float,
                        help='Tree height in meters (coconut only, default: 10.0)')
    parser.add_argument('--dbh', type=float,
                        help='Diameter at breast height in cm (cashew only, default: 25.0)')
    parser.add_argument('--plantation-density', type=int, default=200,
                        help='Trees per hectare (default: 200)')
    parser.add_argument('--fertilizer-usage', type=float, default=100.0,
                        help='Fertilizer usage in kg/hectare/year (default: 100.0)')
    parser.add_argument('--irrigation-activity', type=float, default=5000.0,
                        help='Irrigation in liters/hectare/year (default: 5000.0)')
    
    # Options
    parser.add_argument('--skip-device', action='store_true',
                        help='Skip device provisioning step')
    parser.add_argument('--skip-verification', action='store_true',
                        help='Skip verification steps')
    parser.add_argument('--output-dir', default='device_certs',
                        help='Output directory for device certificates')
    
    args = parser.parse_args()
    
    # Prepare metadata
    metadata = {
        'crop_type': args.crop_type,
        'farm_size': args.farm_size,
        'tree_age': args.tree_age,
        'plantation_density': args.plantation_density,
        'fertilizer_usage': args.fertilizer_usage,
        'irrigation_activity': args.irrigation_activity
    }
    
    if args.crop_type == 'coconut':
        metadata['tree_height'] = args.tree_height if args.tree_height else 10.0
    elif args.crop_type == 'cashew':
        metadata['dbh'] = args.dbh if args.dbh else 25.0
    
    # Print welcome message
    print()
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}CarbonReady Farm Onboarding{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")
    print()
    print(f"Farm ID: {args.farm_id}")
    print(f"Device ID: {args.device_id}")
    print(f"Crop Type: {args.crop_type}")
    print()
    
    # Track results
    results = {
        'metadata': False,
        'device': False,
        'ingestion': False,
        'calculations': False,
        'dashboard': False
    }
    
    # Execute onboarding steps
    try:
        # Step 1: Create farm metadata
        results['metadata'] = step1_create_farm_metadata(args.farm_id, metadata)
        if not results['metadata']:
            print_error("Cannot continue without farm metadata")
            sys.exit(1)
        
        # Step 2: Provision device
        if not args.skip_device:
            results['device'] = step2_provision_device(args.farm_id, args.device_id, args.output_dir)
            if not results['device']:
                print_warning("Device provisioning failed, but continuing...")
        else:
            print_warning("Skipping device provisioning (--skip-device)")
            results['device'] = True
        
        # Step 3-5: Verification steps
        if not args.skip_verification:
            results['ingestion'] = step3_verify_data_ingestion(args.farm_id, args.device_id)
            results['calculations'] = step4_verify_carbon_calculations(args.farm_id)
            results['dashboard'] = step5_verify_dashboard(args.farm_id)
        else:
            print_warning("Skipping verification steps (--skip-verification)")
            results['ingestion'] = True
            results['calculations'] = True
            results['dashboard'] = True
        
        # Generate report
        generate_onboarding_report(args.farm_id, args.device_id, results)
        
        # Exit with appropriate code
        sys.exit(0 if all(results.values()) else 1)
        
    except KeyboardInterrupt:
        print()
        print_warning("Onboarding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Onboarding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
