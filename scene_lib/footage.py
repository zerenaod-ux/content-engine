"""REAL_FOOTAGE (owner 2026-11-14): real close-up video for every sentence instead of drawings.
1. free LLM writes 10-12 sentences + for each a concrete stock-video search ("spark plug firing close up") and a 1-3 word label
2. Pexels (PEXELS_API_KEY) / Pixabay (PIXABAY_API_KEY) free stock video: one real clip per sentence, never the same clip twice
3. ffmpeg: portrait 1080x1920, strong push-in zoom on each clip, white flash cut, big caption, yellow label with an arrow
4. energetic edge-tts voice + generated music + whoosh on every cut (scene_lib/audio.py)
Usage: python3 scene_lib/footage.py --topic-file topic.txt out.mp4   (writes auto-scene.json too)"""
import re, json, os, random, subprocess, sys, textwrap, time, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm
import scene_lib.writer as W
import scene_lib.quality as Q
from scene_lib.writer import _call
W.SYS = 'You write narration for viral, accurate explainer Shorts made from real stock footage. Return only valid JSON.'
HOOK = ['']
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
WPS = 2.7
UA = {'User-Agent': 'content-engine/1.0'}

PROMPT = """Write a 45-60 second explainer Short: "{topic}". It is made of REAL close-up stock video clips, one per sentence, with a hard zoom on the part being explained.
Rules:
- 10 to 12 sentences, 8 to 14 words each, 125 to 160 words in total.
- Sentence 1 is a hook question or surprising fact. Then follow what really happens, in order, one action per sentence, small physical details, say WHY it works. Last sentence: a short payoff.
- Speaker style: talk to the viewer ("you"), calm, direct, confident. No hype words. True general facts only; no numbers you are not sure of.
- For each sentence "query": 2-4 English words to search a stock video site for a REAL close-up that shows exactly this (e.g. "car key ignition", "spark plug", "engine pistons", "car battery", "gasoline pump nozzle"). Concrete objects, no abstract words, no text, no people's names.
- "label": 1-3 words naming the part shown (e.g. "Spark plug").
- "image": one English sentence describing a photorealistic, extremely detailed close-up picture that SHOWS exactly this sentence, like a high-end engineering cut-away or macro photo: name the exact part, what it is doing, the view (cut-away, macro, inside view), BRIGHT lighting. Use the exact real name of the object (never a look-alike: a spark plug, not a candle). Example: "photorealistic cut-away of a car engine cylinder, piston at the top, spark plug firing a bright blue spark into fuel mist, bright even studio lighting, light grey background". No text or letters in the picture.
- "move": one short English sentence saying what physically MOVES in that picture, FAST and clearly visible (e.g. "the key turns clockwise in the ignition", "the two gears spin and mesh together").
- "sound": the ONE real-world sound heard in that shot, chosen from: {sounds}. Pick what the moving thing really sounds like (gears turning = gears, engine running = engine, key turning = click, electricity = buzz, fire = crackle, water = flow).
- title: starts with How or Why, 4-8 words, ends with ONE emoji.
- hook: 3-7 words shown small at the top of the whole video, a curiosity hook (e.g. "What really happens when you turn the key"). No emoji.
Return only JSON: {{"title": "...", "hook": "...", "principle": "one sentence why it works", "steps": [{{"say": "...", "query": "...", "label": "...", "image": "...", "move": "...", "sound": "click"}}]}}"""


def problems(c):
    e = []
    if not isinstance(c, dict): return ['answer must be a JSON object']
    st = c.get('steps') if isinstance(c.get('steps'), list) else []
    if not 10 <= len(st) <= 12: e.append('write 10 to 12 sentences (you wrote %d)' % len(st))
    tot = 0
    for k, s in enumerate(st, 1):
        if not isinstance(s, dict) or not all(isinstance(s.get(x), str) and s[x].strip() for x in ('say', 'query', 'label', 'image')): e.append('sentence %d needs say, query, label, image' % k); continue
        n = len(s['say'].split()); tot += n
        if not 6 <= n <= 16: e.append('sentence %d: 8 to 14 words (has %d)' % (k, n))
        if len(s['query'].split()) > 5: e.append('sentence %d: query max 4 words' % k)
    if tot and not 110 <= tot <= 170: e.append('total words %d: aim for 125 to 160' % tot)
    if not isinstance(c.get('title'), str) or not c['title'].split() or c['title'].split()[0] not in ('How', 'Why'): e.append('title must start with How or Why')
    return e


