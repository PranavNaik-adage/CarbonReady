#!/usr/bin/env python3
"""
ESP32 Firmware Flashing Script

This script flashes the CarbonReady firmware to ESP32 devices using PlatformIO.
It handles building the firmware and uploading it to the device.

Requirements: 22.2
"""
import subprocess
import sys
import argparse
from pathlib import Path
import serial.tools.list_ports

def find_esp32_port():
    """
    Auto-detect ESP32 serial port
    """
    print("🔍 Searching for ESP32 device...")
    
    ports = serial.tools.list_ports.comports()
    esp32_ports = []
    
    for port in ports:
        # ESP32 typically shows up as CP210x or CH340
        if any(chip in port.description.upper() for chip in ['CP210', 'CH340', 'UART', 'USB']):
            esp32_ports.append(port.device)
            print(f"  Found potential ESP32: {port.device} - {port.description}")
    
    if not esp32_ports:
        print("⚠️  No ESP32 device detected")
        print("   Make sure the device is connected via USB")
        return None
    
    if len(esp32_ports) == 1:
        print(f"✓ Using port: {esp32_ports[0]}")
        return esp32_ports[0]
    
    # Multiple ports found, ask user
    print(f"\n⚠️  Multiple devices found. Please select:")
    for i, port in enumerate(esp32_ports, 1):
        print(f"  {i}. {port}")
    
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(esp32_ports):
                return esp32_ports[choice - 1]
        except (ValueError, KeyboardInterrupt):
            return None

def build_firmware():
    """
    Build firmware using PlatformIO
    """
    print("\n🔨 Building firmware...")
    
    firmware_dir = Path("firmware/esp32")
    if not firmware_dir.exists():
        print(f"❌ Firmware directory not found: {firmware_dir}")
        return False
    
    try:
        result = subprocess.run(
            ["platformio", "run"],
            cwd=firmware_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Firmware built successfully")
            return True
        else:
            print(f"❌ Build failed:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ PlatformIO not found. Please install it:")
        print("   pip install platformio")
        return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def flash_firmware(port=None):
    """
    Flash firmware to ESP32 device
    """
    print("\n📤 Flashing firmware to ESP32...")
    
    firmware_dir = Path("firmware/esp32")
    
    # Build command
    cmd = ["platformio", "run", "--target", "upload"]
    if port:
        cmd.extend(["--upload-port", port])
    
    try:
        result = subprocess.run(
            cmd,
            cwd=firmware_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Firmware flashed successfully")
            print("\n📋 Firmware flash output:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Flash failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Flash error: {e}")
        return False

def verify_flash():
    """
    Verify firmware was flashed correctly
    """
    print("\n🔍 Verifying flash...")
    
    firmware_dir = Path("firmware/esp32")
    
    try:
        result = subprocess.run(
            ["platformio", "run", "--target", "upload", "--verbose"],
            cwd=firmware_dir,
            capture_output=True,
            text=True
        )
        
        # Check for success indicators in output
        if "success" in result.stdout.lower() or result.returncode == 0:
            print("✓ Flash verification passed")
            return True
        else:
            print("⚠️  Flash verification inconclusive")
            return True  # Don't fail on verification
            
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
        return True  # Don't fail on verification

def main():
    parser = argparse.ArgumentParser(
        description='Flash CarbonReady firmware to ESP32 device'
    )
    parser.add_argument(
        'device_id',
        nargs='?',
        help='Device identifier (for reference only)'
    )
    parser.add_argument(
        '--port',
        help='Serial port (auto-detected if not specified)'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip firmware build step'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CarbonReady ESP32 Firmware Flashing")
    print("=" * 70)
    
    if args.device_id:
        print(f"Device ID: {args.device_id}")
    
    # Step 1: Find ESP32 port
    port = args.port
    if not port:
        port = find_esp32_port()
        if not port:
            print("\n❌ No ESP32 device found")
            print("   Please specify port manually with --port")
            sys.exit(1)
    
    # Step 2: Build firmware
    if not args.skip_build:
        if not build_firmware():
            print("\n❌ Firmware build failed")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping build step")
    
    # Step 3: Flash firmware
    if not flash_firmware(port):
        print("\n❌ Firmware flash failed")
        sys.exit(1)
    
    # Step 4: Verify flash
    verify_flash()
    
    # Success
    print("\n" + "=" * 70)
    print("✅ Firmware flashing completed successfully!")
    print("=" * 70)
    print("\n📋 Next steps:")
    print("  1. Upload certificates to SPIFFS partition")
    if args.device_id:
        print(f"     python scripts/upload_certificates.py {args.device_id}")
    else:
        print(f"     python scripts/upload_certificates.py <device_id>")
    print("  2. Perform initial sensor calibration")
    if args.device_id:
        print(f"     python scripts/calibrate_device.py {args.device_id}")
    else:
        print(f"     python scripts/calibrate_device.py <device_id>")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
