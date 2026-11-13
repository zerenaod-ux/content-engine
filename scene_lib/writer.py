"""THE WRITER: turns a topic into a full scene description, working the way a careful human designer does, with the free LLMs.
  1. PLAN  - find the cause (principle), the chain of cause and effect, the cast of objects and where each one stands, and topic-specific beats with declared demonstrations.
  2. STAGE - turn the plan into the exact scene description (parts, keyframes, camera, sounds).
  3. CHECK - the checker applies structural design checks (physics heuristics, connections, camera, labels, numeric demonstration contracts). Problems go back to the writer to fix.
A description that still fails after the tries is rejected: no video is made from it.
  python3 scene_lib/writer.py --topic-file topic.txt out.json        (needs the free LLM keys in the environment)"""
import json, os, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scene_lib.catalog import CATALOG, catalog_text, SOUNDS_DUR, SOUNDS_FREQ, SOUNDS_PLAIN, PRESETS, GROUNDS
OUTDOORS = {'day', 'dusk', 'night', 'desert', 'snow'}
from scene_lib.validate import check

# Legacy fixtures retain their original timings; new plans choose their own beats.
DURATION = 55.4

def timeline(plan):
    t = 0.3; out = []
    for step in plan['steps']:
        end = round(t + step['seconds'], 2)
        out.append((t, end)); t = round(end + 0.2, 2)
    return out

SYS = 'You are a brilliant science animator and scene designer. You answer with ONE JSON object and nothing else.'
STAGE_TEXT = 'x goes right, y goes up. If there is ground, its surface is y=0 and things below 0 are underground. Keep everything between x=-380 and x=700 and between y=-220 and y=420. Objects are about 60 to 300 units big.'

def _num(v): return isinstance(v, (int, float)) and not isinstance(v, bool)

