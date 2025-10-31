#!/usr/bin/env python3
"""
Test Donner DBM-20 Bluetooth pedal input detection
This will help us see what the pedal actually sends
"""
import sys
import select
import termios
import tty

def test_pedal_input():
    print("🎸 Donner DBM-20 Pedal Test")
    print("=" * 30)
    print("Press pedal buttons to see what they send...")
    print("Press 'q' to quit")
    print()
    
    # Save terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # Set terminal to raw mode to capture all input
        tty.setraw(sys.stdin.fileno())
        
        while True:
            # Check for input
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                
                # Show what we got
                print(f"Got: {repr(char)} (hex: {ord(char):02x})")
                
                if char == 'q':
                    print("Quitting...")
                    break
                elif char == '\x1b':  # ESC sequence start
                    print("  ESC sequence detected, reading more...")
                    sequence = char
                    
                    # Try to read the full sequence
                    for i in range(3):  # Read up to 3 more chars
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            next_char = sys.stdin.read(1)
                            sequence += next_char
                            print(f"    + {repr(next_char)} (hex: {ord(next_char):02x})")
                        else:
                            break
                    
                    print(f"  Full sequence: {repr(sequence)}")
                    
                    # Check if it matches our expected sequences
                    if sequence == '\x1b[A':
                        print("  🔙 LEFT PEDAL (Previous) - MATCHES!")
                    elif sequence == '\x1b[B':
                        print("  ▶️ RIGHT PEDAL (Next) - MATCHES!")
                    else:
                        print(f"  ❓ Unknown sequence: {sequence}")
                    
                    print()
                    
    except KeyboardInterrupt:
        pass
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_pedal_input()