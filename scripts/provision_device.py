#!/usr/bin/env python3
"""
ESP32 Device Provisioning Script

This script provisions ESP32 devices for the CarbonReady system by:
1. Generating unique X.509 certificates for AWS IoT Core authentication
2. Creating IoT Thing and attaching certificates
3. Saving certificates to local directory for SPIFFS upload
4. Logging calibration requirement

Requirements: 11.1, 11.3, 18.1
"""
import boto3
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse

# AWS clients
iot = boto3.client('iot')
dynamodb = boto3.resource('dynamodb')

def get_calibration_table():
    """Find the sensor calibration table"""
    client = boto3.client('dynamodb')
    tables = client.list_tables()['TableNames']
    matching = [t for t in tables if 'SensorCalibrationTable' in t]
    if matching:
        return matching[0]
    raise Exception("Sensor calibration table not found. Deploy infrastructure first.")

def create_device_certificates(device_id):
    """
    Generate unique X.509 certificates for device
    Returns: certificate ARN, certificate ID, certificate PEM, key pair
    """
    print(f"\nGenerating X.509 certificates for {device_id}...")
    
    # Create keys and certificate
    response = iot.create_keys_and_certificate(setAsActive=True)
    
    certificate_arn = response['certificateArn']
    certificate_id = response['certificateId']
    certificate_pem = response['certificatePem']
    key_pair = {
        'public': response['keyPair']['PublicKey'],
        'private': response['keyPair']['PrivateKey']
    }
    
    print(f"[OK] Certificate created: {certificate_id}")
    print(f"  ARN: {certificate_arn}")
    
    return certificate_arn, certificate_id, certificate_pem, key_pair

def create_iot_thing(device_id, farm_id, certificate_arn):
    """
    Create IoT Thing and attach certificate and policy
    """
    print(f"\nCreating IoT Thing: {device_id}...")
    
    # Create Thing with farm_id attribute
    # Note: AWS IoT attributes don't allow + character, so use Z format for UTC
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    try:
        iot.create_thing(
            thingName=device_id,
            attributePayload={
                'attributes': {
                    'farmId': farm_id,
                    'deviceType': 'ESP32-WROOM-32',
                    'provisionedAt': timestamp
                }
            }
        )
        print(f"[OK] Thing created: {device_id}")
    except iot.exceptions.ResourceAlreadyExistsException:
        print(f"[WARN] Thing {device_id} already exists, updating attributes...")
        iot.update_thing(
            thingName=device_id,
            attributePayload={
                'attributes': {
                    'farmId': farm_id,
                    'deviceType': 'ESP32-WROOM-32',
                    'provisionedAt': timestamp
                }
            }
        )
    
    # Attach certificate to Thing
    print(f"Attaching certificate to Thing...")
    iot.attach_thing_principal(
        thingName=device_id,
        principal=certificate_arn
    )
    print(f"[OK] Certificate attached to Thing")
    
    # Attach policy to certificate
    policy_name = "CarbonReadyESP32SensorPolicy"
    print(f"Attaching policy {policy_name}...")
    try:
        iot.attach_policy(
            policyName=policy_name,
            target=certificate_arn
        )
        print(f"[OK] Policy attached to certificate")
    except Exception as e:
        print(f"[WARN] Warning: Could not attach policy: {e}")
        print(f"  Make sure the IoT stack is deployed")

def save_certificates(device_id, certificate_pem, key_pair, output_dir):
    """
    Save certificates to local directory for SPIFFS upload
    """
    print(f"\nSaving certificates to {output_dir}...")
    
    # Create device-specific directory
    device_dir = Path(output_dir) / device_id
    device_dir.mkdir(parents=True, exist_ok=True)
    
    # Save certificate
    cert_file = device_dir / "device.crt"
    with open(cert_file, 'w') as f:
        f.write(certificate_pem)
    print(f"[OK] Certificate saved: {cert_file}")
    
    # Save private key
    key_file = device_dir / "device.key"
    with open(key_file, 'w') as f:
        f.write(key_pair['private'])
    print(f"[OK] Private key saved: {key_file}")
    
    # Save public key (for reference)
    pub_key_file = device_dir / "device.pub"
    with open(pub_key_file, 'w') as f:
        f.write(key_pair['public'])
    print(f"[OK] Public key saved: {pub_key_file}")
    
    # Download Amazon Root CA (if not already present)
    root_ca_file = device_dir / "AmazonRootCA1.pem"
    if not root_ca_file.exists():
        print(f"Downloading Amazon Root CA...")
        import urllib.request
        root_ca_url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        urllib.request.urlretrieve(root_ca_url, root_ca_file)
        print(f"[OK] Root CA saved: {root_ca_file}")
    
    return device_dir

