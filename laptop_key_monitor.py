#!/usr/bin/env python3
"""
Local key monitor for testing DBM-20 on laptop
No need for evdev - just uses keyboard events
"""

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

import sys

def monitor_with_pynput():
    """Monitor using pynput (works on most systems)"""
    print("🎵 DBM-20 Key Monitor (pynput)")
    print("   Pair your DBM-20 pedal via Bluetooth, then press the buttons")
    print("   Press Ctrl+C to stop")
    
    def on_press(key):
        try:
            print(f"🔘 Key pressed: {key.char} (char)")
        except AttributeError:
            print(f"🔘 Special key pressed: {key}")
    
    def on_release(key):
        if key == keyboard.Key.esc:
            return False
    
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\n👋 Done monitoring")

def monitor_with_input():
    """Fallback: simple input monitoring"""
    print("🎵 DBM-20 Key Monitor (simple)")
    print("   Pair your DBM-20 pedal via Bluetooth")
    print("   Focus this terminal and press pedal buttons")
    print("   Type 'quit' to exit")
    
    while True:
        try:
            line = input("Waiting for pedal input (or type 'quit'): ")
            if line.lower() == 'quit':
                break
            if line:
                print(f"📝 Received: '{line}'")
        except KeyboardInterrupt:
            print("\n👋 Done monitoring")
            break

if __name__ == "__main__":
    print("Testing DBM-20 Bluetooth page turner pedal...")
    
    if PYNPUT_AVAILABLE:
        try:
            monitor_with_pynput()
        except Exception as e:
            print(f"pynput failed: {e}")
            print("Falling back to simple input monitoring...")
            monitor_with_input()
    else:
        print("pynput not available, using simple monitoring")
        print("Install with: pip install pynput")
        monitor_with_input()