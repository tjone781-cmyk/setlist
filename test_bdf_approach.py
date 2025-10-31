#!/usr/bin/env python3
"""
Test script to simulate BDF font rendering approach without hardware
"""
import os

# Simulate the graphics module for testing
class MockColor:
    def __init__(self, r, g, b):
        self.r, self.g, self.b = r, g, b
    
    def __str__(self):
        return f"Color({self.r},{self.g},{self.b})"

class MockFont:
    def __init__(self):
        self.loaded_font = None
    
    def LoadFont(self, font_path):
        """Simulate loading a BDF font"""
        if os.path.exists(font_path):
            self.loaded_font = font_path
            print(f"✅ Loaded font: {font_path}")
        else:
            print(f"⚠️  Font file not found: {font_path}")
            # Use default font behavior
            self.loaded_font = "default"

class MockCanvas:
    def __init__(self, width=64, height=32):
        self.width = width
        self.height = height
        self.pixels = {}
    
    def Clear(self):
        self.pixels = {}
        print("Canvas cleared")
    
    def SetPixel(self, x, y, r, g, b):
        self.pixels[(x,y)] = (r, g, b)

class MockMatrix:
    def __init__(self):
        pass
    
    def SwapOnVSync(self, canvas):
        print(f"Display updated - {len(canvas.pixels)} pixels set")

class MockGraphics:
    @staticmethod
    def Color(r, g, b):
        return MockColor(r, g, b)
    
    @staticmethod
    def Font():
        return MockFont()
    
    @staticmethod
    def DrawText(canvas, font, x, y, color, text):
        """Simulate drawing text with BDF font"""
        print(f"📝 DrawText: '{text}' at ({x},{y}) with {color}")
        
        # Simulate pixel setting for text (simple rectangle for testing)
        char_width = 6
        char_height = 10
        
        for i, char in enumerate(text):
            char_x = x + (i * char_width)
            if char_x < canvas.width:
                # Set some pixels to simulate character rendering
                for px in range(min(char_width, canvas.width - char_x)):
                    for py in range(min(char_height, canvas.height - y)):
                        if y + py >= 0:
                            canvas.SetPixel(char_x + px, y + py, color.r, color.g, color.b)

# Test the BDF approach
def test_bdf_font_approach():
    print("🧪 Testing BDF font approach...")
    
    # Mock setup
    graphics = MockGraphics()
    canvas = MockCanvas(64, 32)
    matrix = MockMatrix()
    
    # Font directories to test
    BDF_FONT_DIR = "/home/tjone/rpi-rgb-led-matrix/fonts/"
    LARGE_FONT_FILE = "6x10.bdf"
    
    # Try to load fonts
    try:
        if os.path.exists(os.path.join(BDF_FONT_DIR, LARGE_FONT_FILE)):
            large_font = graphics.Font()
            large_font.LoadFont(os.path.join(BDF_FONT_DIR, LARGE_FONT_FILE))
            print(f"✅ Loaded BDF font: {LARGE_FONT_FILE}")
        else:
            # Use default font
            large_font = graphics.Font()
            print("⚠️  Using default graphics font (BDF files not found)")
            
        small_font = graphics.Font()
        
    except Exception as e:
        print(f"❌ Failed to load fonts: {e}")
        return False
    
    # Test drawing text
    canvas.Clear()
    
    # Create colors
    red_color = graphics.Color(255, 0, 0)
    orange_color = graphics.Color(255, 128, 0)
    
    # Test title
    title = "Amazing Grace"
    graphics.DrawText(canvas, large_font, 1, 10, red_color, title)
    
    # Test key/capo
    key_capo = "G 3"
    graphics.DrawText(canvas, small_font, 1, 24, orange_color, key_capo)
    
    # Display
    matrix.SwapOnVSync(canvas)
    
    print("✅ BDF font approach test completed successfully!")
    return True

if __name__ == "__main__":
    test_bdf_font_approach()