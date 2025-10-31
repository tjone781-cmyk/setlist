#!/usr/bin/env python3
"""
Simple key monitor to see what the DBM-20 sends when buttons are pressed
"""

import evdev
import sys

def monitor_pedal():
    # Look for the DBM-20 (shows up as "Bluetooth Music Pedal")
    device = None
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if "music pedal" in dev.name.lower():
            device = dev
            print(f"✅ Found DBM-20: {dev.name} at {path}")
            break
    
    if not device:
        print("❌ DBM-20 not found. Available devices:")
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            print(f"  - {dev.name}")
        return
    
    print("🎵 Press pedal buttons now - I'll show you what keys they send...")
    print("   (Press Ctrl+C to stop)")
    
    try:
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                if key_event.keystate == evdev.KeyEvent.key_down:
                    print(f"🔘 Button pressed: {key_event.keycode}")
    except KeyboardInterrupt:
        print("\n👋 Done monitoring")

if __name__ == "__main__":
    monitor_pedal()