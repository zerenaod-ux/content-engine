"""THE WRITER: turns a topic into a full scene description, working the way a careful human designer does, with the free LLMs.
  1. PLAN  - find the cause (principle), the chain of cause and effect, the cast of objects and where each one stands, and 7 steps that each PROVE one sentence.
  2. STAGE - turn the plan into the exact scene description (parts, keyframes, camera, sounds).
  3. CHECK - the checker applies the design logic (physics, connections, camera, labels, proof for every sentence). Problems go back to the writer to fix.
A description that still fails after the tries is rejected: no video is made from it.
  python3 scene_lib/writer.py --topic-file topic.txt out.json        (needs the free LLM keys in the environment)"""
import json, os, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scene_lib.catalog import CATALOG, catalog_text, SOUNDS_DUR, SOUNDS_FREQ, SOUNDS_PLAIN, PRESETS, GROUNDS
OUTDOORS = {'day', 'dusk', 'night', 'desert', 'snow'}
from scene_lib.validate import check

TIMES = [(0.3, 4.5), (4.7, 9.2), (9.4, 13.6), (13.8, 18.6), (18.8, 23.4), (23.6, 28.4), (28.6, 33.5)]
DURATION = 33.6
SYS = 'You are a brilliant science animator and scene designer. You answer with ONE JSON object and nothing else.'
STAGE_TEXT = 'x goes right, y goes up. If there is ground, its surface is y=0 and things below 0 are underground. Keep everything between x=-380 and x=700 and between y=-220 and y=420. Objects are about 60 to 300 units big.'

def _num(v): return isinstance(v, (int, float)) and not isinstance(v, bool)

def plan_prompt(topic):
    return f"""TOPIC: {topic}

You will plan a 33-second animated explainer shown as ONE continuous living scene (no cuts): a cut-away side view where the viewer watches the thing work, step by step.
Work like a careful designer. Think in this order:

1. PRINCIPLE: the real cause. Why does it work? One or two true sentences.
2. CHAIN: 5 to 7 links of cause and effect, in the order they happen ("because A, B happens").
3. CAST: 4 to 8 objects the viewer must see. ANY topic can be drawn: "emoji" gives any recognisable object (animal, organ, planet, vehicle, tool, food, person, building), "path" draws any custom shape, and there are ready parts for water, pipes, wires, wheels, particles (fire, smoke, steam, sparks, bubbles, snow), meters and more. All part types: {', '.join(CATALOG)}.
   Also choose the SETTING that truly fits the topic: where it really happens. A kitchen, home or workshop topic is indoors: preset "clean" or "lab" with ground "floor" (no hills, no trees). Space has no ground. Only use outdoor presets for things that happen outdoors.
   The STAR of the video (the thing the topic is about) must be drawn LARGE and, when the secret is inside it, shown as a cut-away so the viewer sees inside.
4. LAYOUT: give every cast member a box on the stage: x0, x1, y0, y1. Stage: {STAGE_TEXT}
   - The layout must SHOW the principle. If gravity matters, the source is physically higher than where the water ends up. If something is underground, it is below y=0.
   - Put the objects in the order of the chain, left to right, so the camera travels one way.
   - Solid machines and buildings stand on dry ground, never inside water. Boxes of different objects must not overlap (a pipe or wire joins them).
   - EXCEPT things that truly sit inside another thing (clothes in a drum, a seed in a fruit, a piston in a cylinder): give them "inside": "<id of the container>" and place their box inside the container's box. Draw the container as a cut-away so the inside is seen.
5. STEPS: exactly 7. Each step = one spoken sentence + the ONE cast member that visibly changes to prove it (fills, drains, flows, spins, grows, lights up, appears).
   - "say": ONE energetic sentence, 8 to 13 plain words, spoken like an excited friend. Strong action verbs (slams, rockets, squeezes, bursts, snaps), never dull ones (is, has, creates, forms, allows). At least 5 sentences end with "!". Step 1 is a hook question. Step 7 is the payoff that ties it to the viewer's life.
   - True, general facts only. No numbers you are not sure of. No medical or money advice.
   - Be creative: choose a surprising, concrete angle, not a textbook definition.

Return JSON:
{{"title": "starts with How or Why, 4-8 words, ends with ONE emoji",
 "principle": "...",
 "style": "flow" (mostly water, pipes, machines) or "icons" (living things, body, space, objects, ideas),
 "setting": {{"preset": "day|dusk|night|desert|snow|space|ocean|body|lab|clean", "ground": "grass|sand|snow|rock|seabed|floor|none"}},
 "chain": ["...", "..."],
 "cast": [{{"id": "shortname", "what": "what it is", "built_from": "part types", "x0": 0, "x1": 0, "y0": 0, "y1": 0, "inside": "optional container id"}}],
 "steps": [{{"label": "2-16 letters", "say": "...", "shows": "cast id", "change": "what visibly changes"}}]}}"""

