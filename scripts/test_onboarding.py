#!/usr/bin/env python3
"""
Test Farm Onboarding Script

Quick test to verify the onboarding script works correctly.
This creates a test farm and verifies all components.

Usage:
    python scripts/test_onboarding.py
"""
import subprocess
import sys
import time
from datetime import datetime

def print_header(message):
    print(f"\n{'=' * 70}")
    print(message)
    print('=' * 70)

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{description}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Success")
            if result.stdout:
                print("Output:")
                print(result.stdout[:500])  # First 500 chars
            return True
        else:
            print("✗ Failed")
            if result.stderr:
                print("Error:")
                print(result.stderr[:500])
            return False
    except subprocess.TimeoutExpired:
        print("✗ Timeout")
        return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def main():
    print_header("CarbonReady Onboarding Script Test")
    
    # Generate test IDs with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_farm_id = f"test-farm-{timestamp}"
    test_device_id = f"test-esp32-{timestamp}"
    
    print(f"\nTest Farm ID: {test_farm_id}")
    print(f"Test Device ID: {test_device_id}")
    
    results = []
    
    # Test 1: Run onboarding script with coconut farm
    print_header("Test 1: Onboard Coconut Farm")
    success = run_command(
        [
            'python', 'scripts/onboard_farm.py',
            test_farm_id, test_device_id,
            '--crop-type', 'coconut',
            '--tree-age', '15',
            '--tree-height', '12.5',
            '--farm-size', '2.0',
            '--plantation-density', '180',
            '--skip-verification'  # Skip verification for faster test
        ],
        "Running onboarding script for coconut farm"
    )
    results.append(("Coconut farm onboarding", success))
    
    # Test 2: Run onboarding script with cashew farm
    print_header("Test 2: Onboard Cashew Farm")
    test_farm_id_2 = f"test-farm-{timestamp}-2"
    test_device_id_2 = f"test-esp32-{timestamp}-2"
    
    success = run_command(
        [
            'python', 'scripts/onboard_farm.py',
            test_farm_id_2, test_device_id_2,
            '--crop-type', 'cashew',
            '--tree-age', '10',
            '--dbh', '28.5',
            '--farm-size', '3.0',
            '--plantation-density', '250',
            '--skip-verification'  # Skip verification for faster test
        ],
        "Running onboarding script for cashew farm"
    )
    results.append(("Cashew farm onboarding", success))
    
    # Test 3: Verify help message
    print_header("Test 3: Verify Help Message")
    success = run_command(
        ['python', 'scripts/onboard_farm.py', '--help'],
        "Checking help message"
    )
    results.append(("Help message", success))
    
    # Test 4: Test with minimal arguments (defaults)
    print_header("Test 4: Onboard with Defaults")
    test_farm_id_3 = f"test-farm-{timestamp}-3"
    test_device_id_3 = f"test-esp32-{timestamp}-3"
    
    success = run_command(
        [
            'python', 'scripts/onboard_farm.py',
            test_farm_id_3, test_device_id_3,
            '--crop-type', 'coconut',
            '--skip-device',  # Skip device provisioning
            '--skip-verification'  # Skip verification
        ],
        "Running onboarding with default values"
    )
    results.append(("Onboarding with defaults", success))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed\n")
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print()
    
    if passed == total:
        print("✓ All tests passed!")
        print("\nThe onboarding script is working correctly.")
        print("\nCleanup:")
        print(f"  Test farms created: {test_farm_id}, {test_farm_id_2}, {test_farm_id_3}")
        print(f"  Test devices created: {test_device_id}, {test_device_id_2}")
        print("  You may want to delete these test resources from AWS.")
        return 0
    else:
        print("✗ Some tests failed.")
        print("\nPlease review the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
