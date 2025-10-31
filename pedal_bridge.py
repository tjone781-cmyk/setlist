#!/usr/bin/env python3
"""
Bluetooth Pedal Bridge Service
Listens for Bluetooth pedal HID input and sends TCP commands to main app
Run as: sudo python3 pedal_bridge.py
"""
import select
import struct
import socket
import time
import os

def send_tcp_command(command):
    """Send command to main app via TCP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 6789))
        sock.send(command.encode())
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Failed to send TCP command: {e}")
        return False

def main():
    print("🎵 Bluetooth Pedal Bridge Service")
    print("=" * 40)
    print("Connecting pedal input to setlist app...")
    
    # Find the pedal input device
    input_device = None
    for i in range(20, -1, -1):
        device = f"/dev/input/event{i}"
        if os.path.exists(device):
            input_device = device
            break
    
    if not input_device:
        print("❌ No input device found")
        return
        
    print(f"📡 Listening on {input_device}")
    print("🎵 Press pedal buttons to test...")
    
    try:
        with open(input_device, 'rb') as f:
            while True:
                # Check if data is available
                ready, _, _ = select.select([f], [], [], 0.1)
                if ready:
                    data = f.read(24)
                    if len(data) == 24:
                        # Unpack input event
                        sec, usec, type_, code, value = struct.unpack('llHHi', data)
                        if type_ == 1 and value == 1:  # Key press
                            if code == 108:  # Down arrow - Next
                                print("🎵 Next song")
                                if send_tcp_command("40("):
                                    print("✅ Command sent")
                            elif code == 103:  # Up arrow - Previous
                                print("🎵 Previous song") 
                                if send_tcp_command("38&"):
                                    print("✅ Command sent")
                            else:
                                print(f"🎵 Unknown key: {code}")
                
    except KeyboardInterrupt:
        print("\n👋 Pedal bridge stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()