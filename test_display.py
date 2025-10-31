#!/usr/bin/env python3
"""
Simple setlist display test - no GPIO buttons, just matrix display and TCP
"""

import json
import threading
import socket
import time
import sys
import os
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Matrix configuration
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'
options.brightness = 60

# Colors
RED = graphics.Color(255, 0, 0)
GREEN = graphics.Color(0, 255, 0)
BLUE = graphics.Color(0, 0, 255)
WHITE = graphics.Color(255, 255, 255)
YELLOW = graphics.Color(255, 255, 0)

# Global variables
matrix = None
canvas = None
setlist = []
idx = 0
font = None

def load_setlist():
    global setlist
    try:
        with open('/home/tjone/setlist_app/setlist.json', 'r') as f:
            setlist = json.load(f)
        print(f"✅ Loaded {len(setlist)} songs")
    except Exception as e:
        print(f"❌ Error loading setlist: {e}")
        # Default setlist for testing
        setlist = [
            {"title": "Wonderwall", "key": "G", "capo": "2"},
            {"title": "Sweet Child O' Mine", "key": "D", "capo": "0"},
            {"title": "Stairway to Heaven", "key": "Am", "capo": "0"}
        ]

def setup_matrix():
    global matrix, canvas, font
    try:
        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()
        
        # Load BDF font - try multiple options
        font_paths = [
            '/home/tjone/rpi-rgb-led-matrix/fonts/6x9.bdf',
            '/home/tjone/rpi-rgb-led-matrix/fonts/5x8.bdf',
            '/home/tjone/rpi-rgb-led-matrix/fonts/tom-thumb.bdf'
        ]
        
        font = graphics.Font()
        for font_path in font_paths:
            if os.path.exists(font_path):
                font.LoadFont(font_path)
                print(f"✅ Loaded BDF font: {font_path}")
                break
        else:
            print(f"❌ No fonts found in: {font_paths}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Matrix setup failed: {e}")
        return False

def draw_screen():
    global canvas, setlist, idx, font
    if not matrix or not font:
        return
    
    canvas.Clear()
    
    if not setlist:
        graphics.DrawText(canvas, font, 2, 10, WHITE, "No songs")
        matrix.SwapOnVSync(canvas)
        return
    
    song = setlist[idx]
    title = song["title"]
    key = song["key"]
    capo = song["capo"]
    
    # Display format
    key_capo_text = f"{key} {capo}" if capo != "0" else key
    
    # Title on top (with scrolling if needed)
    title_width = len(title) * 6  # Approximate width with 6x10 font
    
    if title_width <= 62:  # Fits on screen
        graphics.DrawText(canvas, font, 2, 10, WHITE, title)
    else:
        # Simple scrolling - just show first part for testing
        graphics.DrawText(canvas, font, 2, 10, WHITE, title[:10] + "...")
    
    # Key/Capo on bottom
    graphics.DrawText(canvas, font, 2, 25, YELLOW, key_capo_text)
    
    # Song counter
    counter = f"{idx + 1}/{len(setlist)}"
    graphics.DrawText(canvas, font, 64 - len(counter) * 6, 25, GREEN, counter)
    
    matrix.SwapOnVSync(canvas)
    print(f"🎵 Displaying: {title} | {key_capo_text} | ({counter})")

def tcp_server():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 6789))
        server.listen(5)
        print("🌐 TCP server listening on port 6789")
        
        while True:
            client, addr = server.accept()
            try:
                data = client.recv(1024).decode().strip()
                print(f"📡 Received: {data}")
                
                global idx
                if data == "NEXT":
                    idx = (idx + 1) % len(setlist)
                    draw_screen()
                    client.send(b"OK\n")
                elif data == "PREV":
                    idx = (idx - 1) % len(setlist)
                    draw_screen()
                    client.send(b"OK\n")
                elif data == "LIST":
                    response = f"{len(setlist)} songs loaded\n"
                    client.send(response.encode())
                else:
                    client.send(b"UNKNOWN\n")
                    
            except Exception as e:
                print(f"❌ TCP error: {e}")
            finally:
                client.close()
                
    except Exception as e:
        print(f"❌ TCP server error: {e}")

def main():
    print("🎸 Setlist Display Test")
    print("=======================")
    
    load_setlist()
    
    if not setup_matrix():
        print("❌ Matrix setup failed!")
        return
    
    # Initial display
    draw_screen()
    
    # Start TCP server
    threading.Thread(target=tcp_server, daemon=True).start()
    
    print("✅ Display test ready!")
    print("📡 TCP commands: NEXT, PREV, LIST")
    print("🎯 Try: echo 'NEXT' | nc 192.168.1.206 6789")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()