def plan_prompt(topic, lessons=""):
    context = "\nObserved prior attempts (diagnostics, not verified scientific facts):\n" + lessons if lessons else ""
    return f"""TOPIC: {topic}{context}

You will plan a {int(DURATION)}-second animated explainer with topic-appropriate composition: closeups, cutaways and transitions where useful. Choose a clear visual explanation rather than a fixed formula.
Work like a careful designer. Think in this order:

1. PRINCIPLE: establish the actual mechanism before designing pictures. State limitations and common misconceptions. Add "basis": {{"status":"model_knowledge_unverified", "limitations":"what is simplified or uncertain"}}. Do not invent citations or claim external fact verification. If uncertain, choose a simpler defensible explanation.
2. CHAIN: 5 to 7 links of cause and effect, in the order they happen ("because A, B happens").
3. CAST: 4 to 8 objects the viewer must see. ANY topic can be drawn: "emoji" gives any recognisable object (animal, organ, planet, vehicle, tool, food, person, building), "path" draws any custom shape, and there are ready parts for water, pipes, wires, wheels, particles (fire, smoke, steam, sparks, bubbles, snow), meters and more. All part types: {', '.join(CATALOG)}.
   Also choose the SETTING that truly fits the topic: where it really happens. A kitchen, home or workshop topic is indoors: preset "clean" or "lab" with ground "floor" (no hills, no trees). Space has no ground. Only use outdoor presets for things that happen outdoors.
   The STAR of the video (the thing the topic is about) must be drawn LARGE and, when the secret is inside it, shown as a cut-away so the viewer sees inside.
4. LAYOUT: give every cast member a box on the stage: x0, x1, y0, y1. Stage: {STAGE_TEXT}
   - The layout must SHOW the principle. If gravity matters, the source is physically higher than where the water ends up. If something is underground, it is below y=0.
   - Arrange objects to explain the mechanism; use a closeup when the process is too small.
   - Solid machines and buildings stand on dry ground, never inside water. Boxes of different objects must not overlap (a pipe or wire joins them).
   - EXCEPT things that truly sit inside another thing (clothes in a drum, a seed in a fruit, a piston in a cylinder): give them "inside": "<id of the container>" and place their box inside the container's box. Draw the container as a cut-away so the inside is seen.
5. STEPS: choose 5 to 12 beats to suit this topic. Give each "seconds" for its spoken sentence and demonstration; total scene including 0.2-second gaps and 0.6-second padding must be 45-65 seconds.
   - "say": 4 to 18 plain words, natural spoken language. Questions and exclamations are optional. Do not exaggerate the science for excitement.
   - Each sentence must have a concrete visible demonstration, not decorative motion. Add "demonstration": describe what the viewer should observe, and "change": the physical change that supports this claim. Distinguish an illustrative diagram from a literal view. When comparing distinct colours, paths or states, add "contrasts": [{{"parts":["part1","part2"],"fields":["color","pts"]}}] naming ALL required separate parts and their distinguishing fields. Leave [] when no comparison is needed. These requirements must be retained in the scene, not invented after staging.
   - True, general facts only. No numbers you are not sure of. No medical or money advice.
   - Be creative: choose a surprising, concrete angle, not a textbook definition.

Return JSON:
{{"title": "starts with How or Why, 4-8 words, ends with ONE emoji",
 "principle": "...", "basis": {{"status":"model_knowledge_unverified", "limitations":"..."}},
 "style": "flow" (mostly water, pipes, machines) or "icons" (living things, body, space, objects, ideas),
 "setting": {{"preset": "day|dusk|night|desert|snow|space|ocean|body|lab|clean", "ground": "grass|sand|snow|rock|seabed|floor|none"}},
 "chain": ["...", "..."],
 "cast": [{{"id": "shortname", "what": "what it is", "built_from": "part types", "x0": 0, "x1": 0, "y0": 0, "y1": 0, "inside": "optional container id"}}],
 "steps": [{{"label": "2-16 letters", "say": "...", "shows": "cast id", "change": "what physically changes", "demonstration":"what visibly supports this sentence", "seconds": 6.0}}]}}"""

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
    if not isinstance(st, list) or not 5 <= len(st) <= 12: E.append('steps must have 5 to 12 beats'); st = []
    if not isinstance(pl.get('basis'), dict) or pl['basis'].get('status') != 'model_knowledge_unverified' or not pl['basis'].get('limitations'): E.append('basis must disclose model_knowledge_unverified and limitations')
    if st and all(isinstance(x, dict) and _num(x.get('seconds')) for x in st):
        if any(x['seconds'] < 1.5 for x in st) or not 45 <= timeline(pl)[-1][1] + 0.3 <= 65: E.append('beat timings must total 45-65 seconds, each at least 1.5 seconds')
    else: E.append('each beat needs numeric seconds')
    for i, s in enumerate(st, 1):
        if not isinstance(s, dict): E.append('step %d must be an object' % i); continue
        if s.get('shows') not in ids: E.append('step %d: "shows" must be one of the cast ids' % i)
        w = len(str(s.get('say', '')).split())
        if not 4 <= w <= 18: E.append('step %d: say must have 4 to 18 words' % i)
        if not isinstance(s.get('demonstration'), str) or len(s['demonstration'].split()) < 4: E.append('step %d needs an observable demonstration' % i)
        contrasts=s.get('contrasts', [])
        if not isinstance(contrasts,list) or any(not isinstance(c,dict) or not isinstance(c.get('parts'),list) or len(c['parts']) < 2 or not all(isinstance(id,str) for id in c['parts']) or not isinstance(c.get('fields'),list) or not c['fields'] for c in contrasts): E.append('step %d: contrasts need separate part ids and distinguishing fields' % i)
        if not isinstance(s.get('label'), str) or not 2 <= len(s['label']) <= 16: E.append('step %d: label must be 2 to 16 letters' % i)
    return E

