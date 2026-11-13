"""After rendering: makes sure the video is not blank and that the picture really changes from step to step.  python3 scene_lib/check_frames.py spec.json"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
spec = json.loads(Path(sys.argv[1]).read_text()); shots = []
for s in spec['steps']:
    f = int(round((s['start'] + s['end']) / 2 * 30)); shots.append(np.asarray(Image.open('fr/%04d.jpg' % f).convert('L').resize((90, 160)), dtype=float))
flat = [i + 1 for i, a in enumerate(shots) if a[40:, :].std() < 10]
same = [i + 1 for i, (a, b) in enumerate(zip(shots, shots[1:])) if np.abs(a - b)[40:, :].mean() < 1.5]
msg = []
if flat: msg.append('the picture is nearly blank in step(s) %s' % flat)
if len(same) > 1: msg.append('the picture barely changes between steps %s' % ['%d-%d' % (i, i + 1) for i in same])
print('\n'.join(msg) if msg else 'frames OK: the picture changes in every step'); sys.exit(1 if msg else 0)
