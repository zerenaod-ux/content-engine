"""CLEAN_TEMPLATE: the free writer only chooses WHAT to show (a star object, 3-5 parts of the chain, one sentence per step).
WHERE things go, how big they are, the camera and the motion are fixed and designed here, so every video is tidy:
big star at the top, the chain as large picture cards below, arrows that grow in order, the camera moves to each card as it is talked about.
Input (content.json):
 {"title": "...", "star": {"emoji": "🏎️", "label": "Race car"} or {"prop": "microwave", "label": "..."},
  "items": [{"id": "wheel", "emoji": "🛞", "label": "Spinning wheel"}, ...3-5],
  "steps": [{"say": "...", "focus": "star" | item id | "all", "link": [from_id, to_id] (optional)}, ...7-12]}
"""
import json, sys

WPS = 2.9          # spoken words per second at the narrator's speed
CARD_W, CARD_H = 250, 230
PALETTE = ['#ffd166', '#06d6a0', '#4cc9f0', '#f78c6b', '#c77dff']


def _kf(points):
    out = []
    for t, v in points:
        if out and t <= out[-1][0]: t = out[-1][0] + 0.01
        out.append([round(t, 2), v])
    return out


def build(c):
    items = c['items'][:5]
    n = len(items)
    # star at the top, cards in a two-column zigzag below it
    pos = {'star': (0, 430)}
    for i, it in enumerate(items):
        pos[it['id']] = (-160 if i % 2 == 0 else 160, 110 - i * 300)
    # timing from the words
    t, steps = 0.4, []
    for s in c['steps']:
        d = max(3.2, len(s['say'].split()) / WPS + 0.9)
        steps.append(dict(s, start=round(t, 2), end=round(t + d, 2))); t += d
    dur = round(t + 0.5, 2)
    parts = [{'type': 'sky', 'preset': 'clean'}]
    # soft panel behind the chain
    top, bottom = 260, 110 - (n - 1) * 300 - CARD_H / 2 - 40
    parts.append({'type': 'rect', 'x': -330, 'y': bottom, 'w': 660, 'h': top - bottom, 'r': 36, 'fill': '#ffffff', 'alpha': 0.22})

    def first(idv):
        for s in steps:
            if s.get('focus') == idv or idv in (s.get('link') or []): return s['start']
        return 0.4

    def focus_glow(idv):
        a = [[0, 0]]
        for s in steps:
            on = 1 if s.get('focus') == idv else 0
            a += [[s['start'] + 0.15, on], [s['end'] - 0.15, on]]
        return _kf(a)

    # arrows (drawn under the cards), each grows during the step that names the link, else in item order when the next card appears
    links = []
    for s in steps:
        l = s.get('link')
        if l and len(l) == 2 and all(x in pos for x in l) and tuple(l) not in [x[:2] for x in links]: links.append((l[0], l[1], s['start'], s['end']))
    if not links:
        chain = ['star'] + [it['id'] for it in items]
        for a, b in zip(chain, chain[1:]): links.append((a, b, first(b), first(b) + 1.5))
    for a, b, s0, s1 in links:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        fr = [x1 + 0.3 * (x2 - x1), (y1 - CARD_H / 2 - 4) if a != 'star' else y1 - 130]
        to = [x2 - 0.3 * (x2 - x1), y2 + CARD_H / 2 + 12]
        for k in range(3):   # ENERGY: little sparks travel along the arrow while that link is explained
            t0 = s0 + 0.4 + k * 0.5; xs, ys = [[0, fr[0]]], [[0, fr[1]]]; al = [[0, 0], [t0, 0], [t0 + 0.1, 1]]
            tt = t0
            while tt + 1.2 < s1:
                xs += [[tt, fr[0]], [tt + 1.2, to[0]]]; ys += [[tt, fr[1]], [tt + 1.2, to[1]]]; tt += 1.25
            al += [[max(t0 + 0.2, s1 - 0.2), 1], [s1, 0]]
            parts.append({'type': 'emoji', 'char': '⚡' if c.get('spark') is None else c['spark'], 'x': _kf(xs), 'y': _kf(ys), 'size': 46, 'alpha': _kf(al)})
        parts.append({'type': 'arrow', 'from': fr, 'to': to, 'w': 12, 'head': 30, 'color': '#ff5a3c',
                      'progress': _kf([[0, 0], [s0 + 0.3, 0], [min(s1, s0 + 1.8), 1]])})
    # star
    sx, sy = pos['star']
    parts.append({'type': 'glow', 'x': sx, 'y': sy, 'r': 260, 'rgb': '255,214,102', 'alpha': focus_glow('star')})
    st = c['star']
    if st.get('prop'):
        parts.append({'type': 'prop', 'kind': st['prop'], 'x': sx, 'y': sy - 120, 's': 1.6, 'id': 'star'})
    else:
        parts.append({'type': 'emoji', 'id': 'star', 'char': st['emoji'], 'x': sx, 'y': sy, 'size': 300,
                      'alpha': _kf([[0, 0], [0.5, 1]]), 'bob': 4})
    # cards
    for i, it in enumerate(items):
        x, y = pos[it['id']]; t0 = max(0.3, first(it['id']) - 0.4)
        col = PALETTE[i % len(PALETTE)]
        show = _kf([[0, 0], [t0, 0], [t0 + 0.5, 1]])
        parts.append({'type': 'glow', 'x': x, 'y': y, 'r': 210, 'rgb': '255,236,140', 'alpha': focus_glow(it['id'])})
        parts.append({'type': 'rect', 'id': it['id'] + '_card', 'x': x - CARD_W / 2, 'y': y - CARD_H / 2, 'w': CARD_W, 'h': CARD_H, 'r': 30,
                      'fill': '#ffffff', 'stroke': col, 'lw': 9, 'alpha': show})
        parts.append({'type': 'rect', 'x': x - CARD_W / 2 + 12, 'y': y - CARD_H / 2 + 12, 'w': CARD_W - 24, 'h': 52, 'r': 18, 'fill': col, 'alpha': show})
        # MOTION: while its card is talked about the picture moves - spins (wheels, gears, fans) or pulses
        act = it.get('action') or ('spin' if any(w in it['label'].lower() for w in ('wheel', 'gear', 'motor', 'generator', 'fan', 'turbine', 'rotor', 'drum')) else 'pulse')
        rot, size = [[0, 0]], [[0, 120]]
        for st_ in steps:
            if st_.get('focus') != it['id']: continue
            a0, a1 = st_['start'] + 0.2, st_['end'] - 0.2
            if act == 'spin': rot += [[a0, rot[-1][1]], [a1, rot[-1][1] - 360 * (a1 - a0) / 1.6]]
            else:
                k = a0
                while k + 0.6 < a1: size += [[k, 120], [k + 0.3, 140], [k + 0.6, 120]]; k += 0.6
        parts.append({'type': 'emoji', 'id': it['id'], 'char': it['emoji'], 'x': x, 'y': y + 28, 'size': _kf(size), 'rot': _kf(rot), 'alpha': show})
        parts.append({'type': 'text', 'x': x, 'y': y - CARD_H / 2 + 38, 'text': it['label'][:18], 'size': 25 if len(it['label']) <= 12 else 20, 'color': '#1b2a41', 'outline': 'rgba(255,255,255,0.0)', 'alpha': show})
    # camera: close on the card being talked about, wide on "all"
    wide_y = (430 + bottom) / 2
    cam = []
    for s in steps:
        f = s.get('focus')
        if f in pos and f != 'star': x, y = pos[f]; sc = 1.6; x *= 0.55; y += 110 / sc   # card sits in the middle, below the caption
        elif f == 'star': x, y, sc = 0, 400 + 40 / 1.4, 1.4
        else: sc = min(1.0, 980 / (430 + 170 - bottom)); x, y = 0, (430 + 170 + bottom) / 2 - 110 / sc
        cam += [[s['start'], x, y, sc], [s['end'] - 0.5, x, y, sc * 1.04]]
    fixed = []
    for k in cam:
        if fixed and k[0] <= fixed[-1][0]: k = [fixed[-1][0] + 0.01] + k[1:]
        fixed.append([round(k[0], 2)] + [round(v, 1) if i < 2 else round(v, 3) for i, v in enumerate(k[1:])])
    cam = fixed + [[dur] + fixed[-1][1:]]
    out_steps = [{'start': s['start'], 'end': s['end'], 'label': s.get('label') or {i['id']: i['label'] for i in items}.get(s.get('focus'), c['star'].get('label', 'How') if s.get('focus') == 'star' else 'Together'), 'say': s['say'],
                  'shows': s.get('focus') if s.get('focus') in pos else 'star'} for s in steps]
    return {'template': 1, 'title': c['title'], 'principle': c.get('principle', c['title']), 'duration': dur, 'music': {'bpm': 118},
            'camera': [list(x) for x in cam], 'steps': out_steps, 'parts': parts}


if __name__ == '__main__':
    spec = build(json.load(open(sys.argv[1])))
    json.dump(spec, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print('template scene: %d steps, %.1f s' % (len(spec['steps']), spec['duration']))
