#!/usr/bin/env python3
"""
Bluetooth Pedal Service - runs with sudo to access input devices
Sends commands to main application via socket
"""

import evdev
import socket
import time
import sys
from threading import Thread

def find_pedal_device():
    """Find the DBM-20 or other page turner pedal device"""
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    # Common page turner device names - DBM-20 shows up as "Bluetooth Music Pedal"
    pedal_keywords = ['compx', '2.4g', 'dbm', 'donner', 'page turner', 'bluetooth music pedal', 'music pedal', 'receiver']
    
    for device in devices:
        device_name = device.name.lower()
        for keyword in pedal_keywords:
            if keyword in device_name:
                print(f"✅ Found pedal device: {device.name} at {device.path}")
                return device
    
    # If no obvious pedal found, list all keyboard-like devices
    print("❌ No obvious pedal device found. Available input devices:")
    for device in devices:
        capabilities = device.capabilities()
        # Look for devices that can send keyboard events
        if evdev.ecodes.EV_KEY in capabilities:
            print(f"  - {device.name} ({device.path}) - keyboard capable")
        else:
            print(f"  - {device.name} ({device.path})")
    return None

def send_command(command):
    """Send command to main application"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 6789))
        sock.send(command.encode())
        response = sock.recv(1024).decode()
        print(f"📡 Sent: {command} -> {response}")
        sock.close()
    except Exception as e:
        print(f"❌ Failed to send command {command}: {e}")

def pedal_listener():
    """Listen for pedal button presses"""
    device = find_pedal_device()
    if not device:
        print("❌ No pedal device found, exiting...")
        return
    
    print(f"🎵 Listening for pedal input on {device.name}...")
    
    try:
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                if key_event.keystate == evdev.KeyEvent.key_down:
                    keycode = key_event.keycode
                    print(f"🔘 Pedal button pressed: {keycode}")
                    
                    # DBM-20 specific key mappings based on testing:
                    # Left button sends: ^[[A (Up Arrow) = KEY_UP  
                    # Right button sends: ^[[B (Down Arrow) = KEY_DOWN
                    
                    if keycode == 'KEY_UP':
                        send_command('PREV')
                        print(f"⬅️  Previous song (DBM-20 left button: {keycode})")
                    elif keycode == 'KEY_DOWN':
                        send_command('NEXT')
                        print(f"➡️  Next song (DBM-20 right button: {keycode})")
                    elif keycode in ['KEY_LEFT', 'KEY_RIGHT', 'KEY_PAGEUP', 'KEY_PAGEDOWN']:
                        # Fallback for other common page turner keys
                        if keycode in ['KEY_LEFT', 'KEY_PAGEUP']:
                            send_command('PREV')
                            print(f"⬅️  Previous song (fallback: {keycode})")
                        else:
                            send_command('NEXT')
                            print(f"➡️  Next song (fallback: {keycode})")
                    elif keycode in ['KEY_ENTER', 'KEY_ESC', 'KEY_SPACE']:
                        send_command('LIST')
                        print(f"📋 Show list (triggered by {keycode})")
                    else:
                        # Log unknown keys to help with mapping
                        print(f"❓ Unknown key {keycode} - ignoring")
                        print(f"   If this is a pedal button, add it to the mapping above")
                        
    except KeyboardInterrupt:
        print("👋 Pedal service stopped")
    except Exception as e:
        print(f"❌ Error in pedal listener: {e}")

if __name__ == "__main__":
    print("🚀 Starting pedal service...")
    pedal_listener()