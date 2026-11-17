"""How It Ticks LONG video (owner 2026-11-16: a long video every 2 days).
Joins the newest 3-4 new-system shorts (not deleted, approved first) into one 16:9 explainer:
branded intro card, then each machine as a chapter (sharp vertical video in the middle, soft blurred copy behind,
chapter title on the left, logo on the right). Writes long.mp4 + long.json {title, tags}. Nothing is posted here."""
import json, random, subprocess, sys, textwrap, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

B = Path(__file__).resolve().parent
START = 'ce-20261116-2300'   # first tested-component shorts; older looks are never reused
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BG, C, D, O = (30, 80, 106), (246, 240, 222), (24, 62, 84), (221, 102, 57)
MACHINES = {'solar': ('solar', 'sunlight', 'photovoltaic'), 'wind': ('wind', 'turbine'), 'pump': ('pump', 'piston'), 'bridge': ('bridge',)}
TITLES = ['How {n} Everyday Machines Really Work 🔧', 'How {n} Clever Machines Do Their Jobs 🔧', 'How Machines Work From the Inside 🔧']

def run(*a): subprocess.run(a, check=True)

def pick(n=4):
    vids = json.loads((B / 'data/scenes/videos.json').read_text())
    try: idx = {i['tag']: i.get('folder') for i in json.loads((B / 'data/scenes/review/index.json').read_text()).get('items', [])}
    except Exception: idx = {}
    used = set()
    try: used = set(json.loads((B / 'data/scenes/long-used.json').read_text()))
    except Exception: pass
    pool = [v for v in vids if v.get('tag', '') >= START and v.get('kind') != 'long' and idx.get(v['tag']) != 'delete']
    pool.sort(key=lambda v: (idx.get(v['tag']) != 'saved', v['tag'] in used, -int(''.join(c for c in v['tag'] if c.isdigit())[:12] or 0)))
    out, seen = [], set()
    for v in pool:
        t = v['title'].lower()
        key = next((m for m, ws in MACHINES.items() if any(x in t for x in ws)), t[:28])   # one chapter per machine
        if key in seen: continue
        seen.add(key); out.append(v)
        if len(out) == n: break
    return out

def logo(d, cx, cy, s):
    pts = []
    import math
    for i in range(48):
        a = i / 48 * 2 * math.pi - math.pi / 2 + math.pi / 48; rr = 520 * s * (1.0 if i % 4 in (1, 2) else .84)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=C); d.ellipse((cx - 360 * s, cy - 360 * s, cx + 360 * s, cy + 360 * s), fill=D); d.ellipse((cx - 330 * s, cy - 330 * s, cx + 330 * s, cy + 330 * s), fill=C)
    for k in range(12):
        a = k / 12 * 2 * math.pi; r1 = (225 if k % 3 == 0 else 255) * s
        d.line((cx + r1 * math.sin(a), cy - r1 * math.cos(a), cx + 305 * s * math.sin(a), cy - 305 * s * math.cos(a)), fill=D, width=max(2, int((26 if k % 3 == 0 else 14) * s)))
    for ang, l, w, col in ((300, 165, 46, D), (60, 240, 30, O)):
        a = math.radians(ang); d.line((cx, cy, cx + l * s * math.sin(a), cy - l * s * math.cos(a)), fill=col, width=max(3, int(w * s)))
    d.ellipse((cx - 42 * s, cy - 42 * s, cx + 42 * s, cy + 42 * s), fill=O)

def strip_emoji(t): return ''.join(ch for ch in t if ord(ch) < 0x2190).strip()

def card(path, title, n):
    im = Image.new('RGB', (1920, 1080), BG); d = ImageDraw.Draw(im)
    logo(d, 960, 380, .42)
    f = ImageFont.truetype(BOLD, 76); g = ImageFont.truetype(REG, 40)
    t = strip_emoji(title); w = d.textlength(t, font=f); d.text(((1920 - w) / 2, 660), t, font=f, fill=C)
    s = '%d machines, opened up and explained' % n; w = d.textlength(s, font=g); d.text(((1920 - w) / 2, 770), s, font=g, fill=O)
    im.save(path)

def panel(path, k, n, title):
    im = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 656, 1080), fill=BG + (235,)); d.rectangle((1264, 0, 1920, 1080), fill=BG + (235,))
    f = ImageFont.truetype(REG, 34); g = ImageFont.truetype(BOLD, 54)
    d.text((70, 360), 'PART %d OF %d' % (k, n), font=f, fill=O)
    for j, line in enumerate(textwrap.wrap(strip_emoji(title), 17)[:5]): d.text((70, 420 + j * 70), line, font=g, fill=C)
    logo(d, 1592, 470, .26)
    h = ImageFont.truetype(BOLD, 46); w = d.textlength('How It Ticks', font=h); d.text((1592 - w / 2, 640), 'How It Ticks', font=h, fill=C)
    im.save(path)

def main(out='long.mp4'):
    clips = pick()
    if len(clips) < 3: print('not enough new-style shorts yet (%d); no long video' % len(clips)); return 1
    n = len(clips); k = len(json.loads((B / 'data/scenes/long-used.json').read_text())) if (B / 'data/scenes/long-used.json').exists() else 0
    title = TITLES[(datetime.date.today().toordinal() // 2) % len(TITLES)].format(n=n)
    w = Path('long-work'); w.mkdir(exist_ok=True); parts = []
    card(w / 'intro.png', title, n)
    run('ffmpeg', '-v', 'error', '-y', '-loop', '1', '-t', '4', '-i', str(w / 'intro.png'), '-f', 'lavfi', '-t', '4', '-i', 'anullsrc=r=44100:cl=stereo',
        '-vf', 'fps=30,format=yuv420p,fade=in:0:15,fade=out:105:15', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'aac', '-shortest', str(w / 'p0.mp4'))
    parts.append(w / 'p0.mp4')
    for i, v in enumerate(clips, 1):
        src = w / ('s%d.mp4' % i)
        run('gh', 'release', 'download', v['tag'], '-p', '*.mp4', '-O', str(src), '--clobber')
        panel(w / ('o%d.png' % i), i, n, v['title'])
        fc = ('[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=30:4,eq=brightness=-0.12[bg];'
              '[0:v]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0[v1];[v1][1:v]overlay=0:0,fps=30,format=yuv420p[v]')
        run('ffmpeg', '-v', 'error', '-y', '-i', str(src), '-i', str(w / ('o%d.png' % i)), '-filter_complex', fc, '-map', '[v]', '-map', '0:a?',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'aac', '-ar', '44100', '-ac', '2', str(w / ('p%d.mp4' % i)))
        parts.append(w / ('p%d.mp4' % i))
    (w / 'list.txt').write_text(''.join("file '%s'\n" % p.resolve() for p in parts))
    run('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(w / 'list.txt'), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-c:a', 'aac', '-movflags', '+faststart', out)
    Path('long.json').write_text(json.dumps({'title': title, 'tags': [v['tag'] for v in clips], 'titles': [v['title'] for v in clips]}, ensure_ascii=False, indent=1))
    p = B / 'data/scenes/long-used.json'
    try: used = json.loads(p.read_text())
    except Exception: used = []
    p.write_text(json.dumps((used + [v['tag'] for v in clips])[-60:], indent=1) + '\n')
    print('long video:', title, [v['tag'] for v in clips]); return 0

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
