#!/usr/bin/env python3
import json
import threading
import time
import socket
import os
from PIL import Image, ImageDraw, ImageFont

# Try hardware bindings
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
except Exception:
    RGBMatrix = None
    RGBMatrixOptions = None
    graphics = None

try:
    import serial
except Exception:
    serial = None

try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None

SETLIST_PATH = os.path.join(os.path.dirname(__file__), "setlist.json")
# Use BDF fonts designed for LED matrices instead of TrueType
BDF_FONT_DIR = "/home/tjone/rpi-rgb-led-matrix/fonts/"
LARGE_FONT_FILE = "6x10.bdf"  # Good readability on 2.5mm pitch LED matrix
SMALL_FONT_FILE = "6x10.bdf"  # Same font for consistency

if RGBMatrixOptions is None:
    raise SystemExit("rgbmatrix binding not found in venv; install it before running.")

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.gpio_slowdown = 2
options.hardware_mapping = 'adafruit-hat'
options.brightness = 60  # Brighter for better LED readability

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

setlist = []
idx = 0
lock = threading.Lock()

# Global variables for title scrolling
scroll_offset = 0
last_song_change = time.time()
scroll_start_time = None

BTN_NEXT_PIN = 17
BTN_PREV_PIN = 27

def load_setlist():
    global setlist
    try:
        print("DEBUG: SETLIST_PATH =", SETLIST_PATH)
        with open(SETLIST_PATH, "r", encoding="utf-8") as f:
            data = f.read()
        print(f"DEBUG: setlist.json size={len(data)}")
        if not data.strip():
            raise ValueError("empty setlist.json")
        setlist = json.loads(data)
    except Exception as e:
        print("ERROR loading setlist:", repr(e))
        setlist = [{"title": "(no setlist)", "key": "", "capo": 0}]
        try:
            with open(SETLIST_PATH, "w", encoding="utf-8") as f:
                json.dump(setlist, f, indent=2)
            print("Wrote default setlist to", SETLIST_PATH)
        except Exception as e2:
            print("Failed to write default setlist:", repr(e2))


def _text_size(draw, text, font):
    # Pillow compatibility: prefer textbbox, fall back to textsize or font.getsize
    if hasattr(draw, "textbbox"):
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        return (r - l, b - t)
    if hasattr(draw, "textsize"):
        return draw.textsize(text, font=font)
    try:
        return font.getsize(text)
    except Exception:
        return (len(text) * 6, 10)

def draw_screen():
    global canvas, idx, scroll_offset, last_song_change, scroll_start_time
    with lock:
        song = setlist[idx]
    
    title = song.get("title", "Untitled")
    key = song.get("key", "")
    capo = song.get("capo", 0)
    
    try:
        # Load BDF fonts optimized for LED matrices
        font_large = graphics.Font()
        font_large.LoadFont(BDF_FONT_DIR + LARGE_FONT_FILE)
        
        font_small = graphics.Font()  
        font_small.LoadFont(BDF_FONT_DIR + SMALL_FONT_FILE)
        
        # Create colors
        red = graphics.Color(255, 0, 0)
        orange = graphics.Color(255, 128, 0)
        
    except Exception as e:
        print(f"❌ Font loading failed: {e}")
        return
    
    # Calculate actual title width for scrolling using temporary canvas
    temp_canvas = matrix.CreateFrameCanvas()
    title_width = graphics.DrawText(temp_canvas, font_large, 0, 12, red, title)
    max_title_width = options.cols - 2
    
    current_time = time.time()
    
    # Handle scrolling for long titles
    if title_width > max_title_width:
        # Start scrolling after 2 second delay from when song was last changed
        if scroll_start_time is None:
            if current_time - last_song_change >= 2.0:
                scroll_start_time = current_time
                scroll_offset = 0
        
        if scroll_start_time is not None:
            # Scroll slower - 3 pixels per second for smoother appearance
            scroll_duration = current_time - scroll_start_time
            scroll_offset = int(scroll_duration * 3)
            
            # Reset scroll when we've gone too far
            if scroll_offset > title_width - max_title_width + 20:
                scroll_offset = 0  # Start over
                scroll_start_time = current_time
    else:
        scroll_offset = 0
    
    # Clear canvas for this frame
    canvas.Clear()
    
    # Draw title with BDF font - much cleaner on LED matrix
    title_x = 1 - scroll_offset
    graphics.DrawText(canvas, font_large, title_x, 12, red, title)
    
    # Draw key and capo info - simplified format
    if key or capo:
        # Simple format: "G 3" or "G" or "3"
        parts = []
        if key:
            parts.append(key)
        if capo:
            parts.append(str(capo))
        key_capo_text = " ".join(parts)
        
        graphics.DrawText(canvas, font_small, 1, 25, orange, key_capo_text)
    
    # Use double-buffering to eliminate flashing
    # SwapOnVSync waits for vertical sync before displaying, preventing flicker
    matrix.SwapOnVSync(canvas)
    print(f"📺 Flicker-free Display: '{title}' at ({title_x}, 12)")