def check_plan(pl):
    E = []
    if not isinstance(pl, dict): return ['the plan must be one JSON object']
    if not isinstance(pl.get('principle'), str) or len(pl['principle'].split()) < 8: E.append('principle must be one or two full sentences')
    if pl.get('style') not in ('flow', 'icons'): E.append('style must be "flow" or "icons"')
    st_ = pl.get('setting')
    if not (isinstance(st_, dict) and st_.get('preset') in PRESETS and st_.get('ground') in GROUNDS | {'none'}): E.append('setting must be {"preset": one of %s, "ground": one of %s or "none"}' % (', '.join(sorted(PRESETS)), ', '.join(sorted(GROUNDS))))
    elif st_['preset'] in ('space', 'body') and st_['ground'] != 'none': E.append('a scene in space or inside a body has no ground: set ground to "none"')
    if not isinstance(pl.get('chain'), list) or not 4 <= len(pl['chain']) <= 8: E.append('chain must have 5 to 7 links')
    cast = pl.get('cast'); ids = {}
    if not isinstance(cast, list) or not 4 <= len(cast) <= 9: E.append('cast must have 4 to 8 objects'); cast = []
    for c in cast:
        if not isinstance(c, dict) or not isinstance(c.get('id'), str) or not all(_num(c.get(k)) for k in ('x0', 'x1', 'y0', 'y1')): E.append('each cast member needs id, x0, x1, y0, y1'); continue
        if c['id'] in ids: E.append('cast id "%s" is used twice' % c['id'])
        ids[c['id']] = c
        if c['x1'] <= c['x0'] or c['y1'] <= c['y0']: E.append('cast "%s": x1 must be greater than x0 and y1 greater than y0' % c['id'])
        if c['x0'] < -420 or c['x1'] > 760 or c['y0'] < -260 or c['y1'] > 460: E.append('cast "%s" is outside the stage' % c['id'])
    cs = list(ids.values())
    def anc(c):
        out = set(); cur = c.get('inside'); n = 0
        while isinstance(cur, str) and cur in ids and cur not in out and n < 8: out.add(cur); cur = ids[cur].get('inside'); n += 1
        return out
    for i, a in enumerate(cs):
        for b in cs[i + 1:]:
            ox = min(a['x1'], b['x1']) - max(a['x0'], b['x0']); oy = min(a['y1'], b['y1']) - max(a['y0'], b['y0'])
            if b['id'] in anc(a) or a['id'] in anc(b) or (anc(a) & anc(b)): continue   # one sits inside the other, or both sit inside the same container
            if ox > 0 and oy > 0:
                small = min((a['x1'] - a['x0']) * (a['y1'] - a['y0']), (b['x1'] - b['x0']) * (b['y1'] - b['y0']))
                if small > 0 and ox * oy / small > 0.35: E.append('cast "%s" and "%s" overlap; give each its own place and join them with a pipe or wire' % (a['id'], b['id']))
    st = pl.get('steps')
    if not isinstance(st, list) or len(st) != 7: E.append('steps must be exactly 7'); st = []
    for i, s in enumerate(st, 1):
        if not isinstance(s, dict): E.append('step %d must be an object' % i); continue
        if s.get('shows') not in ids: E.append('step %d: "shows" must be one of the cast ids' % i)
        w = len(str(s.get('say', '')).split())
        if not 6 <= w <= 14: E.append('step %d: "say" must be 8 to 13 words (it has %d)' % (i, w))
        if not isinstance(s.get('label'), str) or not 2 <= len(s['label']) <= 16: E.append('step %d: label must be 2 to 16 letters' % i)
    if st and isinstance(st[0], dict) and '?' not in str(st[0].get('say', '')): E.append('step 1 must be a hook question')
    if len(st) == 7 and sum(1 for s in st if isinstance(s, dict) and str(s.get('say', '')).strip().endswith(('!', '?'))) < 5: E.append('the script is flat: at least 5 of the 7 sentences must end with ! (or ? for the hook) and use strong action verbs')
    return E

