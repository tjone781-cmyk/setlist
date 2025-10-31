#!/usr/bin/env python3
"""
Interactive Setlist Test - Manual Control

This script lets you manually test the setlist navigation on the Pi
using keyboard input to simulate the Bluetooth pedal.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/home/tjone/setlist_app')

def interactive_test():
    print("🎵 Interactive Setlist Test")
    print("=" * 50)
    
    try:
        import main
        
        # Load the setlist
        main.load_setlist()
        print(f"✅ Loaded {len(main.setlist)} songs")
        
        # Show initial display
        print("\n📺 Initial Display:")
        main.show_current()
        
        print("\n🎮 Controls:")
        print("  n = Next song (simulates Bluetooth pedal 40()")
        print("  p = Previous song (simulates Bluetooth pedal 38&)")
        print("  l = List all songs")
        print("  s = Show current song info")
        print("  1-8 = Jump to specific song")
        print("  q = Quit")
        
        while True:
            try:
                print(f"\n🎵 Currently showing: {main.setlist[main.idx]['title']} (Song {main.idx + 1}/{len(main.setlist)})")
                cmd = input("Enter command: ").strip().lower()
                
                if cmd == 'q':
                    print("👋 Goodbye!")
                    break
                elif cmd == 'n':
                    print("⏭️  Simulating Bluetooth pedal NEXT (40()...")
                    main.handle_command("test 40( pedal")
                elif cmd == 'p':
                    print("⏮️  Simulating Bluetooth pedal PREVIOUS (38&)...")
                    main.handle_command("38& pedal test")
                elif cmd == 'l':
                    print("\n📋 All Songs:")
                    for i, song in enumerate(main.setlist):
                        marker = "►" if i == main.idx else " "
                        title = song.get("title", "Untitled")
                        key = song.get("key", "")
                        capo = song.get("capo", 0)
                        key_info = f" ({key}" + (f" C{capo}" if capo else "") + ")" if key or capo else ""
                        print(f"  {marker} {i+1}. {title}{key_info}")
                elif cmd == 's':
                    song = main.setlist[main.idx]
                    print(f"\n📄 Current Song Details:")
                    print(f"  Title: {song.get('title', 'Untitled')}")
                    print(f"  Key: {song.get('key', 'Not specified')}")
                    print(f"  Capo: {song.get('capo', 0) if song.get('capo', 0) else 'None'}")
                elif cmd.isdigit() and 1 <= int(cmd) <= len(main.setlist):
                    song_num = int(cmd)
                    print(f"🎯 Jumping to song {song_num}...")
                    main.goto_song(song_num - 1)
                else:
                    print("❓ Unknown command. Use n/p/l/s/q or song number 1-8")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except ImportError as e:
        print(f"❌ Cannot import main module: {e}")
        print("Make sure you're running this from the setlist_app directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    interactive_test()