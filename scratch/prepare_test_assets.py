import os
from PIL import Image

assets_dir = 'challenge_assets'
os.makedirs(assets_dir, exist_ok=True)

# 1. banner_good.jpg (already 1280x720, 14.68 KB)
# 2. poster_good.jpg (already 600x900, 9.07 KB)
# 3. thumb_good.jpg (already 640x360, 4.21 KB)
# 4. thumb_tiny.jpg (already 160x90, 0.85 KB)

# Fix banner_too_big.png so its size is genuinely > 200 KB (> 204,800 bytes)
banner_too_big_path = os.path.join(assets_dir, 'banner_too_big.png')
if os.path.exists(banner_too_big_path):
    size_bytes = os.path.getsize(banner_too_big_path)
    if size_bytes < 200 * 1024:
        im = Image.open(banner_too_big_path)
        # Save without compression / with uncompressed metadata to make file size ~250 KB
        # Or save PNG with no compression level
        im.save(banner_too_big_path, format='PNG', compress_level=0)
        # If still < 200KB, append PNG tEXt metadata chunk
        current_size = os.path.getsize(banner_too_big_path)
        if current_size < 200 * 1024:
            needed = (250 * 1024) - current_size
            with open(banner_too_big_path, 'ab') as f:
                f.write(b'\x00' * needed)

# Fix poster_wrong_ratio.jpg if it was invalid text from duplicate link
poster_wrong_path = os.path.join(assets_dir, 'poster_wrong_ratio.jpg')
try:
    im = Image.open(poster_wrong_path)
except Exception:
    # Create 600x600 JPEG (1:1 ratio instead of 2:3) from poster_good.jpg
    poster_good_path = os.path.join(assets_dir, 'poster_good.jpg')
    if os.path.exists(poster_good_path):
        im_good = Image.open(poster_good_path)
        im_square = im_good.crop((0, 0, 600, 600))
        im_square.save(poster_wrong_path, format='JPEG', quality=95)

print("--- Asset Inspection Summary ---")
for f in sorted(os.listdir(assets_dir)):
    p = os.path.join(assets_dir, f)
    try:
        im = Image.open(p)
        w, h = im.size
        size_kb = os.path.getsize(p) / 1024.0
        aspect = w / h
        print(f"{f:22s} | Format: {im.format:4s} | Dimensions: {w:4d}x{h:<4d} | Ratio: {aspect:.3f} | Size: {size_kb:6.2f} KB")
    except Exception as e:
        print(f"{f:22s} | Error: {e}")
