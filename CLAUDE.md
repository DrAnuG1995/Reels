# Instructions for Claude: text-over-B-roll reels

You are editing short vertical reels (1080x1920, about 22 seconds) for the person who owns this repo.
Every reel is text cards over B-roll, one original music track start to finish, and a blurred ending card.
No talking head, no voiceover, unless the owner asks for one.

## The workflow (follow in order, every time)

1. **Catalogue the footage before choosing anything.**
   Run `python3 scripts/catalogue.py <footage folder> catalogue/`, then Read every `sheetNN.jpg`.
   Fill in `catalogue/catalogue.csv`: a plain description of each clip, `ok` = no if it shows
   anything from the privacy list below. Never pick clips from filenames alone.
2. **Write the cards.** 6 cards per reel, each one sentence, ideally under 40 characters, max about 60.
   Card 1 is the hook. Then a 2-line ending: a white line and a short accent-coloured kicker.
   Only state facts the owner gave you or that come from a source they named.
3. **Match B-roll to the words, card by card.** Each card's clip must show what the card says
   (a card about phone calls shows a phone call; a card about rates shows a rate on screen).
   If nothing in the catalogue fits a card, do NOT use a random pretty shot: add it to a
   "shots to film" list for the owner, with the card it fixes, and build the reel later.
   Don't reuse a clip across reels in the same series. Log usage in the `used_in` column.
4. **Make the music.** One new track per reel: `python3 scripts/music.py music/trackNN.wav --seed NN --mood warm --bpm 92 --key 4`.
   Change seed, mood, bpm and key for every reel so no two sound alike. The same track runs under the ending.
5. **Write the spec and build.** Copy `examples/reel_example.json`, fill in cards, clips, start times,
   ending, music and logo, then `python3 scripts/build_reel.py spec.json`.
6. **Review before sending.** `python3 scripts/check_reel.py out.mp4 check.jpg` and Read the image.
   Check every card: text readable, clip matches words, no privacy problems. Fix and rebuild if not.
7. **Deliver.** Send the mp4s to the owner. Only schedule or post after they approve.

## Privacy rules (non-negotiable)

- No faces except the owner's. Strangers in the background get a `blur_boxes` entry or the clip is dropped.
- No patients, ever, even blurred in the distance. Look for beds, wheelchairs and people in gowns.
- No screens or paper with names, patient details, ECGs, whiteboards or rosters.
- No other users' names or photos in app screen recordings: start the clip after those screens.

## Style rules

- No em dashes or en dashes in any text. Use commas, colons or full stops.
- White DejaVu Sans Bold with a dark band behind it, lower third. Ending: blurred, darkened last shot.
- Keep money talk out of town or hospital reels unless the owner asks for it.

## Gotchas

- iPhone footage is often HDR (HLG). build_reel.py tone-maps it; without that it looks grey.
- Some phone clips are recorded sideways with no rotation flag. Check the contact sheet and skip them.
- Clips shorter than a card are stretched up to 2x, then the last frame is held. Prefer longer clips.
- Big files: cut what you need and delete the originals from the working disk as you go.
