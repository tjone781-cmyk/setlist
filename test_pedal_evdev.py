#!/usr/bin/env python3
"""
Test Donner DBM-20 pedal using evdev to read input events directly
"""
import evdev
import sys
import time

def test_pedal_evdev():
    print("🎸 Donner DBM-20 Pedal Test (evdev)")
    print("====================================")
    
    # Find the pedal device
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    pedal_device = None
    
    print("Available input devices:")
    for device in devices:
        print(f"  {device.path}: {device.name}")
        if "music pedal" in device.name.lower() or "pedal" in device.name.lower():
            pedal_device = device
            print(f"    *** Found pedal device! ***")
    
    if not pedal_device:
        print("❌ No pedal device found!")
        print("Looking for any device with 'Bluetooth' in name...")
        for device in devices:
            if "bluetooth" in device.name.lower():
                pedal_device = device
                print(f"    *** Trying Bluetooth device: {device.name} ***")
                break
    
    if not pedal_device:
        print("❌ No suitable device found!")
        return
    
    print(f"\n✅ Using device: {pedal_device.path} - {pedal_device.name}")
    print(f"Device capabilities: {pedal_device.capabilities()}")
    print("\nPress pedal buttons (Ctrl+C to quit)...")
    print("Expected: Left button should send UP arrow, Right button should send DOWN arrow")
    
    try:
        for event in pedal_device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                if key_event.keystate == evdev.KeyEvent.key_down:
                    key_name = evdev.ecodes.KEY[event.code] if event.code in evdev.ecodes.KEY else f"KEY_{event.code}"
                    print(f"🎵 Button pressed: {key_name} (code: {event.code})")
                    
                    # Check for expected arrow keys
                    if event.code == evdev.ecodes.KEY_UP:
                        print("   → This is UP ARROW (LEFT pedal button)")
                    elif event.code == evdev.ecodes.KEY_DOWN:
                        print("   → This is DOWN ARROW (RIGHT pedal button)")
                    elif event.code == evdev.ecodes.KEY_LEFT:
                        print("   → This is LEFT ARROW")
                    elif event.code == evdev.ecodes.KEY_RIGHT:
                        print("   → This is RIGHT ARROW")
                    else:
                        print(f"   → Unknown key (expected UP/DOWN arrows)")
    
    except KeyboardInterrupt:
        print("\n\nTest completed!")
    except PermissionError:
        print(f"\n❌ Permission denied accessing {pedal_device.path}")
        print("Try running with sudo or add user to input group:")
        print("  sudo usermod -a -G input $USER")
        print("  Then log out and back in")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_pedal_evdev()