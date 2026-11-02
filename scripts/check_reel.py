"""Grab one frame per card (plus the ending) so Claude can review a finished reel before sending it.

Usage:  python3 scripts/check_reel.py reel.mp4 check.jpg [card_secs] [n_cards]
"""
import subprocess, sys
from PIL import Image

f, out = sys.argv[1], sys.argv[2]
cd = float(sys.argv[3]) if len(sys.argv) > 3 else 2.9
n = int(sys.argv[4]) if len(sys.argv) > 4 else 6
times = [cd * i + cd / 2 for i in range(n)] + [cd * n + 3]
W, H = 200, 356
sheet = Image.new('RGB', (len(times) * W, H), 'black')
for i, t in enumerate(times):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', f, '-frames:v', '1', '-vf', f'scale={W}:{H}', '/tmp/_c.jpg'])
    sheet.paste(Image.open('/tmp/_c.jpg'), (i * W, 0))
sheet.save(out, quality=85)
print('wrote', out)