def stage_prompt(topic, plan, with_example=True):
    ex = (ROOT / 'scene_lib' / ('example_icons.json' if plan.get('style') == 'icons' else 'example_flow.json')).read_text() if with_example else ''
    return f"""TOPIC: {topic}

Here is the approved PLAN. Now build the exact scene description from it.
{json.dumps(plan, ensure_ascii=False)}

STAGE: {STAGE_TEXT}
Parts are drawn in list order (later parts cover earlier ones): sky first (with the preset from the plan's setting), then scenery, ground (if any), the main objects, labels last.

PARTS YOU MAY USE (only these). Use "emoji" for any recognisable object and "path" to draw custom shapes; never leave a main subject as a plain box:
{catalog_text()}
Any part may have an "id". Give every cast member's main part the same id as in the plan. A part that sits inside another gets "inside": "<container id>".

ANIMATION: any number field can be a fixed number or keyframes [[time, value], ...]. The value holds before the first and after the last keyframe and moves smoothly between.

STEPS: copy the 7 steps from the plan (label, say, shows) and use exactly these times: {', '.join('step %d: %.1f-%.1f' % (i + 1, a, b) for i, (a, b) in enumerate(TIMES))}.

DESIGN RULES (a checker enforces every one):
1. Proof: in each step the part named in "shows" must have keyframes that change INSIDE that step's time, and nothing important should move before its own step.
2. Camera: a list of [time, x, y, zoom]. x is the centre of the picture, y is the height shown a little below the middle. zoom 0.62 shows about 1160 units across, 1.0 shows 720, 1.6 shows 450.
   Start wide at time 0 (show the whole stage), move to each step's "shows" part and zoom in so it is large (1.1 to 2.0), end wide at {DURATION}.
3. Physics: add "flows": [{{"from":[x,y],"to":[x,y],"by":"gravity"|"pump"|"pressure"}}] for every pipe or stream. Gravity flows must go DOWN. A pump flow needs a pump part. Pressure can only lift water to below its source height.
4. Connections: every pipe and wire must start and end touching the things it joins, or run off the edge of the stage (x=-360 or x=680) if it comes from outside. Mains water is "pressure", not gravity.
5. Machines, wheels, pumps and houses stand on dry ground, never inside a body of water. Water never floats: it sits in a container, behind a wall, or in the ground.
6. Houses, towers, trees and plants stand on the ground (y=0) or on top of a shape.
7. Labels: CAPITALS, at most 16 letters, each with "show" keyframes so it fades in during its own step and out again. Never more than 2 labels at once. No labels in step 1.
8. Sounds: "sfx" is a list of [time, name, loudness 0.3-1.0, optional value], at least 10, at least one in every step, timed to the action.
   With an optional length in seconds: {', '.join(sorted(SOUNDS_DUR))}. With an optional pitch: {', '.join(sorted(SOUNDS_FREQ))}. Plain: {', '.join(sorted(SOUNDS_PLAIN))}.
9. Make it alive: at least 8 parts that change over time; water levels, pipe progress and flow, spinning wheels, growing plants, lights, arrows.
10. The star of each step must be BIG: at least 110 px on screen (an emoji of size 120 at zoom 1.0, or size 70 at zoom 1.7), near the centre, and in the middle of the screen height (not under the caption at the top).
11. No clutter: objects never sit on top of each other; scenery (trees) stays away from the action. 22 to 34 parts in total. Write compact JSON.
12. Motion words: to make something jiggle or shake give it "bob" (3 to 10); to turn give "rot" keyframes (degrees); to travel give x and y keyframes; to grow give "size" or "scale" keyframes. Only wheel and pump have "spin".
14. COMMON MISTAKES that make the checker reject a scene (seen in real runs; avoid them the first time):
   - colours ("fill", "stroke", "color") are text like "#7fb2d9", never numbers or keyframes; "lw" is a plain number.
   - the part named in "shows" must have keyframes that CHANGE inside that step's own time, in every step including the last one.
   - fields that a part type does not list do nothing (an emoji has no "spin": use "rot" keyframes or "bob").
   - two objects must not sit on top of each other unless one has "inside": "<container id>".
13. Emoji must show EXACTLY the thing meant. A whole corn cob is not a kernel; a pan with an egg is not an empty pan. If no emoji is exact, draw the thing yourself with path, ellipse, circle, rect and poly (for example a kernel = a yellow ellipse; a cut-away = an outline with the inside drawn in). Things that travel get x and y keyframes (or an orbit). Use particles for fire, smoke, steam, sparks, bubbles, dust.

Return JSON with keys: "title", "principle", "duration": {DURATION}, "music": {{"bpm": 118}}, "flows", "steps", "camera", "sfx", "parts".

{('One finished example for a DIFFERENT topic shows the format and the level of care. Do not copy its layout or sentences: ' + ex) if with_example else ''}"""

