import shutil
import os

src_dir = "challenge_assets"
dst_dir = "frontend/public/test_assets"

os.makedirs(dst_dir, exist_ok=True)
for item in os.listdir(src_dir):
    s = os.path.join(src_dir, item)
    d = os.path.join(dst_dir, item)
    if os.path.isfile(s):
        shutil.copy2(s, d)
        print(f"Copied {item} -> {d}")
