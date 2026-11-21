from PIL import Image

im = Image.open(r"d:\для one plus nord n10\screenshots\mi10t_screen_after_5000_redirect.png")
# Let's inspect some sample pixels across the screen
w, h = im.size
print("Top-left (status bar):", im.getpixel((50, 50)))
print("Center (content):", im.getpixel((w // 2, h // 2)))
print("Bottom (buttons/input):", im.getpixel((w // 2, h - 200)))
print("Accent search:", [p for p in [im.getpixel((x, y)) for x in range(100, w, 100) for y in range(100, h, 100)] if p[0] != p[1] or p[0] > 50][:5])
