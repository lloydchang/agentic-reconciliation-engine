#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont
import io

# Create a simple AI-themed favicon
size = 32
img = Image.new('RGBA', (size, size), (25, 118, 210, 255))  # Blue background
draw = ImageDraw.Draw(img)

# Draw a simple AI brain/network icon
center = size // 2

# Draw circle (representing AI/brain)
circle_size = size // 3
draw.ellipse([center - circle_size, center - circle_size, center + circle_size, center + circle_size], 
             fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=1)

# Draw small dots (representing nodes/network)
for i in range(3):
    angle = i * 120  # 120 degrees apart
    x = center + int(circle_size * 1.5 * __import__('math').cos(__import__('math').radians(angle)))
    y = center + int(circle_size * 1.5 * __import__('math').sin(__import__('math').radians(angle)))
    draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255, 255))

# Save as ICO
img.save('agentic-reconciliation-engine/core/operators/dashboard-frontend/public/favicon.ico', 
         format='ICO', sizes=[(16, 16), (32, 32)])

print("✅ AI-themed favicon created!")
