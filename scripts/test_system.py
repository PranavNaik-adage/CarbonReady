"""
System Testing Script for CarbonReady
Tests the deployed infrastructure end-to-end
"""
import json
import hashlib
import sys
from datetime import datetime

def create_test_payload(farm_id="farm-001", device_id="test-esp32-001"):
    """Create a test sensor payload with valid hash"""
    payload = {
        "farmId": farm_id,
        "deviceId": device_id,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readings": {
            "soilMoisture": 45.5,
            "soilTemperature": 25.3,
            "airTemperature": 28.7,
            "humidity": 65.2
        }
    }
    
    # Compute SHA-256 hash
    payload_str = json.dumps(payload, sort_keys=True)
    payload['hash'] = hashlib.sha256(payload_str.encode()).hexdigest()
    
    return payload

def create_bad_hash_payload(farm_id="farm-001", device_id="test-esp32-001"):
    """Create a test payload with invalid hash (for testing tampering detection)"""
    payload = create_test_payload(farm_id, device_id)
    payload['hash'] = "invalid_hash_12345"
    return payload

def create_invalid_data_payload(farm_id="farm-001", device_id="test-esp32-001"):
    """Create a test payload with out-of-range values"""
    payload = {
        "farmId": farm_id,
        "deviceId": device_id,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readings": {
            "soilMoisture": 150.0,  # Invalid: > 100
            "soilTemperature": 25.3,
            "airTemperature": 28.7,
            "humidity": 65.2
        }
    }
    
    # Compute valid hash (but data is invalid)
    payload_str = json.dumps(payload, sort_keys=True)
    payload['hash'] = hashlib.sha256(payload_str.encode()).hexdigest()
    
    return payload

def save_payload(payload, filename):
    """Save payload to JSON file"""
    with open(filename, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"✓ Created {filename}")

if __name__ == "__main__":
    print("CarbonReady System Test Payload Generator")
    print("=" * 50)
    
    # Create test payloads
    print("\nGenerating test payloads...")
    
    # 1. Valid payload
    valid_payload = create_test_payload()
    save_payload(valid_payload, "test-valid-sensor-data.json")
    
    # 2. Invalid hash payload (for tampering test)
    bad_hash_payload = create_bad_hash_payload()
    save_payload(bad_hash_payload, "test-bad-hash-data.json")
    
    # 3. Invalid data payload (for validation test)
    invalid_data_payload = create_invalid_data_payload()
    save_payload(invalid_data_payload, "test-invalid-data.json")
    
    print("\n" + "=" * 50)
    print("Test payloads created successfully!")
    print("\nNext steps:")
    print("1. Run: python scripts/init_cri_weights.py")
    print("2. Create sensor calibration (see TESTING_COMMANDS.md)")
    print("3. Test data ingestion with generated payloads")
    print("=" * 50)
