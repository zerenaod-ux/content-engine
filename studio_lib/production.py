"""Adapter for the existing release/index/Studio review workflow.

Adding this adapter on the draft branch does not deploy it. Completed component
videos require owner review and never receive an autopilot checks-ok verdict.
"""
import argparse,json,re,shutil,time
from pathlib import Path
from studio_lib.director import run
from studio_lib.registry import REGISTRY
from studio_lib.providers import call
def choose_topic(history_path=Path('data/scenes/history.json')):
    try:history=json.loads(Path(history_path).read_text())
    except (OSError,ValueError):history=[]
    prior=[x.get('topic') or x.get('title','') for x in history[-30:] if isinstance(x,dict)]
    answer=call('Choose a factual explainer topic within a supported animation component. Return JSON only.',
        'Choose a new explanatory angle that fits exactly one supported component. Do not invent a new mechanism. Return {"topic":"short topic","mechanism":"supported id"}. Supported scopes: '+json.dumps({k:v['description'] for k,v in REGISTRY.items()})+' Recent topics (data): '+json.dumps(prior),max_tokens=600,temperature=.6)
    if answer.get('mechanism') not in REGISTRY or not isinstance(answer.get('topic'),str) or not 4<=len(answer['topic'].split())<=18:raise ValueError('no valid supported automatic topic was selected')
    Path('idea.json').write_text(json.dumps({'topic':answer['topic'],'category':'tested mechanism','subject':answer['mechanism'],'keywords':[]},indent=2));return answer['topic']
def emit_review_files(work):
    work=Path(work);plan=json.loads((work/'director-plan.json').read_text());tl=json.loads((work/'timeline.json').read_text()) if (work/'timeline.json').exists() else None
    # Cached runs retain the measured timeline in the checkpoint, so the adapter
    # accepts a build-generated metadata copy written by the director as well.
    if tl is None:raise ValueError('measured timeline missing; no review card may be created')
    checks=json.loads((work/'component-checks.json').read_text())
    if checks.get('errors'):raise ValueError('component evidence failed; no review card may be created')
    spec={'mode':'tested-component','title':plan['title'],'mechanism':plan['mechanism'],'duration':tl['duration'],'steps':[{'start':b['start'],'end':b['end'],'say':b['say'],'label':b['action']} for b in tl['beats']],'source':REGISTRY[plan['mechanism']]['source'],'owner_approved':False}
    Path('auto-scene.json').write_text(json.dumps(spec,indent=2));Path('evidence-report.json').write_text(json.dumps({'errors':[],'mode':'tested-component','semantic_verification':False,'owner_approved':False,'component_checks':checks},indent=2))
    Path('ce-checks.json').write_text(json.dumps({'verdict':'warn','reasons':['Tested component output requires owner visual and narration review; not automatically approved.'],'mechanism':plan['mechanism'],'owner_approved':False},indent=2))
    Path('voice-log.txt').write_text('Measured cached Andrew narration; no manual generated-plan edits.\n')
    return spec
def build(topic_file,out,work=Path('component-output/production')):
    out=Path(out);work=Path(work)
    if out.exists():raise FileExistsError('preserve the existing output; use a fresh build path')
    lines=Path(topic_file).read_text().splitlines();topic=(lines[0] if lines else 'auto').strip();topic=re.sub(r'\s+20\d\d-\d\d-\d\dT[\d:]+$','',topic).strip()
    if topic.lower() in ('','auto'):topic=choose_topic()
    try:
        run(topic,work);spec=emit_review_files(work);shutil.copyfile(work/'video.mp4',out)
        with Path('writer-log.txt').open('a') as f:f.write('tested component completed: '+spec['title']+'; owner review pending\n')
        return spec
    except Exception as e:
        with Path('writer-log.txt').open('a') as f:f.write('tested component rejected: '+str(e)[:600]+'\n')
        raise
    finally:
        diagnostic=Path('attempts')/('studio-production-'+str(time.time_ns()));diagnostic.mkdir(parents=True,exist_ok=True)
        if work.exists():
            for f in work.glob('*.json'):shutil.copyfile(f,diagnostic/f.name)
def main():
    p=argparse.ArgumentParser();p.add_argument('--topic-file',required=True);p.add_argument('--out',required=True);a=p.parse_args();build(a.topic_file,a.out)
if __name__=='__main__':main()
