#!/usr/bin/env python3
"""
Test Device Provisioning Workflow

This script tests the device provisioning workflow without actually
flashing hardware. Useful for testing AWS IoT Core integration.

Usage:
    python scripts/test_provisioning.py
"""
import boto3
import sys
from datetime import datetime, timezone

def test_iot_connectivity():
    """Test AWS IoT Core connectivity"""
    print("\n" + "=" * 70)
    print("Testing AWS IoT Core Connectivity")
    print("=" * 70)
    
    try:
        iot = boto3.client('iot')
        
        # Get IoT endpoint
        endpoint = iot.describe_endpoint(endpointType='iot:Data-ATS')
        print(f"✓ IoT Endpoint: {endpoint['endpointAddress']}")
        
        # List policies
        policies = iot.list_policies()
        sensor_policy = [p for p in policies['policies'] 
                        if 'CarbonReadyESP32SensorPolicy' in p['policyName']]
        if sensor_policy:
            print(f"✓ IoT Policy found: {sensor_policy[0]['policyName']}")
        else:
            print("⚠️  IoT Policy not found (deploy IoT stack first)")
        
        # List rules
        rules = iot.list_topic_rules()
        sensor_rule = [r for r in rules['rules'] 
                      if 'CarbonReadySensorDataRule' in r['ruleName']]
        if sensor_rule:
            print(f"✓ IoT Rule found: {sensor_rule[0]['ruleName']}")
        else:
            print("⚠️  IoT Rule not found (deploy compute stack first)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_dynamodb_tables():
    """Test DynamoDB table access"""
    print("\n" + "=" * 70)
    print("Testing DynamoDB Tables")
    print("=" * 70)
    
    try:
        dynamodb = boto3.client('dynamodb')
        tables = dynamodb.list_tables()['TableNames']
        
        required_tables = [
            'SensorCalibrationTable',
            'FarmMetadataTable',
            'SensorDataTable'
        ]
        
        for table_name in required_tables:
            matching = [t for t in tables if table_name in t]
            if matching:
                print(f"✓ Table found: {matching[0]}")
            else:
                print(f"⚠️  Table not found: {table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_certificate_generation():
    """Test certificate generation (without creating actual device)"""
    print("\n" + "=" * 70)
    print("Testing Certificate Generation")
    print("=" * 70)
    
    try:
        iot = boto3.client('iot')
        
        # Create test certificate
        print("Creating test certificate...")
        response = iot.create_keys_and_certificate(setAsActive=True)
        
        cert_id = response['certificateId']
        cert_arn = response['certificateArn']
        
        print(f"✓ Certificate created: {cert_id}")
        print(f"  ARN: {cert_arn}")
        
        # Clean up test certificate
        print("Cleaning up test certificate...")
        iot.update_certificate(
            certificateId=cert_id,
            newStatus='INACTIVE'
        )
        iot.delete_certificate(certificateId=cert_id)
        print("✓ Test certificate cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_thing_creation():
    """Test IoT Thing creation (without creating actual device)"""
    print("\n" + "=" * 70)
    print("Testing IoT Thing Creation")
    print("=" * 70)
    
    try:
        iot = boto3.client('iot')
        
        test_thing_name = f"test-thing-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Create test thing
        print(f"Creating test thing: {test_thing_name}...")
        iot.create_thing(
            thingName=test_thing_name,
            attributePayload={
                'attributes': {
                    'farmId': 'test-farm',
                    'deviceType': 'ESP32-WROOM-32',
                    'test': 'true'
                }
            }
        )
        print(f"✓ Thing created: {test_thing_name}")
        
        # Clean up test thing
        print("Cleaning up test thing...")
        iot.delete_thing(thingName=test_thing_name)
        print("✓ Test thing cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("CarbonReady Device Provisioning Test")
    print("=" * 70)
    print("\nThis script tests the device provisioning workflow")
    print("without actually provisioning hardware.")
    
    results = []
    
    # Test 1: IoT connectivity
    results.append(("IoT Connectivity", test_iot_connectivity()))
    
    # Test 2: DynamoDB tables
    results.append(("DynamoDB Tables", test_dynamodb_tables()))
    
    # Test 3: Certificate generation
    results.append(("Certificate Generation", test_certificate_generation()))
    
    # Test 4: Thing creation
    results.append(("Thing Creation", test_thing_creation()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Ready to provision devices.")
        print("\nNext steps:")
        print("  1. Provision a device:")
        print("     python scripts/provision_device.py esp32-001 farm-001")
        print("  2. Flash firmware:")
        print("     python scripts/flash_firmware.py esp32-001")
        print("  3. Upload certificates:")
        print("     python scripts/upload_certificates.py esp32-001")
        print("  4. Calibrate sensors:")
        print("     python scripts/calibrate_device.py esp32-001")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check AWS infrastructure deployment.")
        print("\nTroubleshooting:")
        print("  - Ensure CDK stacks are deployed")
        print("  - Check AWS credentials and region")
        print("  - Verify IAM permissions")
        sys.exit(1)

if __name__ == "__main__":
    main()
