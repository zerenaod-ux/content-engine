"""Machine-checkable demonstration contracts. These establish declared numeric
changes, not factual accuracy or human comprehension. Render checks add visibility.
"""
import json
import math
from scene_lib.catalog import ANIM


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def value_at(value, t):
    if number(value): return value
    if not (isinstance(value, list) and value and all(isinstance(k, list) and len(k) == 2 and all(number(x) for x in k) for k in value)):
        return None
    if any(b[0] <= a[0] for a, b in zip(value, value[1:])): return None
    if t <= value[0][0]: return value[0][1]
    for (a, x), (b, y) in zip(value, value[1:]):
        if t <= b:
            u = (t - a) / (b - a)
            return x + (y - x) * u * u * (3 - 2 * u)
    return value[-1][1]


def check_contract(spec):
    errors = []
    if spec.get('evidence_version') != 1: errors.append('unsupported evidence_version')
    basis = spec.get('basis')
    if not isinstance(basis, dict) or not basis.get('limitations') or basis.get('status') != 'model_knowledge_unverified':
        errors.append('basis must explicitly disclose unverified model knowledge and limitations')
    parts = {p.get('id'): p for p in spec.get('parts', []) if isinstance(p, dict) and isinstance(p.get('id'), str)} if isinstance(spec.get('parts'), list) else {}
    for i, step in enumerate(spec.get('steps', []) if isinstance(spec.get('steps'), list) else [], 1):
        if not isinstance(step, dict): continue
        tag = 'step %d demonstration' % i
        if not isinstance(step.get('demonstration'), str) or len(step['demonstration'].split()) < 4:
            errors.append(tag + ': describe what supports the spoken claim')
        evidence = step.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            errors.append(tag + ': evidence must name the indispensable parts and their measurable changes'); continue
        for item in evidence:
            if not isinstance(item, dict): errors.append(tag + ': evidence must be an object'); continue
            part = parts.get(item.get('part')) if isinstance(item.get('part'),str) else None; field = item.get('field')
            at, values = item.get('at'), item.get('values')
            if part is None or not isinstance(field, str) or field not in ANIM or field in ('show',):
                errors.append(tag + ': use an existing part and a physical numeric field (alpha allowed for reveal only)'); continue
            if not (isinstance(at, list) and len(at) == 2 and all(number(x) for x in at) and isinstance(values, list) and len(values) == 2 and all(number(x) for x in values)):
                errors.append(tag + ': at and values need two finite numbers'); continue
            if not (number(step.get('start')) and number(step.get('end')) and step['start'] <= at[0] < at[1] <= step['end']):
                errors.append(tag + ': evidence times must be ordered inside the beat'); continue
            actual = [value_at(part.get(field), t) for t in at]
            if any(x is None or abs(x - y) > 0.001 for x, y in zip(actual, values)):
                errors.append(tag + ': %s.%s does not match promised values' % (item['part'], field))
            if abs(values[1] - values[0]) < 0.001: errors.append(tag + ': promised change is constant')
        # Explicit comparisons generalize to spectra, parallel circuits, flows,
        # trajectories or before/after objects. Do not infer meaning from motion.
        groups = step.get('contrasts', [])
        if not isinstance(groups, list): errors.append(tag + ': contrasts must be a list'); continue
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get('parts'), list) or len(group['parts']) < 2 or not isinstance(group.get('fields'), list) or not group['fields']:
                errors.append(tag + ': a contrast needs at least two parts and distinguishing fields'); continue
            members = [parts.get(id) for id in group['parts'] if isinstance(id,str)]
            if len(members) != len(group['parts']) or any(p is None for p in members):
                errors.append(tag + ': contrast references missing parts'); continue
            declared = {e.get('part') for e in evidence if isinstance(e,dict)}
            if not set(group['parts']) <= declared: errors.append(tag + ': every contrast member needs visibility evidence')
            for field in group['fields']:
                if not isinstance(field,str) or any(field not in p for p in members):
                    errors.append(tag + ': contrast field is absent'); continue
                values = [json.dumps(p[field], sort_keys=True) for p in members]
                if len(set(values)) != len(values): errors.append(tag + ': contrasted parts must have distinct ' + field)
    return errors
