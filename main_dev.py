#!/usr/bin/env python3
"""
Setlist Display Application - Development Version

This version works without the RGB matrix hardware for local development.
It simulates the matrix display in the console and adds keyboard input
to simulate the Bluetooth pedal.
"""
import json
import threading
import time
import socket
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Development mode flag - set to True when running without hardware
DEVELOPMENT_MODE = True

# Try hardware bindings
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    if not DEVELOPMENT_MODE:
        print("✅ RGB Matrix hardware detected")
except ImportError:
    RGBMatrix = None
    RGBMatrixOptions = None
    print("ℹ️  RGB Matrix not available - using development mode")

try:
    import serial
    print("✅ Serial communication available")
except ImportError:
    serial = None
    print("ℹ️  Serial not available")

try:
    import RPi.GPIO as GPIO
    if not DEVELOPMENT_MODE:
        print("✅ GPIO hardware detected")
except ImportError:
    GPIO = None
    print("ℹ️  GPIO not available - using keyboard input")

# Configuration
SETLIST_PATH = os.path.join(os.path.dirname(__file__), "setlist.json")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LARGE_FONT_SIZE = 12
SMALL_FONT_SIZE = 10

# Matrix configuration
MATRIX_WIDTH = 64
MATRIX_HEIGHT = 32

# Global variables
setlist = []
idx = 0
lock = threading.Lock()

