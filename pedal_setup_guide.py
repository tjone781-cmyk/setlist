#!/usr/bin/env python3
"""
Donner DBM-20 Bluetooth Pedal Setup Guide

The pedal sends these escape sequences:
- Left pedal: ^[[A (Up arrow)
- Right pedal: ^[[B (Down arrow)

This translates to:
- Left pedal: Previous song  
- Right pedal: Next song
"""

print("🎸 Donner DBM-20 Bluetooth Pedal Setup")
print("=" * 40)
print()

print("1️⃣  PAIR THE PEDAL:")
print("   sudo bluetoothctl")
print("   scan on")
print("   # Wait for DBM-20 to appear")
print("   pair XX:XX:XX:XX:XX:XX")  
print("   connect XX:XX:XX:XX:XX:XX")
print("   trust XX:XX:XX:XX:XX:XX")
print()

print("2️⃣  TEST THE PEDAL:")
print("   # After pairing, test in terminal:")
print("   cat")
print("   # Press pedal buttons - you should see:")
print("   # Left pedal: ^[[A") 
print("   # Right pedal: ^[[B")
print("   # Press Ctrl+C to exit cat")
print()

print("3️⃣  SETLIST APP INTEGRATION:")
print("   # The app is now listening for these sequences")
print("   # Start the app and press the pedal buttons")
print("   cd /home/tjone/setlist_app")
print("   python3 main.py")
print()

print("4️⃣  TROUBLESHOOTING:")
print("   # If pedal doesn't work:")
print("   # 1. Check pairing: bluetoothctl info XX:XX:XX:XX:XX:XX")
print("   # 2. Check input: cat /proc/bus/input/devices | grep -A5 DBM")
print("   # 3. Manual test: echo -e '\\033[A' (simulates left pedal)")
print()

print("✅ READY FOR LIVE PERFORMANCE!")
print("   Left pedal = Previous song")  
print("   Right pedal = Next song")
print("   Enjoy your show! 🎵")