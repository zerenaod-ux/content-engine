"""INSIDE_STORY (owner rule 2026-11-14): the video is ONE detailed drawn object (from the PROPS library in scene.html).
The camera starts on the whole object, then flies INTO the exact inside part each sentence talks about (key, engine, battery ...),
and that part does its action (key turns, hood opens, piston moves, fuel flows, battery charges, wheels turn).
The free writer only writes the sentences and names a spot for each; everything visual is designed here.
Input (content.json): {"title", "principle", "object": "car", "steps": [{"say": "...", "spot": "key"}, ...]}"""
import json, sys

WPS = 2.9
S = 2.0   # object scale on screen

# spot: (x, y) inside the object (prop units), zoom, and what that part does while it is explained (field -> value it moves to)
LIBRARY = {
    'car': {
        'ground': '#7a7f86',
        'spots': {
            'whole':    ((0, 62), 1.0, {}),
            'key':      ((34, 88), 4.2, {'cut': 1, 'key': 1, 'light': 1}),
            'tank':     ((-124, 45), 3.4, {'cut': 1, 'fuel': 1}),
            'fuelline': ((-20, 40), 2.6, {'cut': 1, 'fuel': 1}),
            'engine':   ((92, 60), 3.6, {'hood': 1, 'cut': 1, 'run': 1}),
            'piston':   ((93, 62), 4.6, {'hood': 1, 'cut': 1, 'run': 1}),
            'spark':    ((93, 80), 5.0, {'hood': 1, 'cut': 1, 'run': 1, 'spark': 1}),
            'crank':    ((93, 46), 4.6, {'hood': 1, 'cut': 1, 'run': 1}),
            'battery':  ((141, 60), 4.6, {'hood': 1, 'cut': 1, 'charge': 1}),
            'gearbox':  ((76, 32), 4.0, {'cut': 1, 'run': 1, 'spin': 1}),
            'wheel':    ((105, 30), 3.6, {'spin': 1}),
            'exhaust':  ((-150, 30), 3.6, {'cut': 1, 'run': 1}),
        },
        'describe': 'a red car seen from the side; it can open its hood and show an x-ray of its inside',
    },
    'microwave': {
        'ground': '#b98a5a',
        'spots': {
            'whole':     ((0, 75), 1.2, {}),
            'door':      ((-37, 75), 2.8, {'door': 1}),
            'food':      ((-37, 40), 3.6, {'door': 0}),
            'keypad':    ((89, 56), 4.4, {}),
            'timer':     ((89, 116), 5.0, {'on': 1}),
            'magnetron': ((89, 93), 4.4, {'reveal': 1, 'on': 1}),
            'waves':     ((-37, 75), 2.8, {'on': 1, 'waves': 1, 'heat': 1, 'spin': 1}),
            'plate':     ((-37, 32), 3.6, {'on': 1, 'spin': 1}),
        },
        'describe': 'a kitchen microwave with a door, a glass plate, keypad, timer and a magnetron behind the side panel',
    },
}
LATCH = {'key', 'light', 'cut', 'hood', 'fuel', 'run', 'charge', 'on', 'reveal', 'heat'}   # once started these stay on


def build(c):
    lib = LIBRARY[c['object']]; spots = lib['spots']
    t, steps = 0.4, []
    for s in c['steps']:
        d = max(3.0, len(s['say'].split()) / WPS + 0.8)
        steps.append(dict(s, start=round(t, 2), end=round(t + d, 2))); t += d
    dur = round(t + 0.6, 2)
    # part fields: start at 0, move to the action value as its sentence starts
    fields, state = {}, {}
    for s in steps:
        acts = spots.get(s.get('spot'), spots['whole'])[2]
        for f, v in acts.items():
            if state.get(f) != v:
                fields.setdefault(f, [[0, 0]]).append([s['start'] + 0.1, state.get(f, 0)])
                fields[f].append([s['start'] + 1.0, v]); state[f] = v
        for f in list(state):   # actions that do not latch stop when their sentence ends
            if f not in LATCH and f not in acts and state[f]:
                fields[f] += [[s['start'] + 0.1, state[f]], [s['start'] + 0.8, 0]]; state[f] = 0
    prop = {'type': 'prop', 'kind': c['object'], 'id': c['object'], 'x': 0, 'y': 0, 's': S}
    for f, kfs in fields.items():
        clean = []
        for k in kfs:
            if clean and k[0] <= clean[-1][0]: k = [clean[-1][0] + 0.01, k[1]]
            clean.append([round(k[0], 2), k[1]])
        prop[f] = clean
    parts = [{'type': 'sky', 'preset': 'clean'}, {'type': 'rect', 'x': -900, 'y': -500, 'w': 1800, 'h': 500, 'fill': lib['ground']}, prop]
    # camera: fly from the whole object into each spot (0.9 s move), hold with a slow push-in
    cam = []
    for s in steps:
        (x, y), z, _ = spots.get(s.get('spot'), spots['whole'])
        cx, cy = x * S, y * S + 120 / z   # keep the part below the caption
        cam += [[s['start'] + 0.9, cx, cy, z], [s['end'], cx, cy, z * 1.06]]
    cam = [[0, cam[0][1], cam[0][2], cam[0][3]]] + cam
    fixed = []
    for k in cam:
        if fixed and k[0] <= fixed[-1][0]: k = [fixed[-1][0] + 0.01] + k[1:]
        fixed.append([round(k[0], 2), round(k[1], 1), round(k[2], 1), round(k[3], 3)])
    fixed.append([dur] + fixed[-1][1:])
    out_steps = [{'start': s['start'], 'end': s['end'], 'label': (s.get('spot') or 'whole').capitalize() if s.get('spot') != 'whole' else c['object'].capitalize(),
                  'say': s['say'], 'shows': c['object']} for s in steps]
    return {'template': 1, 'title': c['title'], 'principle': c.get('principle', c['title']), 'duration': dur, 'music': {'bpm': 112},
            'camera': fixed, 'steps': out_steps, 'parts': parts}


if __name__ == '__main__':
    spec = build(json.load(open(sys.argv[1])))
    json.dump(spec, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print('inside story: %d steps, %.1f s' % (len(spec['steps']), spec['duration']))