def create_device_config(device_id, farm_id, output_dir):
    """
    Create device configuration file for firmware
    """
    print(f"\nCreating device configuration...")
    
    # Get IoT endpoint
    endpoint_response = iot.describe_endpoint(endpointType='iot:Data-ATS')
    iot_endpoint = endpoint_response['endpointAddress']
    
    device_dir = Path(output_dir) / device_id
    
    # Create config JSON
    config = {
        "deviceId": device_id,
        "farmId": farm_id,
        "iotEndpoint": iot_endpoint,
        "mqttPort": 8883,
        "provisionedAt": datetime.now(timezone.utc).isoformat()
    }
    
    config_file = device_dir / "device_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"[OK] Configuration saved: {config_file}")
    print(f"  IoT Endpoint: {iot_endpoint}")
    
    return config

def log_calibration_requirement(device_id, farm_id):
    """
    Log that device requires initial calibration
    Requirement 18.1: Require sensor calibration confirmation before accepting data
    """
    print(f"\nLogging calibration requirement...")
    
    try:
        table_name = get_calibration_table()
        table = dynamodb.Table(table_name)
        
        # Create a pending calibration record
        calibration_record = {
            'deviceId': device_id,
            'calibrationDate': datetime.now(timezone.utc).isoformat(),
            'calibrationType': 'pending_initial',
            'farmId': farm_id,
            'calibrationParameters': {},
            'referenceValues': {},
            'performedBy': 'provisioning_script',
            'nextCalibrationDue': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            'status': 'PENDING'
        }
        
        table.put_item(Item=calibration_record)
        print(f"[OK] Calibration requirement logged")
        print(f"  [IMPORTANT] Device requires initial calibration before use")
        print(f"  Run: python scripts/calibrate_device.py {device_id}")
        
    except Exception as e:
        print(f"[WARN] Warning: Could not log calibration requirement: {e}")

def provision_device(device_id, farm_id, output_dir="device_certs"):
    """
    Complete device provisioning workflow
    """
    print("=" * 70)
    print("CarbonReady ESP32 Device Provisioning")
    print("=" * 70)
    print(f"Device ID: {device_id}")
    print(f"Farm ID: {farm_id}")
    print(f"Output Directory: {output_dir}")
    
    try:
        # Step 1: Generate certificates
        cert_arn, cert_id, cert_pem, key_pair = create_device_certificates(device_id)
        
        # Step 2: Create IoT Thing and attach certificate
        create_iot_thing(device_id, farm_id, cert_arn)
        
        # Step 3: Save certificates locally
        device_dir = save_certificates(device_id, cert_pem, key_pair, output_dir)
        
        # Step 4: Create device configuration
        config = create_device_config(device_id, farm_id, output_dir)
        
        # Step 5: Log calibration requirement
        log_calibration_requirement(device_id, farm_id)
        
        # Success summary
        print("\n" + "=" * 70)
        print("[SUCCESS] Device provisioning completed successfully!")
        print("=" * 70)
        print(f"\nCertificates and configuration saved to: {device_dir}")
        print(f"\nNext steps:")
        print(f"  1. Flash firmware to ESP32 device")
        print(f"     python scripts/flash_firmware.py {device_id}")
        print(f"  2. Upload certificates to SPIFFS partition")
        print(f"     python scripts/upload_certificates.py {device_id}")
        print(f"  3. Perform initial sensor calibration")
        print(f"     python scripts/calibrate_device.py {device_id}")
        print(f"  4. Deploy device to farm location")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during provisioning: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Provision ESP32 device for CarbonReady system'
    )
    parser.add_argument('device_id', help='Unique device identifier (e.g., esp32-001)')
    parser.add_argument('farm_id', help='Farm identifier (e.g., farm-001)')
    parser.add_argument(
        '--output-dir',
        default='device_certs',
        help='Output directory for certificates (default: device_certs)'
    )
    
    args = parser.parse_args()
    
    success = provision_device(args.device_id, args.farm_id, args.output_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
