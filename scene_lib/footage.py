"""REAL_FOOTAGE (owner 2026-11-14): real close-up video for every sentence instead of drawings.
1. free LLM writes 10-12 sentences + for each a concrete stock-video search ("spark plug firing close up") and a 1-3 word label
2. Pexels (PEXELS_API_KEY) / Pixabay (PIXABAY_API_KEY) free stock video: one real clip per sentence, never the same clip twice
3. ffmpeg: portrait 1080x1920, strong push-in zoom on each clip, white flash cut, big caption, yellow label with an arrow
4. energetic edge-tts voice + generated music + whoosh on every cut (scene_lib/audio.py)
Usage: python3 scene_lib/footage.py --topic-file topic.txt out.mp4   (writes auto-scene.json too)"""
import json, os, random, subprocess, sys, textwrap, time, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm
import scene_lib.writer as W
from scene_lib.writer import _call
W.SYS = 'You write narration for viral, accurate explainer Shorts made from real stock footage. Return only valid JSON.'
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
- title: starts with How or Why, 4-8 words, ends with ONE emoji.
Return only JSON: {{"title": "...", "principle": "one sentence why it works", "steps": [{{"say": "...", "query": "...", "label": "..."}}]}}"""


def problems(c):
    e = []
    if not isinstance(c, dict): return ['answer must be a JSON object']
    st = c.get('steps') if isinstance(c.get('steps'), list) else []
    if not 10 <= len(st) <= 12: e.append('write 10 to 12 sentences (you wrote %d)' % len(st))
    tot = 0
    for k, s in enumerate(st, 1):
        if not isinstance(s, dict) or not all(isinstance(s.get(x), str) and s[x].strip() for x in ('say', 'query', 'label')): e.append('sentence %d needs say, query, label' % k); continue
        n = len(s['say'].split()); tot += n
        if not 6 <= n <= 16: e.append('sentence %d: 8 to 14 words (has %d)' % (k, n))
        if len(s['query'].split()) > 5: e.append('sentence %d: query max 4 words' % k)
    if tot and not 110 <= tot <= 170: e.append('total words %d: aim for 125 to 160' % tot)
    if not isinstance(c.get('title'), str) or not c['title'].split() or c['title'].split()[0] not in ('How', 'Why'): e.append('title must start with How or Why')
    return e


def write(topic, log):
    prompt, last, errs, turn = PROMPT.format(topic=topic), None, None, 0
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


def shot(i, src, d, say, label, first_title=None):
    """one sentence = one clip: cover-crop to 1080x1920, hard push-in (1.0 -> 1.5), white flash in, caption on top, label + arrow."""
    cap = Path('cap%d.txt' % i); cap.write_text('\n'.join(textwrap.wrap(say, 22)))
    lab = Path('lab%d.txt' % i); lab.write_text(label.upper()[:22])
    z = '(1+0.5*t/%.2f)' % d
    vf = [f"scale=w='trunc(1080*{z}/2)*2':h='trunc(1920*{z}/2)*2':force_original_aspect_ratio=increase:eval=frame",
          "crop=1080:1920", "setsar=1", "fps=30", "eq=saturation=1.25:contrast=1.08",
          "fade=in:st=0:d=0.18:color=white",
          f"drawtext=fontfile={FONT}:textfile={cap}:fontsize=64:fontcolor=white:borderw=7:bordercolor=black@0.85:line_spacing=12:x=(w-tw)/2:y=170",
          f"drawtext=fontfile={FONT}:text='▼':fontsize=110:fontcolor=#FFD60A:borderw=6:bordercolor=black:x=(w-tw)/2:y=1080+18*sin(t*8)",
          f"drawtext=fontfile={FONT}:textfile={lab}:fontsize=58:fontcolor=black:box=1:boxcolor=#FFD60A:boxborderw=22:x=(w-tw)/2:y=960"]
    if first_title:
        Path('title.txt').write_text('\n'.join(textwrap.wrap(first_title, 16)))
        vf.append(f"drawtext=fontfile={FONT}:textfile=title.txt:fontsize=84:fontcolor=#FFD60A:borderw=9:bordercolor=black:line_spacing=10:x=(w-tw)/2:y=1450:enable='lt(t,{d:.2f})'")
    sh('ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', '-i', src, '-t', '%.2f' % d, '-an', '-vf', ','.join(vf),
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', 'shot%02d.mp4' % i)


def main():
    topic_file, out = sys.argv[sys.argv.index('--topic-file') + 1], sys.argv[-1]
    topic = Path(topic_file).read_text().strip()
    log = lambda m: (print(m, flush=True), open('writer-log.txt', 'a').write(m + '\n'))
    if topic.lower() in ('auto', ''):
        from scene_lib import ideas
        idea = ideas.pick(log); topic = idea['topic']; Path('idea.json').write_text(json.dumps(idea, ensure_ascii=False))
    log('real-footage writer: ' + topic)
    if not (os.environ.get('PEXELS_API_KEY') or os.environ.get('PIXABAY_API_KEY')): raise SystemExit('REJECTED: no PEXELS_API_KEY or PIXABAY_API_KEY secret, so no real clips can be found.')
    c = write(topic, log)
    used, t, steps = set(), 0.3, []
    for i, s in enumerate(c['steps']):
        u = find_clip(s['query'], s['label'], used, log)
        if not u: raise SystemExit('REJECTED: no real clip found for "%s". No video was made.' % s['query'])
        f = 'clip%02d.mp4' % i; Path(f).write_bytes(_get(u))
        d = round(max(3.0, len(s['say'].split()) / WPS + 0.7), 2)
        steps.append({'start': round(t, 2), 'end': round(t + d, 2), 'say': s['say'], 'label': s['label'], 'query': s['query'], 'clip': u, 'file': f}); t += d
    T = round(t + 0.6, 2)
    steps[-1]['end'] = round(T, 2)
    for i, s in enumerate(steps):
        shot(i, s['file'], (s['end'] - s['start']) + (0.3 if i == 0 else 0), s['say'], s['label'], c['title'] if i == 0 else None)
    Path('shots.txt').write_text(''.join("file 'shot%02d.mp4'\n" % i for i in range(len(steps))))
    sh('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'shots.txt', '-c', 'copy', 'silent.mp4')
    from scene_lib import audio as A
    voice, vlog = A.speak([(s['start'], s['end'], s['say']) for s in steps])
    fx = A.Track(T)
    for s in steps: fx.add(max(0, s['start'] - 0.15), A.whoosh(), 0.55)
    bed = A.music(T, bpm=124)
    A.write_wav('audio.wav', A.mix(T, voice, fx.buf, bed))
    sh('ffmpeg', '-v', 'error', '-y', '-i', 'silent.mp4', '-i', 'audio.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', out)
    spec = {'mode': 'real-footage', 'title': c['title'], 'principle': c.get('principle', ''), 'duration': T,
            'steps': [{k: s[k] for k in ('start', 'end', 'say', 'label', 'query', 'clip')} for s in steps],
            'credits': 'Videos from Pexels / Pixabay (free licences).'}
    Path('auto-scene.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1))
    Path('voice-log.txt').write_text('\n'.join(vlog) + '\n')
    log('real-footage video: %d clips, %.1f s -> %s' % (len(steps), T, out))


if __name__ == '__main__':
    main()
