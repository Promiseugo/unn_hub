"""
Run this script from your project root (unn_hub/) once to generate
a tight-cropped favicon from your logo:
  python make_favicon.py
"""
from PIL import Image
import numpy as np, os, sys

src = 'static/images/ux_logo.png'
if not os.path.exists(src):
    sys.exit(f"Not found: {src}")

img = Image.open(src).convert('RGBA')
w, h = img.size
data = np.array(img)

# Find pixels that are NOT near-black (the actual logo mark)
r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
bright = (r.astype(int) + g.astype(int) + b.astype(int)) > 100
visible = bright & (a > 50)

rows = np.any(visible, axis=1)
cols = np.any(visible, axis=0)

if not np.any(rows):
    sys.exit("Could not detect logo mark — image may be all dark")

rmin, rmax = np.where(rows)[0][[0, -1]]
cmin, cmax = np.where(cols)[0][[0, -1]]

# Add padding
pad = int(min(w, h) * 0.06)
rmin = max(0, rmin - pad)
rmax = min(h, rmax + pad)
cmin = max(0, cmin - pad)
cmax = min(w, cmax + pad)

cropped = img.crop((cmin, rmin, cmax, rmax))
print(f"Original: {w}x{h}  →  Cropped: {cropped.width}x{cropped.height}")

# Save tight PNG for favicon use
out_png = 'static/images/ux_favicon.png'
cropped.resize((256, 256), Image.LANCZOS).save(out_png)
print(f"Saved: {out_png}")

# Also save 32x32 and 16x16 versions
cropped.resize((32, 32), Image.LANCZOS).save('static/images/ux_favicon_32.png')
cropped.resize((16, 16), Image.LANCZOS).save('static/images/ux_favicon_16.png')
print("Saved: ux_favicon_32.png, ux_favicon_16.png")
print("Done — update base.html to use ux_favicon.png as the favicon.")
