"""Rendered blankness, variation and declared-part visibility checks.
Never a semantic or scientific verifier. python3 scene_lib/check_frames.py spec.json
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image


def pixels(path):
    return np.asarray(Image.open(path).convert('RGB'), dtype=float)


def inspect(spec, frames=Path('fr')):
    shots = []
    for step in spec['steps']:
        f = round((step['start'] + step['end']) / 2 * 30)
        shots.append(np.asarray(Image.open(frames / ('%04d.jpg' % f)).convert('L').resize((90, 160)), dtype=float))
    errors = []
    flat = [i + 1 for i, a in enumerate(shots) if a[40:].std() < 10]
    same = [i + 1 for i, (a, b) in enumerate(zip(shots, shots[1:])) if np.abs(a-b)[40:].mean() < 1.5]
    if flat: errors.append('nearly blank steps: %s' % flat)
    if len(same) > 1: errors.append('little variation between steps: %s' % same)
    results = []
    if spec.get('evidence_version') == 1:
        from scene_lib.evidence import check_contract
        errors += check_contract(spec)
        try:
            manifest = json.loads((frames / 'evidence/manifest.json').read_text())
            expected = [(i + 1, e['part'], e['field']) for i, s in enumerate(spec['steps']) for e in s.get('evidence', [])]
            if [(e['step'], e['part'], e['field']) for e in manifest] != expected:
                errors.append('rendered evidence manifest does not match this scene')
            for row in manifest:
                counts = []
                for base in row['files']:
                    a = pixels(frames / ('evidence/' + base + '-actual.jpg'))
                    b = pixels(frames / ('evidence/' + base + '-removed.jpg'))
                    # Exclude title/caption overlays. JPEG noise below 24 is ignored.
                    mask = np.max(np.abs(a-b), axis=2) > 24
                    mask[:360] = False; mask[1180:] = False
                    counts.append(int(mask.sum()))
                visible = len(counts) == 2 and max(counts) >= 80
                results.append({**row, 'visible_pixels': counts, 'visible': visible})
                if not visible:
                    errors.append('step %s: declared evidence %s is absent, tiny or occluded' % (row['step'], row['part']))
                    part=next((p for p in spec.get('parts',[]) if p.get('id')==row['part']),None)
                    if part:
                        fields={'path':('d','x','y','scale','rot'),'line':('pts',),'ellipse':('x','y','rx','ry','rot')}.get(part.get('type'),())
                        overlap=[p.get('id') for p in spec.get('parts',[]) if p is not part and p.get('type')==part.get('type') and fields and all(p.get(k)==part.get(k) for k in fields)]
                        if overlap: errors.append('hidden evidence %s shares the same geometry with %s; later drawing layers can cover it. Distinct comparison elements need separately visible geometry.' % (row['part'], ', '.join(str(x) for x in overlap)))
        except (OSError, ValueError, KeyError, TypeError) as e:
            errors.append('rendered evidence missing or unreadable: %s' % type(e).__name__)
    return {'checks': 'blankness, frame variation, numeric contracts and sampled part visibility',
            'semantic_verification': False, 'factual_verification': False,
            'human_review_required': True, 'warnings': ['Extra helper labels are suppressed by the renderer if more than two appear together.'] if sum(p.get('type')=='label' for p in spec.get('parts',[]))>2 else [], 'errors': errors, 'evidence': results}


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    report = inspect(json.loads(Path(sys.argv[1]).read_text()))
    Path('evidence-report.json').write_text(json.dumps(report, indent=1))
    print('render checks: ' + ('FAILED: ' + ' | '.join(report['errors']) if report['errors'] else 'passed; semantic/factual review still required'))
    sys.exit(1 if report['errors'] else 0)
