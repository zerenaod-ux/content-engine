"""Adapter for the existing release/index/Studio review workflow.

Adding this adapter on the draft branch does not deploy it. Completed component
videos require owner review and never receive an autopilot checks-ok verdict.
"""
import argparse,json,os,re,shutil,time
from pathlib import Path
from studio_lib.director import run
from studio_lib.registry import REGISTRY
from studio_lib.providers import call
from studio_lib.topic_guard import history,duplicate,require_new,reserve,signature
from studio_lib import durable_topics as durable
def choose_topic(history_path=Path('data/scenes/history.json')):
    rows=history(Path(history_path).parent,os.environ.get('GITHUB_RUN_ID'))
    prior=[x.get('topic') or x.get('title','') for x in rows if x.get('topic') or x.get('title')]
    errors=[]
    for attempt in range(4):
        answer=call('Choose a factual explainer topic within a supported animation component. Return JSON only.',
            'Choose a genuinely new explanatory question, not a rewording of an earlier video. Do not invent a new mechanism. Return {"topic":"short topic","mechanism":"supported id"}. Supported scopes: '+json.dumps({k:v['description'] for k,v in REGISTRY.items()})+' Recent examples (data): '+json.dumps(prior[-60:])+' Rejected candidates (data): '+json.dumps(errors),max_tokens=600,temperature=.6)
        if answer.get('mechanism') not in REGISTRY or not isinstance(answer.get('topic'),str) or not 4<=len(answer['topic'].split())<=18:raise ValueError('no valid supported automatic topic was selected')
        reason=duplicate(answer['topic'],rows)
        if reason:
            errors.append({'topic':answer['topic'],'reason':reason});continue
        Path('idea.json').write_text(json.dumps({'topic':answer['topic'],'topic_key':signature(answer['topic']),'category':'tested mechanism','subject':answer['mechanism'],'keywords':[]},indent=2));return answer['topic']
    raise ValueError('No non-repeating supported topic survived the full-history checks')

def prepare(topic_file):
    if durable.enabled():durable.refresh_history()
    topic_file=Path(topic_file);lines=topic_file.read_text().splitlines();topic=(lines[0] if lines else 'auto').strip();topic=re.sub(r'\s+20\d\d-\d\d-\d\dT[\d:]+$','',topic).strip()
    recovered=re.fullmatch(r'resume (\d+)',topic)
    owner=os.environ.get('GITHUB_RUN_ID')
    if recovered:
        if not durable.enabled():raise ValueError('Daily recovery requires a verified cloud source')
        topic,owner=durable.resume_topic(recovered.group(1))
    if topic.lower() in ('','auto'):
        ledger=Path('data/scenes/topic-ledger.json')
        owned=[r for r in json.loads(ledger.read_text()) if str(r.get('owner'))==str(os.environ.get('GITHUB_RUN_ID'))] if ledger.exists() else []
        topic=owned[-1]['topic'] if owned else choose_topic()
    if durable.enabled():durable.reserve_remote(topic,owner)
    else:reserve(topic,owner=owner)
    topic_file.write_text(topic+'\n')
    return topic

def emit_review_files(work):
    work=Path(work);plan=json.loads((work/'director-plan.json').read_text());tl=json.loads((work/'timeline.json').read_text()) if (work/'timeline.json').exists() else None
    # Cached runs retain the measured timeline in the checkpoint, so the adapter
    # accepts a build-generated metadata copy written by the director as well.
    if tl is None:raise ValueError('measured timeline missing; no review card may be created')
    checks=json.loads((work/'component-checks.json').read_text())
    if checks.get('errors'):raise ValueError('component evidence failed; no review card may be created')
    emoji={'wind_turbine':' 💨','photovoltaic_cell':' 🌞','piston_pump':' 💧','bascule_bridge':' 🚢'}.get(plan['mechanism'],' ⚙️')
    title=plan['title'] if any(ord(c)>0x2500 for c in plan['title']) else plan['title'].rstrip('.')+emoji
    spec={'topic':Path('topic.txt').read_text().strip() if Path('topic.txt').exists() else plan['title'],'topic_key':signature(Path('topic.txt').read_text().strip() if Path('topic.txt').exists() else plan['title']),'mode':'tested-component','title':title,'mechanism':plan['mechanism'],'duration':tl['duration'],'steps':[{'start':b['start'],'end':b['end'],'say':b['say'],'label':b['action']} for b in tl['beats']],'source':REGISTRY[plan['mechanism']]['source'],'owner_approved':False}
    Path('auto-scene.json').write_text(json.dumps(spec,indent=2));Path('evidence-report.json').write_text(json.dumps({'errors':[],'mode':'tested-component','semantic_verification':False,'owner_approved':False,'component_checks':checks},indent=2))
    Path('ce-checks.json').write_text(json.dumps({'verdict':'warn','reasons':['Tested component output requires owner visual and narration review; not automatically approved.'],'mechanism':plan['mechanism'],'owner_approved':False},indent=2))
    Path('voice-log.txt').write_text('Measured cached Andrew narration; no manual generated-plan edits.\n')
    return spec
def build(topic_file,out,work=Path('component-output/production')):
    out=Path(out);work=Path(work)
    if out.exists():raise FileExistsError('preserve the existing output; use a fresh build path')
    lines=Path(topic_file).read_text().splitlines();topic=(lines[0] if lines else 'auto').strip();topic=re.sub(r'\s+20\d\d-\d\d-\d\dT[\d:]+$','',topic).strip()
    if topic.lower() in ('','auto'):topic=choose_topic()
    require_new(topic,owner=durable.reservation_owner(topic))
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
    p=argparse.ArgumentParser();p.add_argument('--topic-file',required=True);p.add_argument('--out',required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args();prepare(a.topic_file) if a.prepare_only else build(a.topic_file,a.out)
if __name__=='__main__':main()