def tidy(spec, plan=None):
    """Small safe repairs that do not change the idea: exact step times, duration, music, and the plan's own sentences."""
    if not isinstance(spec, dict): return spec
    spec['duration'] = DURATION
    if not isinstance(spec.get('music'), dict): spec['music'] = {'bpm': 118}
    st = spec.get('steps')
    if isinstance(st, list) and len(st) == len(TIMES):
        for i, (s, (a, b)) in enumerate(zip(st, TIMES)):
            if isinstance(s, dict):
                s['start'], s['end'] = a, b; s.pop('caption', None); s.pop('change', None)
                if plan and isinstance(plan.get('steps'), list) and len(plan['steps']) == len(TIMES):
                    for k in ('label', 'say'): s[k] = plan['steps'][i][k]
    st_ = (plan or {}).get('setting') if plan else None; parts = spec.get('parts')
    if isinstance(st_, dict) and isinstance(parts, list) and parts and isinstance(parts[0], dict) and parts[0].get('type') == 'sky':
        parts[0]['preset'] = st_.get('preset', 'day')
        for k in ('hills', 'clouds', 'sun'): parts[0].pop(k, None)
        indoors = st_.get('preset') not in OUTDOORS
        keep = []
        for q in parts:
            if isinstance(q, dict) and q.get('type') == 'ground':
                if st_.get('ground') == 'none': continue
                q['kind'] = st_.get('ground', 'grass')
            if isinstance(q, dict) and q.get('type') == 'tree' and indoors: continue      # no trees in a kitchen, in space or inside a body
            keep.append(q)
        spec['parts'] = keep
    for q in spec.get('parts', []) if isinstance(spec.get('parts'), list) else []:
        if isinstance(q, dict) and q.get('type') in CATALOG:
            req, opt, _ = CATALOG[q['type']]
            sp = q.get('spin')
            if 'spin' not in req and 'spin' not in opt and sp is not None and 'rot' in opt and 'rot' not in q:   # e.g. a spinning emoji: make it really turn
                speed = sp if isinstance(sp, (int, float)) else max([k[1] for k in sp if isinstance(k, list) and len(k) == 2] or [0])
                if speed: q['rot'] = [[0, 0], [DURATION, round(min(abs(speed), 9) * 240)]]
            for k in [k for k in q if k not in req and k not in opt and k not in ('type', 'id', 'inside')]:
                q.pop(k); spec.setdefault('_dropped', []).append('a %s part%s had "%s", which %s parts do not have, so it did nothing; allowed fields: %s' % (q['type'], ' "%s"' % q['id'] if q.get('id') else '', k, q['type'], ', '.join(req + opt)))
    if plan:
        for k in ('title', 'principle'):
            if isinstance(plan.get(k), str): spec.setdefault(k, plan[k])
    return spec

