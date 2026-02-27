#!/usr/bin/env python3
"""
ESP32 Sensor Calibration Script

This script performs initial sensor calibration for ESP32 devices.
It guides the user through the calibration process and logs the results.

Requirements: 18.1, 18.2, 18.5
"""
import boto3
import sys
import argparse
from datetime import datetime, timezone, timedelta
import json

dynamodb = boto3.resource('dynamodb')

def get_calibration_table():
    """Find the sensor calibration table"""
    client = boto3.client('dynamodb')
    tables = client.list_tables()['TableNames']
    matching = [t for t in tables if 'SensorCalibrationTable' in t]
    if matching:
        return matching[0]
    raise Exception("Sensor calibration table not found. Deploy infrastructure first.")

def get_device_info(device_id, cert_dir):
    """Get device configuration"""
    from pathlib import Path
    
    config_file = Path(cert_dir) / device_id / "device_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def perform_soil_moisture_calibration():
    """
    Guide user through soil moisture sensor calibration
    """
    print("\n" + "=" * 70)
    print("Soil Moisture Sensor Calibration")
    print("=" * 70)
    print("\nThis calibration requires two measurements:")
    print("  1. Dry soil measurement (sensor in air or completely dry soil)")
    print("  2. Wet soil measurement (sensor in water or saturated soil)")
    print("\nThese values will be used to map ADC readings to 0-100% moisture.")
    
    input("\nPress Enter when ready to start calibration...")
    
    # Dry calibration
    print("\n📏 Step 1: Dry Soil Calibration")
    print("   Place the soil moisture sensor in air or completely dry soil")
    input("   Press Enter when ready to measure...")
    
    while True:
        try:
            dry_value = int(input("   Enter ADC reading for dry soil (typically 2500-4095): "))
            if 0 <= dry_value <= 4095:
                break
            print("   ⚠️  Value must be between 0 and 4095")
        except ValueError:
            print("   ⚠️  Please enter a valid number")
    
    print(f"   ✓ Dry value recorded: {dry_value}")
    
    # Wet calibration
    print("\n📏 Step 2: Wet Soil Calibration")
    print("   Place the soil moisture sensor in water or fully saturated soil")
    input("   Press Enter when ready to measure...")
    
    while True:
        try:
            wet_value = int(input("   Enter ADC reading for wet soil (typically 500-1500): "))
            if 0 <= wet_value <= 4095:
                break
            print("   ⚠️  Value must be between 0 and 4095")
        except ValueError:
            print("   ⚠️  Please enter a valid number")
    
    print(f"   ✓ Wet value recorded: {wet_value}")
    
    # Validate calibration
    if dry_value <= wet_value:
        print("\n   ⚠️  WARNING: Dry value should be greater than wet value")
        print(f"   Dry: {dry_value}, Wet: {wet_value}")
        confirm = input("   Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            return None
    
    return {
        'soilMoistureDry': dry_value,
        'soilMoistureWet': wet_value
    }

def perform_temperature_calibration():
    """
    Guide user through temperature sensor calibration
    """
    print("\n" + "=" * 70)
    print("Temperature Sensor Calibration")
    print("=" * 70)
    print("\nTemperature sensors (DHT22 and DS18B20) are typically pre-calibrated.")
    print("This step verifies the sensors are reading reasonable values.")
    
    input("\nPress Enter to continue...")
    
    # Air temperature check
    print("\n🌡️  Air Temperature (DHT22)")
    while True:
        try:
            air_temp = float(input("   Enter current air temperature reading (°C): "))
            if -10 <= air_temp <= 60:
                break
            print("   ⚠️  Value outside expected range (-10 to 60°C)")
        except ValueError:
            print("   ⚠️  Please enter a valid number")
    
    print(f"   ✓ Air temperature recorded: {air_temp}°C")
    
    # Soil temperature check
    print("\n🌡️  Soil Temperature (DS18B20)")
    while True:
        try:
            soil_temp = float(input("   Enter current soil temperature reading (°C): "))
            if -10 <= soil_temp <= 60:
                break
            print("   ⚠️  Value outside expected range (-10 to 60°C)")
        except ValueError:
            print("   ⚠️  Please enter a valid number")
    
    print(f"   ✓ Soil temperature recorded: {soil_temp}°C")
    
    # Humidity check
    print("\n💧 Humidity (DHT22)")
    while True:
        try:
            humidity = float(input("   Enter current humidity reading (%): "))
            if 0 <= humidity <= 100:
                break
            print("   ⚠️  Value outside expected range (0-100%)")
        except ValueError:
            print("   ⚠️  Please enter a valid number")
    
    print(f"   ✓ Humidity recorded: {humidity}%")
    
    return {
        'airTemperatureReference': air_temp,
        'soilTemperatureReference': soil_temp,
        'humidityReference': humidity
    }

def log_calibration(device_id, farm_id, calibration_params, reference_values, performed_by):
    """
    Log calibration event to DynamoDB
    Requirements: 18.2, 18.5
    """
    print("\n💾 Logging calibration to database...")
    
    try:
        table_name = get_calibration_table()
        table = dynamodb.Table(table_name)
        
        calibration_date = datetime.now(timezone.utc).isoformat()
        next_calibration = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        
        # Create calibration record
        calibration_record = {
            'deviceId': device_id,
            'calibrationDate': calibration_date,
            'calibrationType': 'initial',
            'farmId': farm_id,
            'calibrationParameters': calibration_params,
            'referenceValues': reference_values,
            'performedBy': performed_by,
            'nextCalibrationDue': next_calibration,
            'status': 'COMPLETED'
        }
        
        table.put_item(Item=calibration_record)
        
        print("✓ Calibration logged successfully")
        print(f"  Device ID: {device_id}")
        print(f"  Farm ID: {farm_id}")
        print(f"  Calibration Date: {calibration_date}")
        print(f"  Next Calibration Due: {next_calibration}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error logging calibration: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_calibration(device_id):
    """
    Verify calibration was logged correctly
    """
    print("\n🔍 Verifying calibration...")
    
    try:
        table_name = get_calibration_table()
        table = dynamodb.Table(table_name)
        
        response = table.query(
            KeyConditionExpression='deviceId = :device_id',
            ExpressionAttributeValues={':device_id': device_id},
            ScanIndexForward=False,  # Most recent first
            Limit=1
        )
        
        if response['Items']:
            calibration = response['Items'][0]
            if calibration.get('status') == 'COMPLETED':
                print("✓ Calibration verified in database")
                print(f"  Type: {calibration.get('calibrationType')}")
                print(f"  Date: {calibration.get('calibrationDate')}")
                return True
            else:
                print(f"⚠️  Calibration status: {calibration.get('status')}")
                return False
        else:
            print("❌ No calibration record found")
            return False
            
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Perform initial sensor calibration for ESP32 device'
    )
    parser.add_argument(
        'device_id',
        help='Device identifier (e.g., esp32-001)'
    )
    parser.add_argument(
        '--farm-id',
        help='Farm identifier (auto-detected from device config if not specified)'
    )
    parser.add_argument(
        '--cert-dir',
        default='device_certs',
        help='Certificate directory (default: device_certs)'
    )
    parser.add_argument(
        '--performed-by',
        default='technician',
        help='Name of person performing calibration'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CarbonReady ESP32 Sensor Calibration")
    print("=" * 70)
    print(f"Device ID: {args.device_id}")
    
    # Get farm ID
    farm_id = args.farm_id
    if not farm_id:
        device_info = get_device_info(args.device_id, args.cert_dir)
        if device_info:
            farm_id = device_info.get('farmId')
            print(f"Farm ID: {farm_id} (from device config)")
        else:
            print("\n⚠️  Could not auto-detect farm ID")
            farm_id = input("Enter farm ID: ")
    else:
        print(f"Farm ID: {farm_id}")
    
    print(f"Performed by: {args.performed_by}")
    
    try:
        # Step 1: Soil moisture calibration
        soil_moisture_params = perform_soil_moisture_calibration()
        if not soil_moisture_params:
            print("\n❌ Soil moisture calibration cancelled")
            sys.exit(1)
        
        # Step 2: Temperature sensor verification
        temp_reference_values = perform_temperature_calibration()
        
        # Combine all calibration data
        calibration_params = soil_moisture_params
        reference_values = temp_reference_values
        
        # Step 3: Log calibration
        if not log_calibration(
            args.device_id,
            farm_id,
            calibration_params,
            reference_values,
            args.performed_by
        ):
            print("\n❌ Failed to log calibration")
            sys.exit(1)
        
        # Step 4: Verify calibration
        verify_calibration(args.device_id)
        
        # Success
        print("\n" + "=" * 70)
        print("✅ Sensor calibration completed successfully!")
        print("=" * 70)
        print("\n📋 Calibration Summary:")
        print(f"  Soil Moisture Dry: {calibration_params['soilMoistureDry']}")
        print(f"  Soil Moisture Wet: {calibration_params['soilMoistureWet']}")
        print(f"  Air Temperature: {reference_values['airTemperatureReference']}°C")
        print(f"  Soil Temperature: {reference_values['soilTemperatureReference']}°C")
        print(f"  Humidity: {reference_values['humidityReference']}%")
        print("\n📋 Next steps:")
        print("  1. Update firmware config.h with calibration values")
        print("  2. Rebuild and reflash firmware")
        print("  3. Deploy device to farm location")
        print("  4. Monitor data ingestion in CloudWatch")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Calibration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
