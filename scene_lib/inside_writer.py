"""INSIDE_STORY writer: the free LLM writes 10-12 sentences about ONE drawn object and names the inside spot each sentence is about.
template layout: prop_story.py. Topics are only about objects in the drawn library (car, microwave ...).
Usage: python3 scene_lib/inside_writer.py --topic-file topic.txt auto-scene.json   (topic "auto" = next library topic not made yet)"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm
import scene_lib.writer as W
from scene_lib.writer import _call
from scene_lib.prop_story import LIBRARY, build
W.SYS = 'You write the narration of short, accurate animated explainer videos. Return only valid JSON.'

TOPICS = {
    'car': ['How a car engine starts', 'How fuel turns into motion in a car', 'How a car battery gets recharged while you drive',
            'Why a car needs a spark plug', 'How the gearbox moves a car forward', 'Where the exhaust smoke of a car comes from'],
    'microwave': ['How a microwave heats food', 'Why the microwave plate spins', 'Why metal sparks in a microwave'],
}
HIST = Path(__file__).resolve().parent.parent / 'data' / 'scenes' / 'inside-history.json'

PROMPT = """Write the narration of a 45-60 second animated explainer: "{topic}".
The picture is ONE detailed drawing: {describe}.
The camera flies into one inside spot per sentence, and that part moves. Spots you can use: {spots}.
Rules:
- 10 to 12 sentences, 9 to 14 words each, 130 to 160 words in total.
- Speaker style: talk to the viewer ("you"), calm and direct, one action per sentence in the real order things happen, small physical details, and say WHY it works. No hype words.
- True general facts only. No numbers you are not sure of.
- Every sentence names exactly one "spot" from the list, the part it talks about. Start and end with "whole".
- title: starts with How or Why, 4-8 words, ends with ONE emoji.
Return only JSON: {{"title": "...", "principle": "one sentence: why it works", "object": "{obj}", "steps": [{{"say": "...", "spot": "whole"}}]}}"""


def problems(c, obj):
    e = []
    if not isinstance(c, dict): return ['answer must be a JSON object']
    spots = LIBRARY[obj]['spots']
    steps = c.get('steps') if isinstance(c.get('steps'), list) else []
    if not 10 <= len(steps) <= 12: e.append('write 10 to 12 sentences (you wrote %d)' % len(steps))
    total = 0
    for k, s in enumerate(steps, 1):
        if not isinstance(s, dict) or not isinstance(s.get('say'), str): e.append('sentence %d needs "say"' % k); continue
        n = len(s['say'].split()); total += n
        if not 7 <= n <= 16: e.append('sentence %d: 9 to 14 words (has %d)' % (k, n))
        if s.get('spot') not in spots: e.append('sentence %d: spot must be one of %s' % (k, ', '.join(spots)))
    if total and not 115 <= total <= 170: e.append('total words %d: aim for 130 to 160' % total)
    if len({s.get('spot') for s in steps if isinstance(s, dict)}) < 5: e.append('use at least 5 different spots so the camera visits the inside')
    if not isinstance(c.get('title'), str) or not c['title'].split() or c['title'].split()[0] not in ('How', 'Why'): e.append('title must start with How or Why')
    return e


def pick():
    try: done = json.loads(HIST.read_text())
    except (OSError, ValueError): done = []
    for obj, ts in TOPICS.items():
        for tp in ts:
            if tp not in done: return obj, tp
    return 'car', TOPICS['car'][len(done) % len(TOPICS['car'])]


def main():
    topic_file, out = sys.argv[sys.argv.index('--topic-file') + 1], sys.argv[-1]
    raw = Path(topic_file).read_text().strip()
    if raw.lower() in ('auto', ''): obj, topic = pick()
    else:
        topic = raw; low = raw.lower()
        obj = next((o for o in LIBRARY if o in low), None) or ('microwave' if any(w in low for w in ('oven', 'heat food')) else 'car')
    log = lambda m: (print(m, flush=True), open('writer-log.txt', 'a').write(m + '\n'))
    log('inside-story writer: %s (drawn object: %s)' % (topic, obj))
    Path('idea.json').write_text(json.dumps({'topic': topic, 'object': obj}))
    lib = LIBRARY[obj]
    prompt = PROMPT.format(topic=topic, describe=lib['describe'], spots=', '.join(lib['spots']), obj=obj)
    last, errs, turn = None, None, 0
    for k in range(4):
        p = prompt if not errs else prompt + '\n\nYOUR LAST ANSWER HAD THESE PROBLEMS, fix them all and return the full JSON:\n' + '\n'.join('- ' + x for x in errs) + '\n\nLast answer:\n' + json.dumps(last, ensure_ascii=False)[:6000]
        try: last = _call(llm, p, 0.7 if k == 0 else 0.4, turn, log)
        except llm.BudgetExceeded as e: raise SystemExit(str(e))
        except Exception as e:
            turn += 1; log('try %d: no free LLM answered (%s); waiting 30 s' % (k + 1, str(e)[:200])); time.sleep(30); continue
        turn += 1
        if isinstance(last, dict): last['object'] = obj
        errs = problems(last, obj)
        log('try %d: %s' % (k + 1, 'PASSED' if not errs else '; '.join(errs[:8])))
        if not errs:
            Path('content.json').write_text(json.dumps(last, ensure_ascii=False, indent=1))
            spec = build(last); Path(out).write_text(json.dumps(spec, ensure_ascii=False, indent=1))
            try: done = json.loads(HIST.read_text())
            except (OSError, ValueError): done = []
            HIST.write_text(json.dumps(done + [topic], indent=1))
            log('inside story built: %d steps, %.1f s' % (len(spec['steps']), spec['duration']))
            return
    raise SystemExit('REJECTED: the narration could not pass after 4 tries. No video was made.')


if __name__ == '__main__':
    main()