EXTRA = [('GEMINI_API_KEY', 'https://generativelanguage.googleapis.com/v1beta/openai', ('gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash', 'gemini'))]

def _call(llm, prompt, temp, turn, log):
    """Ask the free LLM services one at a time, starting with a different one each turn, and report why each one failed."""
    provs = [p for p in llm.PROVIDERS + EXTRA if os.environ.get(p[0], '').strip()]; saved = llm.PROVIDERS; why = []
    if not provs: raise ValueError('no free LLM key is configured')
    try:
        for p in provs[turn % len(provs):] + provs[:turn % len(provs)]:
            llm.PROVIDERS = [p]
            try: return llm.json_call(SYS, prompt, temperature=temp, max_tokens=5200)
            except Exception as e: why.append(str(e)[:110].replace('llm.py: ', ''))
    finally: llm.PROVIDERS = saved
    raise ValueError(' ; '.join(why))

def _ask(llm, prompt, checker, tries, temp, log, name, post=lambda x: x, repair_prompt=None):
    out = None; errs = None; turn = 0; k = 0; waits = 0
    while k < tries:
        base = prompt if (not errs or out is None or not repair_prompt) else repair_prompt
        p = base if (not errs or out is None) else base + '\n\nYOUR LAST ANSWER HAD THESE PROBLEMS. Fix every one, keep what was good, and return the full corrected JSON:\n' + '\n'.join('- ' + e for e in errs[:30]) + '\n\nYour last answer was:\n' + json.dumps(out, separators=(',', ':'), ensure_ascii=False)[:13000]
        try: got = _call(llm, p, temp if k == 0 else 0.35, turn, log)
        except Exception as e:
            waits += 1; turn += 1
            if waits > 10: raise SystemExit('REJECTED: the free LLM services kept refusing (%s). No video was made.' % str(e)[:200])
            log('%s: no free LLM answered (%s); waiting 60 s (wait %d of 10, does not use up a try)' % (name, str(e)[:260], waits)); time.sleep(60); continue
        k += 1
        try: out = post(got)
        except Exception as e: log('%s try %d: unusable answer (%s)' % (name, k, str(e)[:120])); errs = ['the answer was not a valid scene object']; continue
        errs = checker(out)
        if errs and isinstance(out, dict) and out.get('_dropped'): errs = errs + sorted(set(out['_dropped']))[:6]
        if isinstance(out, dict): out.pop('_dropped', None)
        log('%s try %d: %s' % (name, k, 'PASSED' if not errs else '%d problems: %s' % (len(errs), ' | '.join(errs[:8]))))
        if not errs: return out
    raise SystemExit('REJECTED: the %s could not pass the checker after %d tries. No video was made.' % (name, tries))

