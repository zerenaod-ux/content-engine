"""Bounded repair of a saved scene. Keeps untouched parts, timing and accepted
planning work. No publication or approval side effects. Optional factual context
is supplied explicitly; the model must never present itself as a fact verifier.
"""
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from scene_lib.validate import check
from scene_lib.writer import _call, auto_camera, SYS


def apply_patch(spec, patch):
    if not isinstance(patch,dict): raise ValueError('repair must be an object')
    new=copy.deepcopy(spec)
    replacements=patch.get('replace_parts',{})
    if not isinstance(replacements,dict): raise ValueError('replace_parts must be keyed by existing part id')
    ids={p.get('id'):i for i,p in enumerate(new['parts']) if p.get('id')}
    for id,part in replacements.items():
        if id not in ids or not isinstance(part,dict) or part.get('id') != id:
            raise ValueError('replacement must preserve an existing part id')
        new['parts'][ids[id]]=part
    for part in patch.get('add_parts',[]):
        if not isinstance(part,dict) or not isinstance(part.get('id'),str) or part['id'] in ids:
            raise ValueError('added parts need unique ids')
        ids[part['id']]=len(new['parts']);new['parts'].append(part)
    for update in patch.get('step_updates',[]):
        if not isinstance(update,dict) or not isinstance(update.get('index'),int) or isinstance(update['index'],bool) or not 0 <= update['index'] < len(new['steps']):
            raise ValueError('step update needs a valid zero-based index')
        if set(update) - {'index','say','demonstration','evidence','contrasts','shows','label'}:
            raise ValueError('repair cannot silently alter timing or other step fields')
        new['steps'][update['index']].update({k:v for k,v in update.items() if k != 'index'})
    if isinstance(patch.get('principle'),str): new['principle']=patch['principle']
    new.pop('_path_bounds',None)  # geometry belongs to the old shapes
    auto_camera(new)
    return new


def repair(spec, problems, context='', log=print):
    import llm
    for attempt in range(2):
        prompt='''Repair this saved animated scene, not the whole production pipeline.
First identify every narrated mechanism that its actual drawing fails to show.
The supplied error list is incomplete: visibility alone cannot prove the claim.
Preserve correct parts and timings. Build missing physical demonstrations and
correct scientifically misleading narration. Keep speech plain and natural: 4–18 words per sentence, fitting its existing window. Focus shows may be a ray/path for a wide diagram; do not focus on a tiny endpoint object that the whole composition makes unreadable.
If claiming distinct colours, paths or states, include all of them as separate
parts, evidence for each and contrasts with the distinguishing fields. A named object moving is not sufficient evidence of a distinct internal process.
Do not use decorative motion as a substitute for the claimed mechanism.
Reference context (human supplied, do not invent external verification):
'''+context+'\nProblems: '+json.dumps(problems)+'\nSaved scene: '+json.dumps(spec,ensure_ascii=False)+'''
Return a patch JSON, not a whole new scene:
{"replace_parts":{"existing_id":{"id":"existing_id","type":"...","...":"complete replacement"}},
 "add_parts":[{"id":"unique_new_id","type":"..."}],
 "step_updates":[{"index":0,"say":"optional corrected narration","demonstration":"what is actually visible",
 "shows":"focus id","evidence":[{"part":"id","field":"progress","at":[start,end],"values":[0,1]}],
 "contrasts":[{"parts":["id1","id2"],"fields":["color","pts"]}]}],
 "principle":"optional corrected mechanism"}
Use only catalog fields (numeric values may be keyframes); line: pts/color/w/progress/alpha;
path: d/x/y/scale/rot/fill/stroke/lw/alpha/draw; ellipse: x/y/rx/ry/rot/fill/stroke/lw/alpha.
SVG path local y is DOWN; world y is UP. Keep the drawings centred near their placement.
Use as many separate parts as the demonstration needs. Preserve sound and music settings.
'''
        try:
            patch=_call(llm,prompt,.25,attempt,log)
            candidate=apply_patch(spec,patch)
            errors=check(candidate)
        except llm.BudgetExceeded: raise
        except Exception as e:
            problems=[str(e)[:200]];log('repair patch unusable: '+problems[0]);continue
        Path('attempts').mkdir(exist_ok=True)
        Path('attempts/repair-%d.json' % attempt).write_text(json.dumps({'candidate':candidate,'patch':patch,'errors':errors},indent=1,ensure_ascii=False))
        if not errors:
            candidate['repair_provenance']={'method':'bounded automatic patch of saved scene',
                'replaced_parts':list(patch.get('replace_parts',{})),
                'added_parts':[p['id'] for p in patch.get('add_parts',[])],
                'changed_steps':[u['index']+1 for u in patch.get('step_updates',[])],
                'semantic_verification':False}
            log('repair patch passed structural checks; rendered and factual review still required')
            return candidate
        spec=candidate;problems=errors
        log('repair patch rejected: '+' | '.join(errors[:6]))
    raise ValueError('bounded repair did not pass; original scene and failure evidence retained')


if __name__=='__main__':
    # repair.py saved-scene.json report.json output.json [reference-context.txt]
    spec=json.loads(Path(sys.argv[1]).read_text()); report=json.loads(Path(sys.argv[2]).read_text())
    context=Path(sys.argv[4]).read_text() if len(sys.argv)>4 else ''
    lines=[]
    def log(m): print(m,flush=True);lines.append(m)
    try:
        new=repair(spec,report.get('errors',[]),context,log)
        Path(sys.argv[3]).write_text(json.dumps(new,indent=1,ensure_ascii=False))
    finally: Path('repair-log.txt').write_text('\n'.join(lines))
