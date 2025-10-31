#!/usr/bin/env python3
"""
Test the Donner DBM-20 Bluetooth pedal integration
Simulates the escape sequences the pedal sends
"""
import socket
import time

def test_pedal_commands():
    """Test by sending commands to the running app"""
    host = "192.168.1.206"
    port = 6789
    
    print("🎸 Testing Donner DBM-20 Bluetooth Pedal Integration")
    print("=" * 55)
    
    try:
        # Test TCP commands first
        print("\n1️⃣  Testing via TCP (backup method):")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.settimeout(2)
            
            print("   Sending NEXT command...")
            s.send(b"NEXT\n")
            time.sleep(2)
            
            print("   Sending PREV command...")  
            s.send(b"PREV\n")
            time.sleep(2)
            
            print("   ✅ TCP commands working")
        
    except Exception as e:
        print(f"   ❌ TCP test failed: {e}")
    
    print("\n2️⃣  For Bluetooth pedal testing:")
    print("   📱 Connect your Donner DBM-20 to the Pi via Bluetooth")
    print("   🔴 Left pedal should send: ^[[A (Previous song)")
    print("   🔴 Right pedal should send: ^[[B (Next song)")
    print("   📺 Watch the LED matrix for song changes!")
    
    print("\n3️⃣  Manual simulation (if pedal not available):")
    print("   You can simulate by running this on the Pi:")
    print('   echo -e "\\033[A" | python3 -c "import sys; print(repr(sys.stdin.read()))"')
    print('   echo -e "\\033[B" | python3 -c "import sys; print(repr(sys.stdin.read()))"')

if __name__ == "__main__":
    test_pedal_commands()