def stage_prompt(topic, plan, with_example=True):
    ex = (ROOT / 'scene_lib' / ('example_icons.json' if plan.get('style') == 'icons' else 'example_flow.json')).read_text() if with_example else ''
    times = timeline(plan); duration = round(times[-1][1] + 0.3, 2)
    return f"""TOPIC: {topic}

Here is the approved PLAN. Now build the exact scene description from it.
{json.dumps(plan, ensure_ascii=False)}

STAGE: {STAGE_TEXT}
Parts are drawn in list order (later parts cover earlier ones): sky first (with the preset from the plan's setting), then scenery, ground (if any), the main objects, labels last.

PARTS YOU MAY USE (only these). Use "emoji" for any recognisable object and "path" to draw custom shapes; never leave a main subject as a plain box:
{catalog_text()}
Any part may have an "id". Give every cast member's main part the same id as in the plan. A part that sits inside another gets "inside": "<container id>".

ANIMATION: any number field can be a fixed number or keyframes [[time, value], ...]. The value holds before the first and after the last keyframe and moves smoothly between.

STEPS: copy the steps from the plan (label, say, shows) and use exactly these times: {', '.join('step %d: %.2f-%.2f' % (i + 1, a, b) for i, (a, b) in enumerate(times))}.

DESIGN GUIDANCE:
- Each step copies "demonstration" from the plan and adds "evidence": [{{"part":"id", "field":"progress", "at":[start,end], "values":[0,1]}}]. These are actual numeric values at those times, not guesses. Map every indispensable part of the narrated mechanism. Copy the plan contrasts exactly; every member needs evidence and distinct values for the declared fields. Use physical changes rather than decorative jiggling; alpha may be used only for an explanatory reveal. Distinct paths must be separately visible in position and colour. Numeric and visibility checks cannot establish scientific truth.
- Camera is computed from the focus and all evidence parts. Keep these close enough to read together; the focus needs at least 110 screen pixels (thin paths 45). Give a placeholder camera spanning the whole duration; the system replaces it. Labels must not cover the demonstration.
- Real-looking objects: use a matching detailed prop when available; otherwise an exact icon/emoji or detailed path. Simple shapes may make supporting details. No wrong stand-in images. Show internal mechanisms with a cutaway. A diagram must depict the causal relationship, not unrelated movement.
- Real layout: gravity water flows down; pressure/pump may lift it. For every pipe/stream include flows: [{{"from":[x,y],"to":[x,y],"by":"gravity|pressure|pump"}}]. Pipes/wires touch endpoints or leave the stage. Solids stand on dry ground; water has a container or ground. Objects only overlap when physically appropriate; declare inside for contents.
- Brief labels: at most two together, show keyframes fade each in/out. Text fields <=12 characters; label text <=16. Use only fields in the catalog. Colours are fixed strings and line widths plain numbers. Use rot for rotation, x/y for travel.
- Sound cues [time,name,gain,optional_value] should support the action, not dictate pacing. Duration sounds: {', '.join(sorted(SOUNDS_DUR))}; pitch sounds: {', '.join(sorted(SOUNDS_FREQ))}; plain: {', '.join(sorted(SOUNDS_PLAIN))}. Music stays at the existing default. Use 8–70 parts as required by the rendering schema.

Return JSON with keys: "title", "principle", "evidence_version": 1, "basis" (copy the plan), "duration": {duration}, "music": {{"bpm": 118}}, "flows", "steps", "camera", "sfx", "parts".

{('One finished example for a DIFFERENT topic shows the format and the level of care. Do not copy its layout or sentences: ' + ex) if with_example else ''}"""

