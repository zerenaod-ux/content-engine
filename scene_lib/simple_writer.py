"""CLEAN_TEMPLATE writer: asks a free LLM only for a short content list (star, 3-5 chain parts, 10-12 sentences) and lets template.py lay it out.
One small request per try, so it also fits the small free services. Usage: python3 scene_lib/simple_writer.py --topic-file topic.txt auto-scene.json"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm
from scene_lib.template import build
import scene_lib.writer as W
from scene_lib.writer import _call
W.SYS = 'You write the content of short, accurate animated explainer videos. Return only valid JSON.'

PROMPT = """Write a 45-60 second animated explainer about: {topic}

The picture is FIXED: one big "star" object at the top, then 3 to 5 picture cards in a chain below it, connected by arrows in order. Each card is ONE emoji with a 1-2 word label.
You choose only the content. Rules:
- star: the real everyday thing the video is about, as ONE emoji that clearly shows it.
- items: 3 to 5 cards, in the order energy/matter/action passes along. Each: "id" (short, lowercase), "emoji" (ONE common emoji that really looks like that part, e.g. 🔋 battery, ⚙️ gear or motor, 💧 water, 🔥 heat, ⚡ electricity, 🧲 magnet, 🌬️ air, 🛞 wheel), "label" (1-2 words, max 14 letters), "action": "spin" for things that rotate, else "pulse".
- steps: 10 to 12 sentences, 9 to 15 words each. Speaker style: talk to the viewer ("you"), calm and direct, one action per sentence in clear order, small physical details, say WHY it works. No hype words. True general facts only, no numbers you are not sure of.
- Each step: "say", "focus" = "star", one item id, or "all" (only the LAST step is "all"), and "link": [from_id, to_id] on the step where something passes from one to the next (from_id may be "star"). Every item must be the focus of at least one step, in chain order.
- title: starts with How or Why, 4-8 words, ends with ONE emoji.
- spark: ONE emoji for what travels along the arrows (⚡ electricity, 💧 water, 🔥 heat, 💨 air...).

Return only JSON:
{{"title": "...", "principle": "one sentence: why it works", "spark": "⚡", "star": {{"emoji": "🏎️", "label": "Race car"}},
 "items": [{{"id": "wheel", "emoji": "🛞", "label": "Wheel", "action": "spin"}}],
 "steps": [{{"say": "...", "focus": "star"}}, {{"say": "...", "focus": "wheel", "link": ["star", "wheel"]}}]}}"""


def problems(c):
    e = []
    if not isinstance(c, dict): return ['answer must be a JSON object']
    items = c.get('items') if isinstance(c.get('items'), list) else []
    ids = [i.get('id') for i in items if isinstance(i, dict)]
    if not 3 <= len(items) <= 5: e.append('items must be 3 to 5 cards')
    for i in items:
        if not isinstance(i, dict) or not all(isinstance(i.get(k), str) and i.get(k) for k in ('id', 'emoji', 'label')): e.append('each item needs id, emoji, label'); continue
        if len(i['emoji']) > 4: e.append('item %s: emoji must be ONE emoji' % i['id'])
        if len(i['label']) > 16: e.append('item %s: label max 14 letters' % i['id'])
    if len(set(ids)) != len(ids): e.append('item ids must be different')
    st = c.get('star')
    if not isinstance(st, dict) or not isinstance(st.get('emoji'), str) or len(st['emoji']) > 4: e.append('star needs ONE emoji')
    steps = c.get('steps') if isinstance(c.get('steps'), list) else []
    if not 10 <= len(steps) <= 12: e.append('write 10 to 12 steps (you wrote %d)' % len(steps))
    total = 0
    for k, s in enumerate(steps, 1):
        if not isinstance(s, dict) or not isinstance(s.get('say'), str): e.append('step %d needs "say"' % k); continue
        n = len(s['say'].split()); total += n
        if not 7 <= n <= 17: e.append('step %d: say must have 9 to 15 words (has %d)' % (k, n))
        if s.get('focus') not in ids + ['star', 'all']: e.append('step %d: focus must be "star", "all" or an item id' % k)
        l = s.get('link')
        if l is not None and not (isinstance(l, list) and len(l) == 2 and all(x in ids + ['star'] for x in l)): e.append('step %d: link must be [from_id, to_id]' % k)
    for i in ids:
        if not any(isinstance(s, dict) and s.get('focus') == i for s in steps): e.append('item %s is never the focus of a step' % i)
    if not isinstance(c.get('title'), str) or not c['title'].split() or c['title'].split()[0] not in ('How', 'Why'): e.append('title must start with How or Why')
    if total and not 120 <= total <= 175: e.append('total words %d: aim for 130 to 160 so the video lasts 45 to 60 seconds' % total)
    return e


def main():
    topic_file, out = sys.argv[sys.argv.index('--topic-file') + 1], sys.argv[-1]
    topic = Path(topic_file).read_text().strip()
    if topic.startswith('{'):
        try: topic = json.loads(topic).get('topic', topic)
        except ValueError: pass
    log = lambda m: (print(m, flush=True), open('writer-log.txt', 'a').write(m + '\n'))
    log('clean template writer: ' + topic)
    prompt, last, errs, turn = PROMPT.format(topic=topic), None, None, 0
    for k in range(4):
        p = prompt if not errs else prompt + '\n\nYOUR LAST ANSWER HAD THESE PROBLEMS, fix them all and return the full JSON:\n' + '\n'.join('- ' + x for x in errs) + '\n\nLast answer:\n' + json.dumps(last, ensure_ascii=False)[:6000]
        try: last = _call(llm, p, 0.8 if k == 0 else 0.4, turn, log)
        except llm.BudgetExceeded as e: raise SystemExit(str(e))
        except Exception as e:
            turn += 1; log('try %d: no free LLM answered (%s); waiting 30 s' % (k + 1, str(e)[:200])); time.sleep(30); continue
        turn += 1
        errs = problems(last)
        log('try %d: %s' % (k + 1, 'PASSED' if not errs else '; '.join(errs[:8])))
        if not errs:
            Path('content.json').write_text(json.dumps(last, ensure_ascii=False, indent=1))
            spec = build(last)
            Path(out).write_text(json.dumps(spec, ensure_ascii=False, indent=1))
            log('scene built from template: %d steps, %.1f s' % (len(spec['steps']), spec['duration']))
            return
    raise SystemExit('REJECTED: the content list could not pass after 4 tries. No video was made.')


if __name__ == '__main__':
    main()
