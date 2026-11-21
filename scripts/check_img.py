from PIL import Image

im = Image.open(r"d:\для one plus nord n10\screenshots\mi10t_screen_after_5000_redirect.png")
print("Size:", im.size)
colors = im.getcolors(maxcolors=1000000)
print("Unique colors count:", len(colors) if colors else "Many")
if colors and len(colors) < 10:
    print("Colors:", colors)