def auto_camera(spec):
    """AUTO_CAMERA: the camera is worked out from the scene itself, not guessed by the writer: each step frames its star (the part named in "shows")
    so it is big, centred and fully in the picture (tall things like a wind turbine are not cut off); it starts and ends on a wide view of everything."""
    from scene_lib.validate import _box_at, SCENERY
    parts = [p for p in spec.get('parts', []) if isinstance(p, dict)]; ids = {p['id']: p for p in parts if isinstance(p.get('id'), str)}
    def frame(bx):
        w = max(40, bx[1] - bx[0]); h = max(40, bx[3] - bx[2]); z = max(0.55, min(3.0, 430 / w, 600 / h))
        cx = (bx[0] + bx[1]) / 2; cy = (bx[2] + bx[3]) / 2
        return round(cx, 1), round(cy - 60 / z, 1), round(z, 2)
    main = [p for p in parts if p.get('type') not in SCENERY + ('sky', 'night', 'particles')]
    bxs = []
    for p in main:
        try: bxs.append(_box_at(p, spec['duration'] / 2, spec.get('_path_bounds')))
        except Exception: pass
    if not bxs: return
    wide = frame((min(b[0] for b in bxs), max(b[1] for b in bxs), min(b[2] for b in bxs), max(b[3] for b in bxs)))
    cam = [[0] + list(wide)]
    for st in spec.get('steps', []):
        p = ids.get(st.get('shows'))
        if not p: continue
        a, b = st['start'], st['end']
        try:
            focus = [p] + [ids[e['part']] for e in st.get('evidence', []) if isinstance(e, dict) and e.get('part') in ids]
            bs = [_box_at(q, a + (b - a) * k / 4, spec.get('_path_bounds')) for q in focus for k in range(5)]   # a moving star: keep its whole path in the picture
            f = frame((min(q[0] for q in bs), max(q[1] for q in bs), min(q[2] for q in bs), max(q[3] for q in bs)))
        except Exception: continue
        # A wide explanatory diagram may focus on a path rather than a tiny
        # object at its endpoint. Prefer an actual declared evidence part that
        # is legible in this same composition; narration/claims are unchanged.
        try:
            focus_box = _box_at(p, (a+b)/2, spec.get('_path_bounds'))
            from scene_lib.validate import THIN
            need = 45 if p.get('type') in THIN else 110
            if max(focus_box[1]-focus_box[0],focus_box[3]-focus_box[2])*f[2] < need:
                choices=[]
                for ev in st.get('evidence',[]):
                    q=ids.get(ev.get('part'))
                    if q is None: continue
                    box=_box_at(q,(a+b)/2,spec.get('_path_bounds'))
                    extent=max(box[1]-box[0],box[3]-box[2])*f[2]
                    required=45 if q.get('type') in THIN else 110
                    if extent>=required: choices.append((extent,q['id']))
                if choices:
                    previous=st['shows'];st['shows']=max(choices)[1]
                    spec.setdefault('_focus_repairs',[]).append({'from':previous,'to':st['shows'],'step':len(cam)//2+1})
        except (TypeError,KeyError): pass
        if p.get('type') in ('night',): f = wide
        cam.append([round(a + 0.6, 2)] + list(f)); cam.append([round(b - 0.2, 2)] + list(f))
    cam.append([spec['duration']] + list(wide))
    out = []
    for c in cam:
        if out and c[0] <= out[-1][0] + 0.05: continue
        out.append(c)
    spec['camera'] = out

def tidy(spec, plan=None):
    """Small safe repairs that do not change the idea: exact step times, duration, music, and the plan's own sentences."""
    if not isinstance(spec, dict): return spec
    times = timeline(plan) if plan else [(s['start'], s['end']) for s in spec.get('steps', [])]
    if plan: spec['duration'] = round(times[-1][1] + 0.3, 2)
    if not isinstance(spec.get('music'), dict): spec['music'] = {'bpm': 118}
    st = spec.get('steps')
    if isinstance(st, list) and len(st) == len(times):
        for i, (s, (a, b)) in enumerate(zip(st, times)):
            if isinstance(s, dict):
                s['start'], s['end'] = a, b; s.pop('caption', None)
                if plan:
                    for k in ('label', 'say', 'shows', 'demonstration'): s[k] = plan['steps'][i][k]
                    s['contrasts'] = plan['steps'][i].get('contrasts', [])
    if plan:
        spec['basis'] = plan['basis']; spec['evidence_version'] = 1
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
                if speed: q['rot'] = [[0, 0], [spec['duration'], round(min(abs(speed), 9) * 240)]]
            for k in [k for k in q if k not in req and k not in opt and k not in ('type', 'id', 'inside')]:
                q.pop(k); spec.setdefault('_dropped', []).append('a %s part%s had "%s", which %s parts do not have, so it did nothing; allowed fields: %s' % (q['type'], ' "%s"' % q['id'] if q.get('id') else '', k, q['type'], ', '.join(req + opt)))
    try: auto_camera(spec)
    except Exception: pass
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
            except llm.BudgetExceeded: raise
            except Exception as e: why.append(str(e)[:110].replace('llm.py: ', ''))
    finally: llm.PROVIDERS = saved
    raise ValueError(' ; '.join(why))

def _ask(llm, prompt, checker, tries, temp, log, name, post=lambda x: x, repair_prompt=None):
    out = None; errs = None; turn = 0; k = 0; waits = 0
    while k < tries:
        base = prompt if (not errs or out is None or not repair_prompt) else repair_prompt
        p = base if (not errs or out is None) else base + '\n\nYOUR LAST ANSWER HAD THESE PROBLEMS. Fix every one, keep what was good, and return the full corrected JSON:\n' + '\n'.join('- ' + e for e in errs[:30]) + '\n\nYour last answer was:\n' + json.dumps(out, separators=(',', ':'), ensure_ascii=False)[:13000]
        try: got = _call(llm, p, temp if k == 0 else 0.35, turn, log)
        except llm.BudgetExceeded as e: raise SystemExit(str(e))
        except Exception as e:
            waits += 1; turn += 1
            if waits > 1: raise SystemExit('REJECTED: the free LLM services kept refusing (%s). No video was made.' % str(e)[:200])
            log('%s: no free LLM answered (%s); waiting 10 s (wait %d of 1)' % (name, str(e)[:260], waits)); time.sleep(10); continue
        k += 1
        try: out = post(got)
        except Exception as e: log('%s try %d: unusable answer (%s)' % (name, k, str(e)[:120])); errs = ['the answer was not a valid scene object']; continue
        errs = checker(out)
        from scene_lib.pipeline import save_attempt
        save_attempt(name, out, errs)
        if errs and isinstance(out, dict) and out.get('_dropped'): errs = errs + sorted(set(out['_dropped']))[:6]
        if isinstance(out, dict): out.pop('_dropped', None)
        log('%s try %d: %s' % (name, k, 'PASSED' if not errs else '%d problems: %s' % (len(errs), ' | '.join(errs[:8]))))
        if not errs: return out
    raise SystemExit('REJECTED: the %s could not pass the checker after %d tries. No video was made.' % (name, tries))

def write_scene(topic, log=print):
    import llm
    from scene_lib.pipeline import StageCache
    from scene_lib.ideas import load, words
    relevant=[h for h in load() if words(topic) & words(h.get('topic',''))]
    lessons=json.dumps([{'topic':h.get('topic'), 'failed':h.get('failed',False), 'failure_cause':h.get('failure_cause',''), 'observed_techniques':h.get('techniques',[])} for h in relevant[-4:]],ensure_ascii=False)[:1800] if relevant else ''
    cache = StageCache(topic + lessons)
    plan = cache.accepted('plan', check_plan)
    if plan is None:
        plan = _ask(llm, plan_prompt(topic, lessons), check_plan, 3, 0.9, log, 'plan')
        cache.save('plan', plan)
    log('principle: ' + plan['principle']); log('cast: ' + ', '.join('%s (%s)' % (c['id'], c.get('what', '')) for c in plan['cast']))
    spec = cache.accepted('scene', check)
    if spec is None:
        spec = _ask(llm, stage_prompt(topic, plan), check, 4, 0.5, log, 'scene', post=lambda s: tidy(s, plan), repair_prompt=stage_prompt(topic, plan, with_example=False))
        cache.save('scene', spec)
    safe = json.loads(json.dumps(spec)); log('review: narration preserved so claim mapping stays intact')
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
