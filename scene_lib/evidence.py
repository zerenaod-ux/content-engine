"""Machine-checkable demonstration contracts. These establish declared numeric
changes, not factual accuracy or human comprehension. Render checks add visibility.
"""
import json
import math
from scene_lib.catalog import ANIM, CATALOG


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
            allowed = CATALOG.get(part.get('type'), ([],[],'')) if part else ([],[],'')
            if part is None or not isinstance(field, str) or field not in ANIM or field not in allowed[0]+allowed[1] or field in ('show',):
                errors.append(tag + ': %s.%s is not a supported numeric animation field; choose a part/field from the catalog (alpha is reveal only)' % (item.get('part'),field)); continue
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
            for field in group['fields']:
                if not isinstance(field,str) or any(field not in p for p in members):
                    errors.append(tag + ': contrast field is absent'); continue
                values = [json.dumps(p[field], sort_keys=True) for p in members]
                if len(set(values)) != len(values): errors.append(tag + ': contrasted parts must have distinct ' + field)
    return errors


def compile_animation(spec):
    """Compile declared numeric changes into real renderer keyframes.

    The declaration is the animation source, not a second copy of hand-written
    keyframes that a model must keep in sync. Validation/rendering still check
    the resulting drawing; this cannot establish the declaration's meaning.
    """
    import copy
    from scene_lib.catalog import CATALOG
    out=copy.deepcopy(spec)
    parts={p.get('id'):p for p in out.get('parts',[]) if isinstance(p,dict) and isinstance(p.get('id'),str)}
    schedules={}; intervals={}
    for step in out.get('steps',[]):
        if not isinstance(step,dict): continue
        for e in step.get('evidence',[]) if isinstance(step.get('evidence'),list) else []:
            if not isinstance(e,dict) or not isinstance(e.get('part'),str): continue
            p=parts.get(e['part']);field=e.get('field');times=e.get('at');values=e.get('values')
            if p is None or p.get('type') not in CATALOG or not isinstance(field,str): continue
            req,opt,_=CATALOG[p['type']]
            if field not in ANIM or field not in req+opt: continue
            if not (isinstance(times,list) and len(times)==2 and all(number(t) for t in times) and isinstance(values,list) and len(values)==2 and all(number(v) for v in values)): continue
            key=(e['part'],field)
            schedule=schedules.setdefault(key,{})
            intervals.setdefault(key,[]).append(tuple(times))
            for t,v in zip(times,values):
                if t in schedule and abs(schedule[t]-v)>.001: raise ValueError('conflicting animation declarations for %s.%s at %s' % (e['part'],field,t))
                schedule[t]=v
    for (id,field),schedule in schedules.items():
        existing=parts[id].get(field)
        if isinstance(existing,list):
            for pair in existing:
                if isinstance(pair,list) and len(pair)==2 and all(number(x) for x in pair):
                    t,v=pair
                    if not any(a<=t<=b for a,b in intervals[(id,field)]): schedule.setdefault(t,v)
        parts[id][field]=[[t,v] for t,v in sorted(schedule.items())]
    out['animation_source']='evidence'
    return out


def render_requirements(spec):
    """Every declared contrast member is inspected even when it is static.
    Numeric animation declarations and static visibility serve different jobs.
    """
    out=[]
    for i,step in enumerate(spec.get('steps',[]),1):
        evidence=[dict(e) for e in step.get('evidence',[])]
        ids={e['part'] for e in evidence}
        for group in step.get('contrasts',[]):
            for id in group.get('parts',[]):
                if id not in ids:
                    evidence.append({'part':id,'field':'contrast','at':[step['start'],step['end']]})
                    ids.add(id)
        out.extend({'step':i,**e} for e in evidence)
    return out
