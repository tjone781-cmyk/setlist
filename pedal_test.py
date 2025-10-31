#!/usr/bin/env python3
"""
Bluetooth Pedal HID Event Test
Tests what input the Bluetooth pedal sends when pressed
"""
import os
import sys
import select
import struct
import time

def test_pedal_input():
    print("🎵 Bluetooth Pedal Input Test")
    print("=" * 40)
    
    # Find the pedal input device
    input_devices = []
    for i in range(10):
        device = f"/dev/input/event{i}"
        if os.path.exists(device):
            input_devices.append(device)
    
    print(f"Available input devices: {input_devices}")
    
    # Try to read from the most recent event device (likely the pedal)
    if input_devices:
        device = input_devices[-1]  # Usually the most recently connected
        print(f"Testing device: {device}")
        print("Press the pedal buttons now...")
        print("(Will timeout after 10 seconds)")
        
        try:
            with open(device, 'rb') as f:
                start_time = time.time()
                while time.time() - start_time < 10:
                    # Check if data is available
                    ready, _, _ = select.select([f], [], [], 0.1)
                    if ready:
                        data = f.read(24)  # Input event structure is 24 bytes
                        if len(data) == 24:
                            # Unpack input event: time, type, code, value
                            sec, usec, type_, code, value = struct.unpack('llHHi', data)
                            if type_ == 1 and value == 1:  # EV_KEY, key press
                                print(f"🔴 Key press detected: code={code}, value={value}")
                                
                                # Check if this matches our expected codes
                                if code == 108:  # Down arrow or similar
                                    print("  → This might be NEXT song command!")
                                elif code == 103:  # Up arrow or similar  
                                    print("  → This might be PREVIOUS song command!")
                                else:
                                    print(f"  → Unknown key code: {code}")
                
        except PermissionError:
            print("❌ Permission denied. Try running as sudo:")
            print(f"   sudo python3 {sys.argv[0]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ No input devices found")

if __name__ == "__main__":
    test_pedal_input()