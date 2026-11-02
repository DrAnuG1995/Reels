# reel-kit

Turn phone footage into short vertical reels: text cards over B-roll, an original music track, and a blurred ending card. Built to be run by Claude (Claude Code or Claude Cowork). The rules Claude follows are in `CLAUDE.md`.

## Setup

1. Install ffmpeg (built with zscale/libzimg, which most builds include), Python 3, and `pip install -r requirements.txt`.
2. Make sure DejaVu Sans Bold exists at `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` (`apt install fonts-dejavu-core`, or `brew install --cask font-dejavu` and change `FONT` in `scripts/build_reel.py`).
3. Put your logo as a white PNG about 260px wide at `assets/logo.png` (optional).
4. Put footage in `footage/` (or point the scripts at your Dropbox folder).

## Make a reel

```
python3 scripts/catalogue.py footage catalogue        # contact sheets + catalogue.csv
python3 scripts/music.py music/track01.wav --seed 1 --mood warm
cp examples/reel_example.json specs/reel01.json        # edit cards, clips, ending
python3 scripts/build_reel.py specs/reel01.json
python3 scripts/check_reel.py out/reel01.mp4 out/reel01_check.jpg
```

Or just tell Claude: "Read CLAUDE.md, then make me 5 reels about X from the footage in footage/."
