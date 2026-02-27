#!/usr/bin/env python3
"""
ESP32 Certificate Upload Script

This script uploads X.509 certificates to the ESP32 SPIFFS partition.
Certificates are stored in SPIFFS (not embedded in firmware) for security.

Requirements: 11.3, 22.2
"""
import subprocess
import sys
import argparse
from pathlib import Path
import serial.tools.list_ports
import tempfile
import shutil

def find_esp32_port():
    """
    Auto-detect ESP32 serial port
    """
    print("🔍 Searching for ESP32 device...")
    
    ports = serial.tools.list_ports.comports()
    esp32_ports = []
    
    for port in ports:
        if any(chip in port.description.upper() for chip in ['CP210', 'CH340', 'UART', 'USB']):
            esp32_ports.append(port.device)
            print(f"  Found potential ESP32: {port.device} - {port.description}")
    
    if not esp32_ports:
        print("⚠️  No ESP32 device detected")
        return None
    
    if len(esp32_ports) == 1:
        print(f"✓ Using port: {esp32_ports[0]}")
        return esp32_ports[0]
    
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

def prepare_spiffs_data(device_id, cert_dir):
    """
    Prepare SPIFFS data directory with certificates
    """
    print(f"\n📁 Preparing SPIFFS data for {device_id}...")
    
    device_cert_dir = Path(cert_dir) / device_id
    if not device_cert_dir.exists():
        print(f"❌ Certificate directory not found: {device_cert_dir}")
        print(f"   Run: python scripts/provision_device.py {device_id} <farm_id>")
        return None
    
    # Create temporary SPIFFS data directory
    spiffs_data_dir = Path("firmware/esp32/data")
    spiffs_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy certificates to SPIFFS data directory
    files_to_copy = [
        ("device.crt", "device.crt"),
        ("device.key", "device.key"),
        ("AmazonRootCA1.pem", "root_ca.pem"),
        ("device_config.json", "config.json")
    ]
    
    for src_name, dst_name in files_to_copy:
        src_file = device_cert_dir / src_name
        dst_file = spiffs_data_dir / dst_name
        
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            print(f"  ✓ Copied {src_name} -> {dst_name}")
        else:
            print(f"  ⚠️  Missing: {src_name}")
            return None
    
    print(f"✓ SPIFFS data prepared in: {spiffs_data_dir}")
    return spiffs_data_dir

def upload_spiffs(port=None):
    """
    Upload SPIFFS filesystem to ESP32
    """
    print("\n📤 Uploading SPIFFS to ESP32...")
    
    firmware_dir = Path("firmware/esp32")
    
    # Build command
    cmd = ["platformio", "run", "--target", "uploadfs"]
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
            print("✓ SPIFFS uploaded successfully")
            print("\n📋 Upload output:")
            print(result.stdout)
            return True
        else:
            print(f"❌ SPIFFS upload failed:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ PlatformIO not found. Please install it:")
        print("   pip install platformio")
        return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def cleanup_spiffs_data():
    """
    Clean up temporary SPIFFS data directory
    """
    spiffs_data_dir = Path("firmware/esp32/data")
    if spiffs_data_dir.exists():
        print("\n🧹 Cleaning up temporary SPIFFS data...")
        shutil.rmtree(spiffs_data_dir)
        print("✓ Cleanup complete")

def main():
    parser = argparse.ArgumentParser(
        description='Upload certificates to ESP32 SPIFFS partition'
    )
    parser.add_argument(
        'device_id',
        help='Device identifier (e.g., esp32-001)'
    )
    parser.add_argument(
        '--cert-dir',
        default='device_certs',
        help='Certificate directory (default: device_certs)'
    )
    parser.add_argument(
        '--port',
        help='Serial port (auto-detected if not specified)'
    )
    parser.add_argument(
        '--keep-data',
        action='store_true',
        help='Keep SPIFFS data directory after upload'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CarbonReady ESP32 Certificate Upload")
    print("=" * 70)
    print(f"Device ID: {args.device_id}")
    
    try:
        # Step 1: Find ESP32 port
        port = args.port
        if not port:
            port = find_esp32_port()
            if not port:
                print("\n❌ No ESP32 device found")
                print("   Please specify port manually with --port")
                sys.exit(1)
        
        # Step 2: Prepare SPIFFS data
        spiffs_data_dir = prepare_spiffs_data(args.device_id, args.cert_dir)
        if not spiffs_data_dir:
            print("\n❌ Failed to prepare SPIFFS data")
            sys.exit(1)
        
        # Step 3: Upload SPIFFS
        if not upload_spiffs(port):
            print("\n❌ SPIFFS upload failed")
            sys.exit(1)
        
        # Step 4: Cleanup (unless --keep-data specified)
        if not args.keep_data:
            cleanup_spiffs_data()
        
        # Success
        print("\n" + "=" * 70)
        print("✅ Certificate upload completed successfully!")
        print("=" * 70)
        print("\n📋 Certificates stored in SPIFFS partition:")
        print("  - device.crt (Device certificate)")
        print("  - device.key (Private key)")
        print("  - root_ca.pem (Amazon Root CA)")
        print("  - config.json (Device configuration)")
        print("\n📋 Next steps:")
        print("  1. Power cycle the ESP32 device")
        print("  2. Perform initial sensor calibration")
        print(f"     python scripts/calibrate_device.py {args.device_id}")
        print("  3. Deploy device to farm location")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload cancelled by user")
        cleanup_spiffs_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        cleanup_spiffs_data()
        sys.exit(1)

if __name__ == "__main__":
    main()
