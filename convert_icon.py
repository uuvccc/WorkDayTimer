from wand.image import Image
from PIL import Image as PILImage
import os

# Convert SVG to PNG
svg_path = os.path.join('images', 'icon.svg')
png_path = os.path.join('images', 'icon.png')
ico_path = os.path.join('images', 'icon.ico')

# Convert SVG to PNG using wand
with Image(filename=svg_path) as img:
    img.resize(256, 256)
    img.save(filename=png_path)

# Convert PNG to ICO
img = PILImage.open(png_path)
img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

print('Icon files created successfully!')