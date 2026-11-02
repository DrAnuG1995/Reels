"""Build one vertical text-over-B-roll reel from a JSON spec.

Usage:  python3 scripts/build_reel.py examples/reel_example.json

Spec fields (see examples/reel_example.json):
  out        output mp4 path
  cards      list of {"text": "...", "clip": "path/to/clip.mov", "start": 3.0}
             consecutive cards with the same clip+start play as one continuous shot
  end        ["white line", "accent kicker"]   ending card over the blurred last shot
  music      path to a wav (one track for the whole reel, ending included)
  logo       optional PNG placed top-left (omit for none)
  card_secs  seconds per card (default 2.9)
  end_secs   seconds for the ending (default 4.6)
  accent     hex colour for the kicker (default 0x7CC6BE)
  blur_boxes optional [{"x":0,"y":0,"w":1080,"h":400,"t0":5.0,"t1":6.2}] in final-video coords,
             for faces, names or screens you must hide
"""
import json, os, subprocess, sys, textwrap

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
# HDR iPhone footage (HLG) looks grey and washed out without this tone-map
TONEMAP = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0:peak=4,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")


def probe(p):
    o = json.loads(subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=color_transfer:format=duration', '-of', 'json', p],
        capture_output=True, text=True).stdout)
    return float(o['format']['duration']), o['streams'][0].get('color_transfer', '')


def cut(src, start, length, out):
    """Cover-crop to 1080x1920, tone-map HDR, 30fps, exact length. Stretches short clips up to 2x, then holds the last frame."""
    dur, transfer = probe(src)
    if start is None:
        start = max(0.0, (dur - length) / 2) if dur > length else 0.0
    if start < 0:
        start = max(0.0, dur + start)
    stretch = min(2.0, max(1.0, length / max(0.3, dur - start)))
    hdr = TONEMAP if transfer in ('arib-std-b67', 'smpte2084') else ''
    vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,{hdr}"
          f"setpts={stretch:.3f}*(PTS-STARTPTS),fps=30,tpad=stop_mode=clone:stop_duration={length},"
          f"trim=duration={length},format=yuv420p,eq=saturation=1.08:contrast=1.03")
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{start:.2f}', '-i', src, '-an', '-vf', vf,
                        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '16', out], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'cut failed for {src}:\n{r.stderr[-800:]}')


def esc(t):
    return (t.replace('\\', '\\\\').replace(':', '\\:').replace("'", '’')
             .replace(',', '\\,').replace('%', '\\%'))


def main(spec_path):
    S = json.load(open(spec_path))
    CD, END = S.get('card_secs', 2.9), S.get('end_secs', 4.6)
    accent = S.get('accent', '0x7CC6BE')
    cards = S['cards']
    work = os.path.splitext(S['out'])[0] + '_work'
    os.makedirs(work, exist_ok=True)

    # group consecutive cards on the same shot
    groups = []
    for c in cards:
        key = (c['clip'], c.get('start'))
        if groups and groups[-1][0] == key:
            groups[-1][1] += 1
        else:
            groups.append([key, 1])

    parts = []
    for i, ((clip, start), n) in enumerate(groups):
        length = n * CD + (END if i == len(groups) - 1 else 0)
        out = f'{work}/s{i:02d}.mp4'
        cut(clip, start, length, out)
        parts.append(out)
    open(f'{work}/list.txt', 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{work}/list.txt',
                    '-c', 'copy', f'{work}/base.mp4'], check=True)

    T = len(cards) * CD
    total = T + END
    draw = []
    for i, c in enumerate(cards):
        a, b = i * CD, (i + 1) * CD - 0.02
        lines = textwrap.wrap(c['text'], 20 if len(c['text']) <= 40 else 22)
        fs = 70 if max(len(l) for l in lines) <= 16 else 62
        y0 = 1270 - (len(lines) - 1) * 38
        for j, l in enumerate(lines):
            draw.append(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontsize={fs}:fontcolor=white:"
                        f"borderw=3:bordercolor=black@0.7:box=1:boxcolor=black@0.45:boxborderw=14:"
                        f"x=(w-text_w)/2:y={y0 + j * (fs + 16)}:enable='between(t,{a:.2f},{b:.2f})':"
                        f"alpha='min(1,(t-{a:.2f})/0.15)'")
    white, kicker = S['end']
    w1, w2 = textwrap.wrap(white, 24), textwrap.wrap(kicker, 18)
    y = 820 - len(w1) * 40
    for j, l in enumerate(w1):
        draw.append(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontsize=60:fontcolor=white:x=(w-text_w)/2:"
                    f"y={y + j * 78}:enable='gte(t,{T + 0.3:.2f})':alpha='min(1,max(0,(t-{T + 0.3:.2f})/0.4))'")
    y2 = y + len(w1) * 78 + 40
    for j, l in enumerate(w2):
        draw.append(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontsize=76:fontcolor={accent}:x=(w-text_w)/2:"
                    f"y={y2 + j * 94}:enable='gte(t,{T + 1.3:.2f})':alpha='min(1,max(0,(t-{T + 1.3:.2f})/0.4))'")

    # privacy blur boxes, then ending blur
    fc = '[0:v]null[v0];'
    cur = 'v0'
    for k, bx in enumerate(S.get('blur_boxes', [])):
        fc += (f"[{cur}]split[m{k}][c{k}];[c{k}]crop={bx['w']}:{bx['h']}:{bx['x']}:{bx['y']},gblur=sigma=40[g{k}];"
               f"[m{k}][g{k}]overlay={bx['x']}:{bx['y']}:enable='between(t,{bx['t0']},{bx['t1']})'[b{k}];")
        cur = f'b{k}'
    fc += (f"[{cur}]split[a][b];[b]gblur=sigma=26,eq=brightness=-0.2:saturation=0.6,"
           f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.5:t=fill[bl];[a][bl]overlay=enable='gte(t,{T:.2f})'[m];")
    inputs = ['-i', f'{work}/base.mp4']
    if S.get('logo'):
        inputs += ['-i', S['logo']]
        fc += "[m][1:v]overlay=34:104[m2];"
        music_idx = 2
    else:
        fc += "[m]null[m2];"
        music_idx = 1
    fc += "[m2]" + ",".join(draw) + f",fade=t=out:st={total - 0.5:.2f}:d=0.5[v];"
    fc += (f"[{music_idx}:a]atrim=0:{total:.2f},afade=t=in:d=0.4,afade=t=out:st={total - 1.6:.2f}:d=1.6,"
           f"loudnorm=I=-15:TP=-1.5[au]")
    inputs += ['-i', S['music']]
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', fc, '-map', '[v]', '-map', '[au]',
                        '-t', f'{total:.2f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', S['out']], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-1500:])
    print('built', S['out'], f'{total:.1f}s')


if __name__ == '__main__':
    main(sys.argv[1])
