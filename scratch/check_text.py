import re, os

with open('challenge_text.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

urls = re.findall(r'https?://[^\s"\'\>]+', text)
print('URLs in challenge_text.txt:', urls)

for fn in ['banner_good.jpg', 'banner_too_big.png', 'poster_good.jpg', 'poster_wrong_ratio.jpg', 'thumb_good.jpg', 'thumb_tiny.jpg']:
    print(fn, 'in text:', fn in text)