# Development mode display
class DevelopmentDisplay:
    """Simulates the RGB matrix display in the console"""
    
    def __init__(self):
        self.width = MATRIX_WIDTH
        self.height = MATRIX_HEIGHT
        
    def show_screen(self, title, key, capo, next_title):
        """Display the current screen in console format"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Create display frame
        print("┌" + "─" * (self.width - 2) + "┐")
        
        # Title line
        title_line = f" {title}"
        key_info = f"{key} C{capo}" if capo else key
        key_line = f"{key_info:>10}"
        
        # Pad title line and add key info
        title_display = title_line[:self.width - len(key_line) - 4] + key_line
        title_display = title_display.ljust(self.width - 2)
        print(f"│{title_display}│")
        
        # Separator
        print("│" + "─" * (self.width - 2) + "│")
        
        # Next song line
        next_line = f" NEXT: {next_title}"
        next_display = next_line[:self.width - 2].ljust(self.width - 2)
        print(f"│{next_display}│")
        
        # Empty lines
        for _ in range(self.height - 6):
            print("│" + " " * (self.width - 2) + "│")
            
        print("└" + "─" * (self.width - 2) + "┘")
        
        # Control info
        print("\n📱 Controls:")
        print("  [↓] or [n] - Next song")
        print("  [↑] or [p] - Previous song") 
        print("  [q] - Quit")
        print("  [l] - List all songs")
        print(f"\n🎵 Song {idx + 1} of {len(setlist)}")

# Initialize display
if DEVELOPMENT_MODE or RGBMatrix is None:
    display = DevelopmentDisplay()
    matrix = None
    canvas = None
    options = None
else:
    # Hardware initialization
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
    display = None

# Button pins for hardware
BTN_NEXT_PIN = 17
BTN_PREV_PIN = 27

def load_setlist():
    global setlist
    try:
        print(f"📁 Loading setlist from: {SETLIST_PATH}")
        with open(SETLIST_PATH, "r", encoding="utf-8") as f:
            data = f.read()
        print(f"📄 Setlist file size: {len(data)} bytes")
        if not data.strip():
            raise ValueError("empty setlist.json")
        setlist = json.loads(data)
        print(f"🎵 Loaded {len(setlist)} songs")
    except Exception as e:
        print(f"❌ ERROR loading setlist: {repr(e)}")
        setlist = [{"title": "(no setlist)", "key": "", "capo": 0}]
        try:
            with open(SETLIST_PATH, "w", encoding="utf-8") as f:
                json.dump(setlist, f, indent=2)
            print(f"💾 Wrote default setlist to {SETLIST_PATH}")
        except Exception as e2:
            print(f"❌ Failed to write default setlist: {repr(e2)}")

def _text_size(draw, text, font):
    """Get text dimensions - compatible with different Pillow versions"""
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
    """Draw the current screen - hardware or development mode"""
    global canvas, idx
    
    with lock:
        song = setlist[idx]
        next_song = setlist[(idx + 1) % len(setlist)]
    
    title = song.get("title", "Untitled")
    key = song.get("key", "")
    capo = song.get("capo", 0)
    next_title = next_song.get("title", "")
    
    if DEVELOPMENT_MODE or display:
        # Development mode - console display
        display.show_screen(title, key, capo, next_title)
    else:
        # Hardware mode - RGB matrix
        img = Image.new("RGB", (options.cols, options.rows))
        draw = ImageDraw.Draw(img)
        
        try:
            f_large = ImageFont.truetype(FONT_PATH, LARGE_FONT_SIZE)
            f_small = ImageFont.truetype(FONT_PATH, SMALL_FONT_SIZE)
        except Exception:
            f_large = ImageFont.load_default()
            f_small = ImageFont.load_default()
            
        # Draw title
        draw.text((1, 0), title, font=f_large, fill=(255,255,255))
        
        # Draw key and capo info
        keycap = f"{key} C{capo}" if capo and key else key if key else f"C{capo}" if capo else ""
        if keycap:
            w, h = _text_size(draw, keycap, f_small)
            draw.text((options.cols - w - 1, 0), keycap, font=f_small, fill=(255,255,255))
        
        # Draw next song
        nexttext = f"NEXT: {next_title}"
        draw.text((1, 16), nexttext, font=f_small, fill=(200,200,200))
        
        # Send to matrix
        try:
            img = img.convert("RGB")
            canvas.SetImage(img, 0, 0)
            matrix.SwapOnVSync(canvas)
        except Exception as e:
            print(f"❌ Matrix display error: {repr(e)}")

def show_current():
    """Display current song"""
    draw_screen()

def next_song():
    """Go to next song"""
    global idx
    with lock:
        idx = (idx + 1) % len(setlist)
    print(f"⏭️  Next song")
    show_current()

def prev_song():
    """Go to previous song"""
    global idx
    with lock:
        idx = (idx - 1 + len(setlist)) % len(setlist)
    print(f"⏮️  Previous song")
    show_current()

def goto_song(n):
    """Go to specific song by index"""
    global idx
    with lock:
        if 0 <= n < len(setlist):
            idx = n
    print(f"🎯 Going to song {n + 1}")
    show_current()

def list_songs():
    """List all songs in setlist"""
    print("\n🎵 Current Setlist:")
    print("─" * 50)
    for i, song in enumerate(setlist):
        marker = "►" if i == idx else " "
        title = song.get("title", "Untitled")
        key = song.get("key", "")
        capo = song.get("capo", 0)
        key_info = f" ({key}" + (f" C{capo}" if capo else "") + ")" if key or capo else ""
        print(f"{marker} {i+1:2d}. {title}{key_info}")
    print("─" * 50)

def keyboard_listener():
    """Listen for keyboard input in development mode"""
    if not DEVELOPMENT_MODE:
        return
        
    print("⌨️  Keyboard listener started")
    print("   Use [n/↓] for next, [p/↑] for previous, [l] for list, [q] to quit")
    
    try:
        import termios
        import tty
        
        def get_char():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
        while True:
            char = get_char().lower()
            if char == 'q':
                print("\n👋 Goodbye!")
                os._exit(0)
            elif char in ['n', '\x1b[B']:  # n or down arrow
                handle_command("NEXT")
            elif char in ['p', '\x1b[A']:  # p or up arrow  
                handle_command("PREV")
            elif char == 'l':
                list_songs()
            elif char.isdigit():
                goto_song(int(char) - 1)
                
    except ImportError:
        # Fallback for Windows or if termios not available
        print("⌨️  Using simple input mode (press Enter after each command)")
        while True:
            try:
                cmd = input().strip().lower()
                if cmd in ['q', 'quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                elif cmd in ['n', 'next']:
                    handle_command("NEXT")
                elif cmd in ['p', 'prev', 'previous']:
                    handle_command("PREV") 
                elif cmd in ['l', 'list']:
                    list_songs()
                elif cmd.isdigit():
                    goto_song(int(cmd) - 1)
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

def tcp_server(port=6789):
    """TCP server for remote commands"""
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", port))
        srv.listen(1)
        print(f"🌐 TCP server listening on port {port}")
        
        while True:
            conn, addr = srv.accept()
            with conn:
                data = conn.recv(256).decode().strip()
                if not data:
                    continue
                print(f"📡 TCP command from {addr}: {data}")
                handle_command(data)
                conn.sendall(b"OK\n")
    except Exception as e:
        print(f"❌ TCP server error: {e}")

def serial_listener(port="/dev/ttyUSB0", baud=115200):
    """Listen for serial commands"""
    if serial is None:
        return
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print(f"📻 Serial listener on {port}")
        while True:
            try:
                line = ser.readline().decode().strip()
                if line:
                    print(f"📻 Serial command: {line}")
                    handle_command(line)
            except Exception:
                time.sleep(0.1)
    except Exception as e:
        print(f"❌ Serial listener error: {e}")

def setup_buttons():
    """Set up physical buttons if GPIO available"""
    if GPIO is None or DEVELOPMENT_MODE:
        return
        
    print("🔘 Setting up physical buttons")
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
        print("✅ Button events configured")
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
        print("✅ Button polling started")

def handle_command(cmd):
    """Handle commands from various sources"""
    cmd = cmd.strip().upper()
    
    # Handle Bluetooth pedal inputs
    if "40(" in cmd:  # Down/Next button
        next_song()
        return
    elif "38&" in cmd:  # Up/Previous button  
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
            goto_song(n - 1)  # Convert to 0-based index
        except Exception:
            print(f"❌ Invalid goto command: {cmd}")
    elif cmd == "LIST":
        list_songs()
    else:
        print(f"❓ Unknown command: {cmd}")

def main():
    """Main application entry point"""
    print("🎵 Setlist Display Application")
    print("=" * 50)
    
    # Load data
    load_setlist()
    
    # Set up hardware if available
    setup_buttons()
    
    # Show initial screen
    show_current()
    
    # Start network services
    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=serial_listener, daemon=True).start()
    
    # Start keyboard input in development mode
    if DEVELOPMENT_MODE:
        threading.Thread(target=keyboard_listener, daemon=True).start()
    
    try:
        print("\n🚀 Application started!")
        print("   Press Ctrl+C to exit")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        if GPIO and not DEVELOPMENT_MODE:
            GPIO.cleanup()
        print("👋 Application stopped")

if __name__ == "__main__":
    main()