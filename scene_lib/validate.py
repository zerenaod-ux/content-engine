"""Checks a scene description before any video is made. Returns a list of plain-language problems (empty list = good).
  python3 scene_lib/validate.py scenes/<name>.json"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import re
from scene_lib.catalog import CATALOG, ANIM, POINT_LISTS, POINTS, SOUNDS, SOUNDS_DUR, SOUNDS_FREQ, PRESETS, GROUNDS, PARTICLES

def _num(v): return isinstance(v, (int, float)) and not isinstance(v, bool)
def _kfs(v): return isinstance(v, list) and len(v) > 0 and all(isinstance(k, list) and len(k) == 2 and _num(k[0]) and _num(k[1]) for k in v)
def _pt(v): return isinstance(v, list) and len(v) == 2 and _num(v[0]) and _num(v[1])

def _at(v, t, d=0.0):
    if _num(v): return v
    if not _kfs(v): return d
    if t <= v[0][0]: return v[0][1]
    for a, b in zip(v, v[1:]):
        if t <= b[0]: return a[1] + (b[1] - a[1]) * (t - a[0]) / max(1e-6, b[0] - a[0])
    return v[-1][1]

def _where(p):
    """Rough position of a part, for the camera check."""
    if 'pts' in p and isinstance(p['pts'], list) and p['pts'] and _pt(p['pts'][0]): xs = [q[0] for q in p['pts'] if _pt(q)]; ys = [q[1] for q in p['pts'] if _pt(q)]; return min(xs), max(xs), min(ys), max(ys)
    if 'x0' in p: return p.get('x0', 0), p.get('x1', 0), p.get('y0', 0), _at(p.get('level'), 1e9, p.get('y0', 0))
    if 'from' in p and _pt(p.get('from')) and _pt(p.get('to')): return min(p['from'][0], p['to'][0]), max(p['from'][0], p['to'][0]), min(p['from'][1], p['to'][1]), max(p['from'][1], p['to'][1])
    x = _at(p.get('x'), 0, 0); y = _at(p.get('y'), 0, 0)
    if p.get('type') == 'tower': return x - 90, x + 90, y, y + p.get('legH', 240) + p.get('h', 130)
    return x, x + (_at(p.get('w'), 0, 0) if p.get('type') in ('rect', 'house') else 0), y, y + (_at(p.get('h'), 0, 0) if p.get('type') in ('rect', 'house') else 0)

SOLID = ('wheel', 'pump', 'house', 'tower')
SCENERY = ('sky', 'ground', 'label', 'arrow', 'night', 'glow', 'tree', 'plant')
THIN = ('pipe', 'wire', 'line', 'stream', 'spray', 'particles', 'arrow', 'label', 'text', 'circle', 'glow', 'bar', 'plant')
OBJECTS = ('emoji', 'house', 'tower', 'wheel', 'pump', 'tree')

def _box(p):
    """Bounding box (x0, x1, y0, y1) of a part at its largest."""
    t = p.get('type'); x = _at(p.get('x'), 1e9, 0); y = _at(p.get('y'), 1e9, 0)
    if t in ('wheel', 'pump', 'circle', 'glow'): r = _at(p.get('r'), 1e9, 40 if t == 'wheel' else 20 if t == 'pump' else 60 if t == 'glow' else 10); return x - r, x + r, y - r, y + r
    if t == 'house': return x, x + p.get('w', 170), y, y + p.get('h', 140) + 70
    if t == 'tower': return x - p.get('w', 170) / 2, x + p.get('w', 170) / 2, y, y + p.get('legH', 240) + p.get('h', 130) + 46
    if t == 'rect':
        ys = [k[1] for k in p['y']] if _kfs(p.get('y')) else [y]; xs = [k[1] for k in p['x']] if _kfs(p.get('x')) else [x]
        return min(xs), max(xs) + _at(p.get('w'), 1e9, 10), min(ys), max(ys) + _at(p.get('h'), 1e9, 10)
    if t == 'water':
        lv = [k[1] for k in p['level']] if _kfs(p.get('level')) else [p.get('level', p.get('y0', 0))]; return p.get('x0', 0), p.get('x1', 0), p.get('y0', 0), max(lv)
    if t in ('tree', 'plant'): s_ = p.get('s', 1); return x - 30 * s_, x + 30 * s_, y, y + (110 if t == 'tree' else 50) * s_
    if t in ('stream',): return x - 6, x + 6, min(_at(p.get('y0'), 0, 0), p.get('y1', 0)), p.get('y1', 0)
    if t == 'spray': return x - 20, x + 260, p.get('floor', 0), y + 120
    return _where(p)

def _box_at(p, t):
    """Where a part is at time t (for parts that travel)."""
    ty = p.get('type')
    if ty in ('emoji', 'path', 'ellipse', 'circle', 'particles', 'text', 'glow'):
        o = p.get('orbit')
        if isinstance(o, dict) and all(_num(o.get(k)) for k in ('cx', 'cy', 'rx')):
            a = (t / max(1, o.get('period', 6)) + o.get('phase', 0)) * 2 * math.pi; x = o['cx'] + o['rx'] * math.cos(a); y = o['cy'] + o.get('ry', o['rx']) * math.sin(a)
        else: x = _at(p.get('x'), t, 0); y = _at(p.get('y'), t, 0)
        h = {'emoji': _at(p.get('size'), t, 80) / 2, 'path': 55 * _at(p.get('scale'), t, 1), 'ellipse': max(_at(p.get('rx'), t, 40), _at(p.get('ry'), t, 20)), 'circle': _at(p.get('r'), t, 10), 'particles': 45, 'text': 40, 'glow': p.get('r', 60)}[ty]
        return x - h, x + h, y - h, y + h
    if ty == 'bar': return p.get('x', 0), p.get('x', 0) + p.get('w', 26), p.get('y', 0), p.get('y', 0) + p.get('h', 160)
    return _box(p)

def _near(pt, box, tol):
    return box[0] - tol <= pt[0] <= box[1] + tol and box[2] - tol <= pt[1] <= box[3] + tol

def design_rules(spec, D, steps, cam, parts):
    """The design logic a careful human follows, written as checks: the picture must make physical sense and must prove each sentence."""
    E = []; good = [p for p in parts if isinstance(p, dict) and p.get('type') in CATALOG]
    ids = {}
    for p in good:
        if 'inside' in p and not isinstance(p['inside'], str): E.append('"inside" must be the id of the container part')
        if 'id' in p:
            if not isinstance(p['id'], str) or p['id'] in ids: E.append('part ids must be unique short names (problem with %r)' % (p.get('id'),))
            else: ids[p['id']] = p
    if not isinstance(spec.get('principle'), str) or len(spec['principle'].split()) < 8: E.append('add "principle": one or two sentences saying WHY it works (the cause), before designing anything')
    gy = next((_at(p.get('y'), 0, 0) for p in good if p['type'] == 'ground'), None)
    waters = [p for p in good if p['type'] == 'water']
    def changes_in(p, a, b):
        if isinstance(p.get('orbit'), dict): return True
        if _num(p.get('bob')) and p['bob'] >= 2: return True          # keeps jiggling the whole time
        if p.get('type') in ('wheel', 'pump') and _num(p.get('spin')) and p['spin'] > 0: return True
        for f, v in p.items():
            if f in ANIM and _kfs(v) and len({k[1] for k in v}) > 1:
                for k0, k1 in zip(v, v[1:]):
                    if k0[1] != k1[1] and k0[0] < b and k1[0] > a: return True
        return False
    def view(t):
        cx = _at([[c[0], c[1]] for c in cam], t); cy = _at([[c[0], c[2]] for c in cam], t); z = _at([[c[0], c[3]] for c in cam], t)
        return cx - 360 / z, cx + 360 / z, cy - 520 / z, cy + 500 / z, z
    # rule: every sentence is proved by one named part that visibly changes while the camera looks at it
    for i, s in enumerate(steps, 1):
        if not (isinstance(s, dict) and _num(s.get('start')) and _num(s.get('end'))): continue
        sh = s.get('shows')
        if sh not in ids: E.append('step %d: "shows" must be the id of the part that proves this sentence on screen' % i); continue
        p = ids[sh]; a, b = s['start'] - 0.3, s['end']
        if i > 1 and not changes_in(p, a, b): E.append('step %d: part "%s" does not change during %.1f-%.1f; give it keyframes inside this step so the viewer sees the sentence happen' % (i, sh, s['start'], s['end']))
        if cam and p['type'] not in ('night', 'sky', 'ground'):
            need = 45 if p['type'] in THIN else 110; hit = big = mid = clear = False
            for tt in (s['start'] + 0.35 * (s['end'] - s['start']), s['start'] + 0.7 * (s['end'] - s['start'])):
                vx0, vx1, vy0, vy1, z = view(tt); bx = _box_at(p, tt); cx = (bx[0] + bx[1]) / 2; cy = (bx[2] + bx[3]) / 2
                if bx[1] >= vx0 + 20 / z and bx[0] <= vx1 - 20 / z and bx[3] >= vy0 and bx[2] <= vy1: hit = True
                else: continue
                if max(bx[1] - bx[0], bx[3] - bx[2]) * z >= need: big = True
                span = (bx[1] - bx[0]) / 2
                if vx0 + 0.18 * (vx1 - vx0) - span <= cx <= vx1 - 0.18 * (vx1 - vx0) + span: mid = True
                if 760 - (min(cy, bx[3] - 20 / z) - _at([[c[0], c[2]] for c in cam], tt)) * z >= 440: clear = True
            if not hit: E.append('step %d: the camera is not looking at "%s"; move the camera to it for this step' % (i, sh))
            elif not big: E.append('step %d: "%s" is too small on screen (it must be the star of the step); make it bigger or zoom the camera in until it is at least %d px' % (i, sh, need))
            elif not mid: E.append('step %d: "%s" sits at the edge of the picture; centre the camera x on it' % (i, sh))
            elif not clear: E.append('step %d: "%s" is hidden behind the caption at the top; aim the camera higher (bigger camera y) so it sits in the middle of the screen' % (i, sh))
    # rule: solid machines and buildings are never drawn under water
    for p in good:
        if p['type'] not in SOLID or p.get('inside'): continue
        bx = _box(p); cx, cy = (bx[0] + bx[1]) / 2, (bx[2] + bx[3]) / 2
        for w in waters:
            wb = _box(w)
            if wb[0] < cx < wb[1] and wb[2] < cy < wb[3] - 4 and (wb[1] - wb[0]) > (bx[1] - bx[0]) * 1.3:
                E.append('the %s%s is drawn inside the water (x %d-%d); put machines and buildings on dry ground beside or below the water, joined by a pipe (or, if it truly belongs in the water, give it "inside": "<id of its container>")' % (p['type'], ' "%s"' % p['id'] if p.get('id') else '', wb[0], wb[1])); break
    # rule: water does not float in the air
    holders = [p for p in good if p['type'] in ('rect', 'poly', 'house', 'tower')]
    for w in waters:
        wb = _box(w)
        if wb[2] > (gy if gy is not None else 0) + 70 and not any(_box(h)[0] <= wb[0] + 14 and _box(h)[1] >= wb[1] - 14 and _box(h)[2] <= wb[2] + 14 for h in holders):
            E.append('the water at x %d-%d floats in the air; give it a container or raised ground under it' % (wb[0], wb[1]))
    # rule: pipes and wires join things
    others = lambda me: [_box(q) for q in good if q is not me and q['type'] not in SCENERY]
    for p in good:
        if p['type'] not in ('pipe', 'wire') or not (isinstance(p.get('pts'), list) and len(p['pts']) >= 2 and all(_pt(q) for q in p['pts'])): continue
        for end, name in ((p['pts'][0], 'start'), (p['pts'][-1], 'end')):
            if end[0] <= -330 or end[0] >= 650 or end[1] <= -180 or end[1] >= 400: continue   # it leaves the picture (supply from outside, drain away)
            if not any(_near(end, bx, 48) for bx in others(p)): E.append('the %s %s at %s is not joined to anything; start and end it touching the things it connects (or run it off the edge of the stage, x=-360 or x=680, if it comes from outside)' % (p['type'], name, end))
    # rule: flows obey physics
    fl = spec.get('flows')
    if any(p['type'] in ('pipe', 'stream') for p in good):
        if not isinstance(fl, list) or not fl: E.append('add "flows": for each pipe say where the water goes and why: [{"from":[x,y],"to":[x,y],"by":"gravity" or "pump" or "pressure"}]')
        else:
            for n, f in enumerate(fl, 1):
                if not (isinstance(f, dict) and _pt(f.get('from')) and _pt(f.get('to')) and f.get('by') in ('gravity', 'pump', 'pressure')): E.append('flow %d must have from, to and by (gravity, pump or pressure)' % n); continue
                if f['by'] == 'gravity' and f['to'][1] > f['from'][1] - 15: E.append('flow %d is marked gravity but does not go down (from height %d to %d); water only falls downhill: raise the source, lower the outlet, or mark it "pressure" (mains water) or "pump" if something pushes it' % (n, f['from'][1], f['to'][1]))
                if f['by'] == 'pump' and not any(p['type'] == 'pump' for p in good): E.append('flow %d needs a pump part' % n)
                if f['by'] == 'pressure':
                    top = max([g['from'][1] for g in fl if isinstance(g, dict) and g.get('by') == 'gravity' and _pt(g.get('from'))] or [None], key=lambda v: -1e9 if v is None else v)
                    if top is not None and f['from'][1] < top and f['to'][1] > top - 15: E.append('flow %d: pressure can only push water up to below its source height (%d)' % (n, top))
    # rule: things stand on the ground or on something
    if gy is not None:
        tops = [_box(h)[3] for h in holders]
        for p in good:
            if p['type'] in ('house', 'tower', 'tree', 'plant'):
                y = _at(p.get('y'), 0, 0)
                if abs(y - gy) > 8 and not any(abs(y - tp) <= 8 for tp in tops): E.append('the %s at x=%d floats (y=%d); stand it on the ground (y=%d) or on top of a shape' % (p['type'], _at(p.get('x'), 0, 0), y, gy))
    # rule: labels come and go with their step, never a wall of tags
    labs = [p for p in good if p['type'] == 'label']
    for p in labs:
        if not _kfs(p.get('show')): E.append('label "%s" is always on; give it "show" keyframes so it appears only during its own step' % p.get('text'))
    t = 0.5
    while t < D:
        on = [p.get('text') for p in labs if _kfs(p.get('show')) and _at(p['show'], t) > 0.5]
        if len(on) > 2: E.append('%d labels are on screen together at %.1fs (%s); show at most 2 at a time' % (len(on), t, ', '.join(map(str, on[:4])))); break
        t += 0.5
    # rule: no clutter - recognisable objects do not sit on top of each other
    def visible(p, t):
        if p['type'] == 'emoji' and _at(p.get('size'), t, 80) < 12: return False
        if p['type'] == 'tree' and _at(p.get('grow'), t, 1) < 0.2: return False
        return _at(p.get('alpha'), t, 1) > 0.3
    objs = [p for p in good if p['type'] in OBJECTS]; told = set()
    for s_ in steps:
        if not (isinstance(s_, dict) and _num(s_.get('start')) and _num(s_.get('end'))): continue
        tt = (s_['start'] + s_['end']) / 2
        for i_, a_ in enumerate(objs):
            for b_ in objs[i_ + 1:]:
                if (id(a_), id(b_)) in told or not (visible(a_, tt) and visible(b_, tt)): continue
                A, B = _box_at(a_, tt), _box_at(b_, tt); ox = min(A[1], B[1]) - max(A[0], B[0]); oy = min(A[3], B[3]) - max(A[2], B[2])
                small = min((A[1] - A[0]) * (A[3] - A[2]), (B[1] - B[0]) * (B[3] - B[2]))
                inside = a_.get('inside') or b_.get('inside')   # only a declared container excuses an overlap
                if not inside and ox > 0 and oy > 0 and small > 0 and ox * oy / small > 0.4:
                    told.add((id(a_), id(b_))); nm = lambda q: '%s%s' % (q['type'], ' ' + q['char'] if q.get('char') else (' "%s"' % q['id'] if q.get('id') else ''))
                    E.append('clutter: %s and %s are drawn on top of each other around %.0fs (x=%d); move one of them so every object is clearly seen (if one truly sits inside the other, give it "inside": "<id>")' % (nm(a_), nm(b_), tt, (A[0] + A[1]) / 2))
    # rule: every step has its own sound
    sf = [c for c in (spec.get('sfx') or []) if isinstance(c, list) and c and _num(c[0])]
    for i, s in enumerate(steps, 1):
        if isinstance(s, dict) and _num(s.get('start')) and _num(s.get('end')) and not any(s['start'] - 0.3 <= c[0] <= s['end'] for c in sf): E.append('step %d has no sound; add one timed to its action' % i)
    return E

def check(spec):
    E = []
    if not isinstance(spec, dict): return ['the description must be one JSON object']
    D = spec.get('duration')
    if not _num(D) or not 20 <= D <= 50: E.append('duration must be a number of seconds between 20 and 50'); D = 33.6
    if not isinstance(spec.get('title'), str) or not 3 <= len(spec['title']) <= 70: E.append('title must be a short text')
    steps = spec.get('steps')
    if not isinstance(steps, list) or not 5 <= len(steps) <= 9: E.append('steps must be a list of 5 to 9 steps'); steps = []
    last = -1.0
    for i, s in enumerate(steps, 1):
        if not isinstance(s, dict) or not _num(s.get('start')) or not _num(s.get('end')): E.append('step %d needs start and end times' % i); continue
        if s['start'] < last - 0.01: E.append('step %d starts before step %d ends' % (i, i - 1))
        if s['end'] <= s['start'] or s['end'] > D + 0.01: E.append('step %d: end must be after start and within the duration' % i)
        last = s['end']
        say = s.get('say'); lab = s.get('label')
        if not isinstance(lab, str) or not 2 <= len(lab) <= 16: E.append('step %d: label must be 2 to 16 letters' % i)
        if not isinstance(say, str): E.append('step %d needs a "say" sentence' % i); continue
        w = len(say.split())
        if not 4 <= w <= 18: E.append('step %d: "say" must be 4 to 18 words (it has %d)' % (i, w))
        if w / 3.3 > (s['end'] - s['start']) + 0.4: E.append('step %d: the sentence is too long to speak in %.1f seconds; cut it to about %d words' % (i, s['end'] - s['start'], int((s['end'] - s['start']) * 3.3)))
    says = [str(s.get('say', '')) for s in steps if isinstance(s, dict)]
    if len(says) >= 5 and sum(1 for x in says if x.strip().endswith(('!', '?'))) < 4: E.append('the script is flat: at least 4 sentences must end with ! or ? and use strong action verbs')
    cam = spec.get('camera')
    if not isinstance(cam, list) or len(cam) < 3 or not all(isinstance(c, list) and len(c) == 4 and all(_num(v) for v in c) for c in cam): E.append('camera must be a list of at least 3 [time, x, y, zoom] entries'); cam = []
    else:
        if any(b[0] <= a[0] for a, b in zip(cam, cam[1:])): E.append('camera times must go up')
        if cam[0][0] > 0.5 or cam[-1][0] < D - 1.5: E.append('camera must start at time 0 and run to the end of the video')
        if any(not 0.45 <= c[3] <= 3.2 for c in cam): E.append('camera zoom must stay between 0.45 and 3.2')
    parts = spec.get('parts')
    if not isinstance(parts, list) or not 8 <= len(parts) <= 70: E.append('parts must be a list of 8 to 70 parts'); parts = []
    if parts and (not isinstance(parts[0], dict) or parts[0].get('type') != 'sky'): E.append('the first part must be the sky (background)')
    anim_times = []; movers = []
    for n, p in enumerate(parts, 1):
        if not isinstance(p, dict) or p.get('type') not in CATALOG: E.append('part %d: unknown type %r (allowed: %s)' % (n, p.get('type') if isinstance(p, dict) else p, ', '.join(CATALOG))); continue
        req, opt, _ = CATALOG[p['type']]; tag = 'part %d (%s)' % (n, p['type'])
        for f in req:
            if f not in p: E.append('%s is missing "%s"' % (tag, f))
        moving = False
        for f, v in p.items():
            if f in ('type', 'id', 'inside'): continue
            if f not in req and f not in opt: E.append('%s has a field the engine does not know: "%s"' % (tag, f)); continue
            if f in POINT_LISTS:
                if not (isinstance(v, list) and len(v) >= 2 and all(_pt(q) for q in v)): E.append('%s: "%s" must be a list of [x,y] points' % (tag, f))
                elif any(abs(q[0]) > 1400 or not -500 <= q[1] <= 950 for q in v): E.append('%s: a point is far outside the stage' % tag)
            elif f in POINTS:
                if not _pt(v): E.append('%s: "%s" must be one [x,y] point' % (tag, f))
            elif f in ANIM:
                if _num(v): pass
                elif _kfs(v):
                    ts = [k[0] for k in v]
                    if any(b < a for a, b in zip(ts, ts[1:])): E.append('%s: times in "%s" must go up' % (tag, f))
                    if ts[0] < -0.01 or ts[-1] > D + 0.6: E.append('%s: "%s" has a time outside the video' % (tag, f))
                    if len({k[1] for k in v}) > 1: moving = True; anim_times += ts
                else: E.append('%s: "%s" must be a number or keyframes [[time, value], ...]' % (tag, f))
            elif f in ('x0', 'x1', 'legH', 'lw', 'teeth', 'dir', 'head', 'floor', 'bob', 'speed', 'count') and not _num(v): E.append('%s: "%s" must be a number' % (tag, f))
            elif f in ('fill', 'stroke', 'color', 'bg', 'text', 'preset', 'kind', 'wall', 'roof', 'rgb', 'outline', 'char', 'd') and not isinstance(v, str): E.append('%s: "%s" must be text' % (tag, f))
            elif f == 'char' and (not 1 <= len(v) <= 8 or all(ord(ch) < 128 for ch in v)): E.append('%s: "char" must be ONE emoji character' % tag)
            elif f == 'd' and (not 5 <= len(v) <= 1800 or not re.fullmatch(r'[MmLlHhVvCcSsQqTtAaZz0-9eE\s,.+-]+', v)): E.append('%s: "d" must be a plain SVG path string (letters MLHVCSQTAZ and numbers only, under 1800 characters)' % tag)
            elif f == 'preset' and v not in PRESETS: E.append('%s: unknown preset %r (allowed: %s)' % (tag, v, ', '.join(sorted(PRESETS))))
            elif f == 'kind' and p['type'] == 'particles' and v not in PARTICLES: E.append('%s: unknown particles kind %r (allowed: %s)' % (tag, v, ', '.join(sorted(PARTICLES))))
            elif f == 'kind' and p['type'] == 'ground' and v not in GROUNDS: E.append('%s: unknown ground kind %r (allowed: %s)' % (tag, v, ', '.join(sorted(GROUNDS))))
            elif f == 'orbit':
                if not (isinstance(v, dict) and all(_num(v.get(k)) for k in ('cx', 'cy', 'rx')) and all(_num(x) for x in v.values()) and v.get('period', 6) >= 1): E.append('%s: "orbit" must be {"cx","cy","rx","ry","period","phase"} with numbers' % tag)
                else: moving = True
            elif f == 'dash' and not (isinstance(v, list) and len(v) == 2 and all(_num(x) and x > 0 for x in v)): E.append('%s: "dash" must be two numbers like [10,10]' % tag)
        if p['type'] == 'label' and isinstance(p.get('text'), str) and len(p['text']) > 18: E.append('%s: label text is too long (max 16 letters)' % tag)
        if p['type'] == 'text' and isinstance(p.get('text'), str) and len(p['text']) > 14: E.append('%s: text is too long (max 12 letters)' % tag)
        for f in ('x', 'y'):
            v = p.get(f)
            for val in ([v] if _num(v) else [k[1] for k in v] if _kfs(v) else []):
                if (f == 'x' and abs(val) > 1400) or (f == 'y' and not -500 <= val <= 950): E.append('%s: %s=%s is far outside the stage' % (tag, f, val)); break
        if moving: movers.append(p)
    if parts and len(movers) < 6: E.append('too little movement: only %d parts change over time; a living scene needs at least 6' % len(movers))
    cam_times = [c[0] for c in cam]
    for i, s in enumerate(steps, 1):
        if not (isinstance(s, dict) and _num(s.get('start')) and _num(s.get('end'))): continue
        a, b = s['start'] - 0.4, s['end']
        if sum(1 for t in anim_times + cam_times if a <= t <= b) < 2: E.append('step %d: nothing changes on screen during this step; make something move, fill, grow or appear between %.1f and %.1f' % (i, s['start'], s['end']))
        if cam:   # the camera must be looking at something that is changing in this step
            mid = (s['start'] + s['end']) / 2; cx = _at([[c[0], c[1]] for c in cam], mid); cy = _at([[c[0], c[2]] for c in cam], mid); z = _at([[c[0], c[3]] for c in cam], mid)
            vx0, vx1, vy0, vy1 = cx - 360 / z, cx + 360 / z, cy - 520 / z, cy + 760 / z; seen = False
            for p in movers:
                act = any(a <= k[0] <= b for f, v in p.items() if f in ANIM and _kfs(v) for k in v)
                if not act: continue
                x0, x1, y0, y1 = _where(p)
                if x1 >= vx0 and x0 <= vx1 and y1 >= vy0 and y0 <= vy1: seen = True; break
            if not seen and any(any(a <= k[0] <= b for f, v in p.items() if f in ANIM and _kfs(v) for k in v) for p in movers):
                E.append('step %d: the camera (centre %d,%d zoom %.2f) is not pointing at the thing that moves in this step' % (i, cx, cy, z))
    E += design_rules(spec, D, steps, cam, parts)
    for n, c in enumerate(spec.get('sfx', []) or [], 1):
        if not (isinstance(c, list) and len(c) >= 2 and _num(c[0]) and isinstance(c[1], str)): E.append('sound %d must be [time, name, loudness]' % n); continue
        if c[1] not in SOUNDS: E.append('sound %d: unknown sound %r (allowed: %s)' % (n, c[1], ', '.join(sorted(SOUNDS))))
        if not 0 <= c[0] <= D: E.append('sound %d: time is outside the video' % n)
        if len(c) > 2 and not (_num(c[2]) and 0 < c[2] <= 1.2): E.append('sound %d: loudness must be between 0 and 1.2' % n)
        if len(c) > 3:
            if c[1] in SOUNDS_DUR and not (_num(c[3]) and 0.1 <= c[3] <= 6): E.append('sound %d: length must be 0.1 to 6 seconds' % n)
            elif c[1] in SOUNDS_FREQ and not (_num(c[3]) and 100 <= c[3] <= 4000): E.append('sound %d: pitch must be 100 to 4000' % n)
            elif c[1] not in SOUNDS_DUR and c[1] not in SOUNDS_FREQ: E.append('sound %d: %s takes no 4th value' % (n, c[1]))
        if len(c) > 4: E.append('sound %d has too many values' % n)
    if isinstance(spec.get('sfx'), list) and len(spec['sfx']) < 6: E.append('add more sounds: at least 6, one for each action on screen')
    return E

if __name__ == '__main__':
    errs = check(json.loads(Path(sys.argv[1]).read_text()))
    print('\n'.join(errs) if errs else 'OK'); sys.exit(1 if errs else 0)