def show_current():
    """Display current song"""
    print(f"📺 Showing song {idx + 1}: {setlist[idx]['title']}")
    draw_screen()

def next_song():
    global idx, last_song_change, scroll_offset, scroll_start_time
    with lock:
        idx = (idx + 1) % len(setlist)
    last_song_change = time.time()
    scroll_offset = 0  # Reset scrolling for new song
    scroll_start_time = None
    show_current()

def prev_song():
    global idx, last_song_change, scroll_offset, scroll_start_time
    with lock:
        idx = (idx - 1 + len(setlist)) % len(setlist)
    last_song_change = time.time()
    scroll_offset = 0  # Reset scrolling for new song
    scroll_start_time = None
    show_current()

def goto_song(n):
    global idx, last_song_change, scroll_offset, scroll_start_time
    with lock:
        if 0 <= n < len(setlist):
            idx = n
    last_song_change = time.time()
    scroll_offset = 0  # Reset scrolling for new song
    scroll_start_time = None
    show_current()

def tcp_server(port=6789):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)
    while True:
        conn, addr = srv.accept()
        with conn:
            data = conn.recv(256).decode().strip()
            if not data:
                continue
            handle_command(data)
            conn.sendall(b"OK\n")

def serial_listener(port="/dev/ttyUSB0", baud=115200):
    if serial is None:
        return
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
    except Exception:
        return
    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                handle_command(line)
        except Exception:
            time.sleep(0.1)

def setup_buttons():
    if GPIO is None:
        return
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for p in (BTN_NEXT_PIN, BTN_PREV_PIN):
        try:
            GPIO.remove_event_detect(p)
        except Exception:
            pass
        try:
            GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        except Exception:
            pass
    try:
        GPIO.add_event_detect(BTN_NEXT_PIN, GPIO.FALLING, callback=lambda ch: next_song(), bouncetime=200)
        GPIO.add_event_detect(BTN_PREV_PIN, GPIO.FALLING, callback=lambda ch: prev_song(), bouncetime=200)
        return
    except Exception:
        def _poll_buttons():
            try:
                last_next = GPIO.input(BTN_NEXT_PIN)
                last_prev = GPIO.input(BTN_PREV_PIN)
            except Exception:
                last_next, last_prev = 1, 1
            while True:
                time.sleep(0.06)
                try:
                    cur_next = GPIO.input(BTN_NEXT_PIN)
                    cur_prev = GPIO.input(BTN_PREV_PIN)
                except Exception:
                    continue
                if last_next == 1 and cur_next == 0:
                    next_song()
                if last_prev == 1 and cur_prev == 0:
                    prev_song()
                last_next, last_prev = cur_next, cur_prev
        t = threading.Thread(target=_poll_buttons, daemon=True)
        t.start()

def handle_command(cmd):
    cmd_original = cmd.strip()
    cmd = cmd_original.upper()
    
    # Handle Bluetooth pedal inputs (check original case-sensitive command)
    if "40(" in cmd_original:  # Down/Next button
        next_song()
        return
    elif "38&" in cmd_original:  # Up/Previous button  
        prev_song()
        return
    
    # Handle text commands
    if cmd == "NEXT":
        next_song()
    elif cmd in ("PREV", "BACK"):
        prev_song()
    elif cmd.startswith("GOTO "):
        try:
            n = int(cmd.split()[1])
            goto_song(n)
        except Exception:
            pass
    elif cmd == "LIST":
        for i, s in enumerate(setlist):
            print(i, s.get("title", ""))
    else:
        print("Unknown:", cmd)

def main():
    print("🚀 Starting setlist application...")
    load_setlist()
    print("📋 Setlist loaded")
    setup_buttons()
    print("🔘 Buttons configured")
    show_current()
    print("📺 Initial display should be shown")
    threading.Thread(target=tcp_server, daemon=True).start()
    print("🌐 TCP server started")
    threading.Thread(target=serial_listener, daemon=True).start()
    print("📡 Serial listener started")
    print("✅ Application running - press Ctrl+C to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if GPIO:
            GPIO.cleanup()

if __name__ == "__main__":
    main()
