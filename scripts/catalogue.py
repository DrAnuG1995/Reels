"""Make contact sheets of every clip in a folder so Claude can SEE the footage before choosing B-roll.

Usage:  python3 scripts/catalogue.py /path/to/footage out_dir
Writes out_dir/sheet00.jpg ... (12 clips per sheet, 3 frames each) and out_dir/catalogue.csv.
Claude then Reads each sheet image and fills in the 'description' and 'ok' columns of the CSV.
"""
import csv, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
clips = sorted(f for f in os.listdir(src) if f.lower().endswith(('.mov', '.mp4', '.m4v')))
rows, tiles = [], []
for i, name in enumerate(clips):
    p = os.path.join(src, name)
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                             capture_output=True, text=True).stdout.strip() or 0)
    tile = Image.new('RGB', (3 * 182, 350), 'black')
    for j, frac in enumerate((0.15, 0.5, 0.85)):
        tmp = os.path.join(out, '_t.jpg')
        if os.path.exists(tmp):
            os.remove(tmp)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(d * frac), '-i', p, '-frames:v', '1',
                        '-vf', 'scale=180:320', tmp])
        if os.path.exists(tmp):
            tile.paste(Image.open(tmp), (j * 182, 30))
    ImageDraw.Draw(tile).text((4, 4), f'{i}: {name[:34]} ({d:.0f}s)', fill='yellow', font=F)
    tiles.append(tile)
    rows.append({'id': i, 'file': p, 'seconds': round(d, 1), 'description': '', 'ok': '', 'used_in': ''})
for s in range(0, len(tiles), 12):
    sheet = Image.new('RGB', (4 * 550, 3 * 350), 'gray')
    for k, t in enumerate(tiles[s:s + 12]):
        sheet.paste(t, ((k % 4) * 550, (k // 4) * 350))
    sheet.save(os.path.join(out, f'sheet{s // 12:02d}.jpg'), quality=80)
with open(os.path.join(out, 'catalogue.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f'{len(clips)} clips, {len(tiles) // 12 + 1} sheets in {out}')