def review(llm, plan, spec, log):
    """A second look, like a director: is every emoji exactly the right picture, and is every sentence punchy? Only safe, small edits are applied, and only if the scene still passes the checker."""
    emo = [(i, p) for i, p in enumerate(spec['parts']) if p.get('type') == 'emoji']
    what = {c['id']: c.get('what', '') for c in plan.get('cast', []) if isinstance(c, dict) and 'id' in c}
    prompt = f"""You are the director reviewing an animated explainer before it is made.
PRINCIPLE: {spec.get('principle', '')}
SENTENCES (spoken, in order): {json.dumps([s['say'] for s in spec['steps']], ensure_ascii=False)}
EMOJI USED AS OBJECTS: {json.dumps([{'n': i, 'emoji': p['char'], 'meant_to_be': what.get(p.get('id'), p.get('id', 'scenery'))} for i, p in emo], ensure_ascii=False)}

1. For each emoji: does it show EXACTLY the thing it is meant to be? If a clearly better, very common emoji exists (one that has been on every phone for years), give it. If the emoji is right, or nothing better exists, leave it out of your answer.
2. Rewrite the 7 sentences to be punchier: same facts, same order, 8 to 13 plain words each, strong action verbs, spoken like an excited friend. Sentence 1 stays a question. At least 5 end with "!".
Return JSON: {{"emoji": [{{"n": number, "better": "one emoji"}}], "say": ["7 sentences"]}}"""
    try: r = _call(llm, prompt, 0.6, 1, log)
    except Exception as e: log('review: skipped (%s)' % str(e)[:120]); return spec
    new = json.loads(json.dumps(spec)); n_e = n_s = 0
    for f in r.get('emoji', []) if isinstance(r.get('emoji'), list) else []:
        if isinstance(f, dict) and isinstance(f.get('n'), int) and 0 <= f['n'] < len(new['parts']) and new['parts'][f['n']].get('type') == 'emoji' and isinstance(f.get('better'), str) and 1 <= len(f['better']) <= 8 and any(ord(ch) > 127 for ch in f['better']) and f['better'] != new['parts'][f['n']]['char']:
            log('review: emoji %s -> %s' % (new['parts'][f['n']]['char'], f['better'])); new['parts'][f['n']]['char'] = f['better']; n_e += 1
    say = r.get('say')
    if isinstance(say, list) and len(say) == len(new['steps']):
        for s, t in zip(new['steps'], say):
            if isinstance(t, str) and 6 <= len(t.split()) <= 13 and t.strip() != s['say']: s['say'] = t.strip(); n_s += 1
        if '?' not in new['steps'][0]['say']: new['steps'][0]['say'] = spec['steps'][0]['say']
    errs = check(new)
    if errs: log('review: edits dropped because the scene would no longer pass (%s)' % errs[0][:120]); return spec
    log('review: %d emoji fixed, %d sentences sharpened' % (n_e, n_s)); return new

def write_scene(topic, log=print):
    import llm
    plan = _ask(llm, plan_prompt(topic), check_plan, 5, 0.9, log, 'plan')
    log('principle: ' + plan['principle']); log('cast: ' + ', '.join('%s (%s)' % (c['id'], c.get('what', '')) for c in plan['cast']))
    spec = _ask(llm, stage_prompt(topic, plan), check, 8, 0.5, log, 'scene', post=lambda s: tidy(s, plan), repair_prompt=stage_prompt(topic, plan, with_example=False))
    safe = json.loads(json.dumps(spec)); spec = review(llm, plan, spec, log)
    return plan, spec, safe

if __name__ == '__main__':
    if len(sys.argv) < 4 or sys.argv[1] != '--topic-file': raise SystemExit(__doc__)
    topic = re.sub(r'\s+', ' ', Path(sys.argv[2]).read_text().splitlines()[0]).strip()[:200]
    if len(topic) < 8: raise SystemExit('the topic is too short')
    lines = ['topic: ' + topic]
    def log(m): print(m, flush=True); lines.append(m)
    try:
        plan, spec, safe = write_scene(topic, log=log)
        Path(sys.argv[3]).write_text(json.dumps(spec, indent=1, ensure_ascii=False)); Path('auto-plan.json').write_text(json.dumps(plan, indent=1, ensure_ascii=False))
        Path('auto-scene-safe.json').write_text(json.dumps(safe, indent=1, ensure_ascii=False))   # the scene before the review, used if a reviewed emoji cannot be drawn
        log('title: %s | %d parts | %d sounds' % (spec['title'], len(spec['parts']), len(spec.get('sfx', []))))
    finally:
        Path('writer-log.txt').write_text('\n'.join(lines) + '\n')
