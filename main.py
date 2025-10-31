#!/usr/bin/env python3
import json
import threading
import time
import socket
import os
from PIL import Image, ImageDraw, ImageFont

# Try hardware bindings
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except Exception:
    RGBMatrix = None
    RGBMatrixOptions = None

try:
    import serial
except Exception:
    serial = None

try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None

SETLIST_PATH = os.path.join(os.path.dirname(__file__), "setlist.json")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LARGE_FONT_SIZE = 10  # Reduced from 12 for better fit
SMALL_FONT_SIZE = 8   # Reduced from 10 for better fit

if RGBMatrixOptions is None:
    raise SystemExit("rgbmatrix binding not found in venv; install it before running.")

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.gpio_slowdown = 2
options.hardware_mapping = 'adafruit-hat'
options.brightness = 40

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

setlist = []
idx = 0
lock = threading.Lock()

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
    global canvas, idx
    with lock:
        song = setlist[idx]
        next_song = setlist[(idx + 1) % len(setlist)]
    img = Image.new("RGB", (options.cols, options.rows))
    draw = ImageDraw.Draw(img)
    try:
        f_large = ImageFont.truetype(FONT_PATH, LARGE_FONT_SIZE)
        f_small = ImageFont.truetype(FONT_PATH, SMALL_FONT_SIZE)
    except Exception:
        f_large = ImageFont.load_default()
        f_small = ImageFont.load_default()
    title = song.get("title", "Untitled")
    # Draw title in bright red for main focus
    draw.text((1, 0), title, font=f_large, fill=(255,0,0))
    keycap = song.get("key", "")
    capo = song.get("capo", None)
    if capo:
        keycap = f"{keycap}  C{capo}" if keycap else f"C{capo}"
    w, h = _text_size(draw, keycap, f_small)
    # Draw key/capo info in orange-red for secondary info
    draw.text((options.cols - w - 1, 0), keycap, font=f_small, fill=(255,64,0))
    nexttext = f"NEXT: {next_song.get('title','')}"
    # Draw next song in dim red for preview
    draw.text((1, 16), nexttext, font=f_small, fill=(128,0,0))

    # Ensure a compatible Pillow Image object for rgbmatrix bindings
    try:
        img = img.convert("RGB")
    except Exception:
        pass

    # Handle Pillow 11+ compatibility issue - use pixel-by-pixel copy
    # The new Pillow version removed the internal API that rgbmatrix uses
    print("Using Pillow 11+ compatible pixel-by-pixel method")
    try:
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = img.getpixel((x, y))
                canvas.SetPixel(x, y, r, g, b)
        print("✅ Display updated successfully")
    except Exception as e:
        print(f"❌ Pixel-by-pixel method failed: {repr(e)}")
        return

    matrix.SwapOnVSync(canvas)

def show_current():
    draw_screen()

def next_song():
    global idx
    with lock:
        idx = (idx + 1) % len(setlist)
    show_current()

def prev_song():
    global idx
    with lock:
        idx = (idx - 1 + len(setlist)) % len(setlist)
    show_current()

def goto_song(n):
    global idx
    with lock:
        if 0 <= n < len(setlist):
            idx = n
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
    load_setlist()
    setup_buttons()
    show_current()
    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=serial_listener, daemon=True).start()
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