def write(topic, log):
    from scene_lib.audio import SFX
    prompt, last, errs, turn = PROMPT.format(topic=topic, sounds=', '.join(sorted(SFX))), None, None, 0
    for k in range(4):
        p = prompt if not errs else prompt + '\n\nYOUR LAST ANSWER HAD THESE PROBLEMS, fix them all and return the full JSON:\n' + '\n'.join('- ' + x for x in errs) + '\n\nLast answer:\n' + json.dumps(last, ensure_ascii=False)[:6000]
        try: last = _call(llm, p, 0.8 if k == 0 else 0.4, turn, log)
        except llm.BudgetExceeded as e: raise SystemExit(str(e))
        except Exception as e:
            turn += 1; log('try %d: no free LLM answered (%s); waiting 30 s' % (k + 1, str(e)[:200])); time.sleep(30); continue
        turn += 1; errs = problems(last)
        log('try %d: %s' % (k + 1, 'PASSED' if not errs else '; '.join(errs[:8])))
        if not errs: return last
    raise SystemExit('REJECTED: the narration could not pass after 4 tries. No video was made.')


def _get(url, headers=None):
    r = urllib.request.Request(url, headers=dict(UA, **(headers or {})))
    with urllib.request.urlopen(r, timeout=40) as x: return x.read()


def pexels(q, used):
    key = os.environ.get('PEXELS_API_KEY', '').strip()
    if not key: return None
    for orient in ('portrait', ''):
        u = 'https://api.pexels.com/videos/search?per_page=15&size=medium&query=' + urllib.parse.quote(q) + ('&orientation=' + orient if orient else '')
        try: vids = json.loads(_get(u, {'Authorization': key})).get('videos', [])
        except Exception: vids = []
        for v in vids:
            if v.get('id') in used or v.get('duration', 0) < 3: continue
            files = [f for f in v.get('video_files', []) if f.get('link') and (f.get('height') or 0) >= 720 and max(f.get('height') or 0, f.get('width') or 0) <= 2160]
            if not files: continue
            f = min(files, key=lambda f: abs((f.get('height') or 0) - 1920))
            used.add(v['id']); return f['link']
    return None


def pixabay(q, used):
    key = os.environ.get('PIXABAY_API_KEY', '').strip()
    if not key: return None
    try: hits = json.loads(_get('https://pixabay.com/api/videos/?per_page=15&safesearch=true&key=' + key + '&q=' + urllib.parse.quote(q))).get('hits', [])
    except Exception: return None
    for h in hits:
        if ('px' + str(h.get('id'))) in used or h.get('duration', 0) < 3: continue
        v = h.get('videos', {}); f = v.get('large') if (v.get('large') or {}).get('url') else v.get('medium')
        if f and f.get('url'): used.add('px' + str(h['id'])); return f['url']
    return None


def _crop_mark(f):
    """NO_MARK: the free picture service prints a small name in the bottom-left corner; cut the bottom 7% away."""
    try:
        import cv2; im = cv2.imread(f); h = im.shape[0]; cv2.imwrite(f, im[:int(h * 0.93)], [cv2.IMWRITE_JPEG_QUALITY, 95])
    except Exception: pass


def ai_image(desc, i, log, seeds=None):
    """AI_PICTURE: free Pollinations image service (FLUX model, no key): a photorealistic close-up / cut-away made for this exact sentence."""
    prompt = desc + ', photorealistic, ultra detailed, tack sharp focus, bright well-lit high-key lighting, vivid colors, vertical 9:16, no text, no letters, no watermark'
    tok = os.environ.get('POLLINATIONS_TOKEN', '').strip()
    for k, seed in enumerate(seeds or (7 + i, 101 + i, 211 + i, 307 + i, 401 + i)):
        time.sleep((16 if i else 0) if k == 0 else 35)   # PACING: the free tier allows about one picture every 15 seconds; wait longer after a refusal
        u = 'https://image.pollinations.ai/prompt/' + urllib.parse.quote(prompt) + '?width=1080&height=1920&nologo=true&model=flux&seed=%d' % seed
        try:
            b = _get(u, {'Authorization': 'Bearer ' + tok} if tok else None)
            if len(b) > 30000 and b[:3] in (b'\xff\xd8\xff', b'\x89PN'):
                f = 'img%02d.jpg' % i; Path(f).write_bytes(b); _crop_mark(f); log('AI picture %d: %s' % (i + 1, desc[:90])); return f, u.split('?')[0]
        except Exception as e: log('AI picture %d failed (%s)' % (i + 1, str(e)[:80]))
    return None, None


def find_clip(q, label, used, log):
    for qq in (q, label, ' '.join(q.split()[-2:]), q.split()[-1]):
        for src in (pexels, pixabay):
            u = src(qq, used)
            if u: log('clip for "%s": %s (%s)' % (q, src.__name__, qq)); return u
    return None


def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(' '.join(a[:3]) + ': ' + r.stderr[-600:])
    return r.stdout


def esc(path): return path.replace(':', '\\:')


XF = 0.3   # crossfade seconds between shots


# MOTION_MODE (owner 2026-11-15, permanent): the DEFAULT builds every shot from a sharp picture with real depth-parallax camera work (CPU only, minutes, never melts,
# no GPU quota, so 3+ videos a day are possible). AI-invented motion is only a bonus: set CE_AI_MOTION=1 (it still goes through the quality gate).
AI_MOTION = os.environ.get('CE_AI_MOTION') == '1'

def shot(i, src, d, say, label, first_title=None, push=0.6):
    """one sentence = one clip: cover-crop to 1080x1920, hard push-in (1.0 -> 1.5), white flash in, caption on top, label + arrow."""
    # CLEAN_SCREEN (owner 2026-11-14): no subtitles, no label or title in the middle; only one small hook line at the top for the whole video
    Path('hook.txt').write_text(HOOK[0])
    z = '(1+%.2f*t/%.2f)' % (push, d)   # push-in toward the centre (small when the clip already moves in 3D)
    vf = [f"scale=w='trunc(1080*{z}/2)*2':h='trunc(1920*{z}/2)*2':force_original_aspect_ratio=increase:eval=frame",
          "crop=1080:1920", "setsar=1", "fps=30", "eq=saturation=1.25:contrast=1.08",
          f"drawtext=fontfile={FONT}:textfile=hook.txt:fontsize=40:line_spacing=8:fontcolor=white:box=1:boxcolor=black@0.45:boxborderw=16:x=(w-tw)/2:y=120"]
    still = src.endswith('.jpg')
    if not still:   # a short moving clip is slowed to fill its sentence instead of jumping back to the start
        try:
            cd = float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src).strip())
            # REAL_SPEED (owner 2026-11-15: motion must look fast and alive): slow down at most 1.3x, then play it back and forth
            if 0.5 < cd < d: vf.insert(0, 'setpts=PTS*%.3f' % min(1.3, d / cd + 0.02))
            if cd * 1.3 < d:
                rb = 'rb%02d.mp4' % i
                sh('ffmpeg', '-v', 'error', '-y', '-i', src, '-filter_complex', '[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0', '-an', '-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast', rb)
                src = rb
            # CRISP_BRIGHT (owner 2026-11-15: clips were blurry and dark): sharp upscale, lift dark parts, sharpen
            vf.insert(0, 'scale=1080:1920:flags=lanczos:force_original_aspect_ratio=increase')
            vf.insert(len(vf) - 1, 'eq=gamma=1.18:brightness=0.03:contrast=1.05,unsharp=7:7:1.1:5:5:0.0')
        except Exception: pass
    sh('ffmpeg', '-v', 'error', '-y', *(['-loop', '1', '-framerate', '30'] if still else ['-stream_loop', '-1']), '-i', src, '-t', '%.2f' % d, '-an', '-vf', ','.join(vf),
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', 'shot%02d.mp4' % i)


def main():
    topic_file, out = sys.argv[sys.argv.index('--topic-file') + 1], sys.argv[-1]
    topic = Path(topic_file).read_text().strip()
    log = lambda m: (print(m, flush=True), open('writer-log.txt', 'a').write(m + '\n'))
    topic = re.sub(r'\s+20\d\d-\d\d-\d\dT[\d:]+$', '', topic).strip()   # run.trigger carries a timestamp after the topic; 'auto 2026-..' must still mean auto
    if topic.lower() in ('auto', ''):
        from scene_lib import ideas
        idea = ideas.pick(log); topic = idea['topic']; Path('idea.json').write_text(json.dumps(idea, ensure_ascii=False))
    log('real-footage writer: ' + topic)
    c = write(topic, log)
    HOOK[0] = '\n'.join(textwrap.wrap(''.join(ch for ch in (c.get('hook') or c['title']) if ord(ch) < 0x2000).strip(), 34)[:2])   # whole hook, at most 2 short lines
    used, t, steps = set(), 0.3, []
    PIC_PASS, SHARP = [], {}   # CHECKS_FILE: what the autopilot may trust
    for i, s in enumerate(c['steps']):
        f, u = ai_image(s['image'], i, log); ok = None
        for tryn in range(3):   # PICTURE_CHECK (owner 2026-11-15): a vision AI confirms the picture shows the named part, else draw again
            if not f: break
            ok, note = Q.picture_ok(f, s['say'], s['label'] + ' (' + s['image'][:160] + ')', log)
            log('picture %d check: %s (%s)' % (i + 1, {True: 'OK', False: 'WRONG', None: 'not checked'}[ok], note))
            if ok is not False: break
            f2, u2 = ai_image(s['image'] + ', clearly showing the ' + s['label'], i, log, seeds=(901 + 37 * tryn + i, 1301 + i))
            if f2: f, u = f2, u2
        PIC_PASS.append(ok is True)
        if not f and steps:   # NO_RANDOM_CLIPS (owner 2026-11-14: unrelated stock clips like the sea looked wrong): reuse the last matching picture
            f, u = steps[-1]['file'], steps[-1]['clip']; log('picture %d: reusing the previous picture' % (i + 1))
        if not f:
            raise SystemExit('REJECTED: the free picture service gave no picture for the first sentence. No video was made.')
        d = round(max(3.0, len(s['say'].split()) / WPS + 0.7), 2)
        steps.append({'start': round(t, 2), 'end': round(t + d, 2), 'say': s['say'], 'label': s['label'], 'query': s['query'], 'clip': u, 'file': f}); t += d
    T = round(t + 0.6, 2)
    steps[-1]['end'] = round(T, 2)
    from scene_lib.parallax import make_clip
    styles = ['push', 'orbit', 'pull', 'rise', 'orbit_l', 'pull_r', 'fall']
    # REAL_MOTION on every shot (owner 2026-11-14: everything must really move). GPU 1: Hugging Face (free ZeroGPU), shot by shot until its
    # daily time runs out; GPU 2: Kaggle (free ~30 h/week), all remaining shots in one batch; last resort: gentle 3D glide.
    from scene_lib.hf_motion import animate
    moved, hf_down = {}, 0
    for i, s in enumerate(steps):
        if AI_MOTION and s['file'].endswith('.jpg') and c['steps'][i].get('move') and hf_down < 2:
            mv = animate(s['file'], c['steps'][i]['move'], 'real%02d.mp4' % i, log)
            if mv: moved[i] = mv; hf_down = 0
            else: hf_down += 1   # two refusals in a row = its free time is used up for today
    rest = [{'img': s['file'], 'move': c['steps'][i]['move'], 'out': 'real%02d.mp4' % i} for i, s in enumerate(steps)
            if i not in moved and s['file'].endswith('.jpg') and c['steps'][i].get('move')]
    if rest and AI_MOTION:
        from scene_lib.kaggle_motion import animate_batch
        got = animate_batch(rest, log)
        for i, s in enumerate(steps):
            if ('real%02d.mp4' % i) in got: moved[i] = got['real%02d.mp4' % i]
    for i in list(moved):   # MOTION_CHECK (owner 2026-11-15: many shots did not really move): reject clips that look like a still photo
        try:
            m = Q.motion_score(moved[i]); b, sh_ = Q.looks(moved[i])
            log('shot %d motion %.2f brightness %.0f sharpness %.0f' % (i + 1, m, b, sh_)); SHARP[i] = (round(m, 2), round(b), round(sh_))
            pb, ps = Q.looks(steps[i]['file'])   # QUALITY_GATE (owner 2026-11-15 22:20: clips came out dark, smeared, chaotic): the clip must stay as bright and sharp as its own picture
            if m < 0.6: log('shot %d barely moves: using the 3D glide instead' % (i + 1)); del moved[i]
            elif m > 6.0 or b < max(55, 0.6 * pb) or sh_ < 0.45 * ps:
                log('shot %d clip is chaotic/dark/blurry (motion %.1f, brightness %.0f vs %.0f, sharpness %.0f vs %.0f): using the sharp 3D glide instead' % (i + 1, m, b, pb, sh_, ps)); del moved[i]
        except Exception as e: log('motion check failed for shot %d (%s)' % (i + 1, str(e)[:80]))
    log('real motion on %d of %d shots' % (len(moved), len(steps)))
    # CHECKS_FILE (owner 2026-11-15): machine-readable verdict for the How It Ticks autopilot. 'ok' only when every picture passed the vision check
    # AND at least half the shots really move AND no moving clip is dark/blurry. Anything else is 'warn' (waits for the owner).
    reasons = []
    if not all(PIC_PASS): reasons.append('%d of %d pictures not confirmed by the vision check' % (PIC_PASS.count(False), len(PIC_PASS)))
    if AI_MOTION and len(moved) * 2 < len(steps): reasons.append('real motion on only %d of %d shots' % (len(moved), len(steps)))
    dark = [i + 1 for i in moved if i in SHARP and SHARP[i][1] < 60]; blur = [i + 1 for i in moved if i in SHARP and SHARP[i][2] < 8]
    for i, st in enumerate(steps):   # camera mode: the PICTURES must be sharp and bright (that is all the viewer sees)
        try:
            pb, ps = Q.looks(st['file'])
            if pb < 60: dark.append(i + 1)
            if ps < 25: blur.append(i + 1)
        except Exception: pass
    if dark: reasons.append('dark clips: %s' % dark)
    if blur: reasons.append('blurry clips: %s' % blur)
    Path('ce-checks.json').write_text(json.dumps({'verdict': 'warn' if reasons else 'ok', 'reasons': reasons, 'pictures_ok': PIC_PASS, 'moving': len(moved), 'shots': len(steps)}))
    durs = []
    for i, s in enumerate(steps):
        d = (s['end'] - s['start']) + (0.3 if i == 0 else 0); src, push = s['file'], 0.6
        if i in moved: src, push = moved[i], 0.05
        elif src.endswith('.jpg'):   # MOTION_3D fallback: gentle 3D glide
            try: src = make_clip(src, 'm3d%02d.mp4' % i, d + 0.1, styles[i % len(styles)]); push = 0.08
            except Exception as e: log('3D motion failed for picture %d (%s); zoom only' % (i + 1, str(e)[:80]))
        durs.append(d)
        shot(i, src, d + (XF if i < len(steps) - 1 else 0), s['say'], s['label'], c['title'] if i == 0 else None, push)
    # SMOOTH_CUTS (owner 2026-11-15): shots dissolve into each other (0.3 s crossfade, total length unchanged) instead of hard flash cuts
    if len(steps) == 1: sh('ffmpeg', '-v', 'error', '-y', '-i', 'shot00.mp4', '-c', 'copy', 'silent.mp4')
    else:
        parts, last, off = [], '[0:v]', 0.0
        for k in range(1, len(steps)):
            off += durs[k - 1]; nm = '[x%d]' % k
            parts.append('%s[%d:v]xfade=transition=fade:duration=%.2f:offset=%.3f%s' % (last, k, XF, off, nm)); last = nm
        sh('ffmpeg', '-v', 'error', '-y', *sum((['-i', 'shot%02d.mp4' % k] for k in range(len(steps))), []), '-filter_complex', ';'.join(parts), '-map', last, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', 'silent.mp4')
    from scene_lib import audio as A
    voice, vlog = A.speak([(s['start'], s['end'], s['say']) for s in steps])
    fx = A.Track(T)
    for i, s in enumerate(steps):
        # QUIET_SOUNDS (owner 2026-11-15): no whoosh on cuts; effects sit quietly under the voice, the heartbeat very quietly
        snd = c['steps'][i].get('sound')   # AUTO_SOUNDS: the writer names the real sound of each shot
        if snd in A.SFX:
            dd = max(0.5, s['end'] - s['start'] - 0.2)
            fx.add(s['start'] + 0.1, A.SFX[snd](dd) if snd in A.LONG_SFX else A.SFX[snd](), 0.12 if snd == 'heartbeat' else 0.28 if snd in A.LONG_SFX else 0.4)
    bed = A.music(T, bpm=124)
    A.write_wav('audio.wav', A.mix(T, voice, fx.buf, bed))
    sh('ffmpeg', '-v', 'error', '-y', '-i', 'silent.mp4', '-i', 'audio.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', out)
    spec = {'mode': 'real-footage', 'title': c['title'], 'principle': c.get('principle', ''), 'duration': T,
            'steps': [{k: s[k] for k in ('start', 'end', 'say', 'label', 'query', 'clip')} for s in steps],
            'credits': 'Pictures: Pollinations (FLUX, free). Plan B clips: Pexels / Pixabay (free licences).'}
    Path('auto-scene.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1))
    Path('voice-log.txt').write_text('\n'.join(vlog) + '\n')
    Path('evidence-report.json').write_text(json.dumps({'mode': 'real-footage', 'errors': [], 'note': 'pictures/clips chosen by search and AI; facts need human review'}))
    log('real-footage video: %d clips, %.1f s -> %s' % (len(steps), T, out))


if __name__ == '__main__':
    main()
