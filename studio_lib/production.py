"""Adapter for the existing release/index/Studio review workflow.

Adding this adapter on the draft branch does not deploy it. Completed component
videos require owner review and never receive an autopilot checks-ok verdict.
"""
import argparse,json,os,re,shutil,time
from pathlib import Path
from studio_lib.director import run
from studio_lib.registry import REGISTRY
from studio_lib.providers import call
from studio_lib import novelty
from studio_lib.topic_guard import history,duplicate,require_new,reserve,signature
from studio_lib import durable_topics as durable
from studio_lib.topic_scope import scope_error,require_supported
def choose_topic(history_path=Path('data/scenes/history.json')):
    rows=history(Path(history_path).parent,os.environ.get('GITHUB_RUN_ID'))
    rows+=novelty.records()
    available=novelty.unused(REGISTRY,rows,os.environ.get('GITHUB_RUN_ID'))
    if os.environ.get('CE_FORCE_RECIPE')=='true':return recipe_topic(rows)   # manual test only; automatic kit fallback PAUSED 2026-11-23 (owner: far weaker than hand-built machines)
    if not available:raise ValueError('No unused hand-built machine remains; kit-recipe fallback is paused until the owner approves it')

    prior=[x.get('topic') or x.get('title','') for x in rows if x.get('topic') or x.get('title')]
    errors=[]
    for attempt in range(4):
        answer=call('Choose a factual explainer topic within a supported animation component. Return JSON only.',
            'Choose a genuinely new explanatory question, not a rewording of an earlier video. Its causal change must be visible in the supplied action facts. Never choose bearing friction/lubrication, measured efficiency, or another unshown detail. Do not invent a new mechanism. Return {"topic":"short topic","mechanism":"supported id"}. Supported scopes: '+json.dumps({k:{'description':v['description'],'actions':v['facts']} for k,v in available.items()})+' Recent examples (data): '+json.dumps(prior[-60:])+' Rejected candidates (data): '+json.dumps(errors),max_tokens=600,temperature=.6)
        if answer.get('mechanism') not in REGISTRY or not isinstance(answer.get('topic'),str) or not 4<=len(answer['topic'].split())<=18:raise ValueError('no valid supported automatic topic was selected')
        reason=scope_error(answer['topic'],answer['mechanism']) or novelty.reason(answer['topic'],answer['mechanism'],rows,os.environ.get('GITHUB_RUN_ID'))
        if reason:
            errors.append({'topic':answer['topic'],'reason':reason});continue
        Path('idea.json').write_text(json.dumps({'topic':answer['topic'],'topic_key':signature(answer['topic']),'category':'tested mechanism','subject':answer['mechanism'],'selected_by_system':True,'selection_owner':os.environ.get('GITHUB_RUN_ID'),'keywords':[]},indent=2));return answer['topic']
    raise ValueError('No non-repeating supported topic survived the full-history checks')

def recipe_topic(rows):
    """Unlimited supply: the free LLM invents a new everyday object as a recipe of tested kit parts; every check still applies."""
    from studio_lib.kit import generate,register
    from studio_lib import director
    run_id=os.environ.get('GITHUB_RUN_ID')
    prior=[x.get('topic') or x.get('title','') for x in rows if x.get('topic') or x.get('title')]
    def why(topic,key,recipe):
        register.install(recipe,director.COMPONENTS)
        return scope_error(topic,key) or novelty.reason(topic,key,rows,run_id)
    topic,recipe,key=generate.make(prior,rows,call,why)
    register.save(recipe)
    if os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GH_TOKEN'):
        # Keep the recipe on main so an automatic recovery run (new checkout) can rebuild the same machine.
        from studio_lib.service_queue import write_document
        try:write_document('data/scenes/recipes/'+key+'.json',recipe,None,'Save kit recipe '+key)
        except Exception as e:print('recipe backup skipped:',str(e)[:120],flush=True)
    Path('idea.json').write_text(json.dumps({'topic':topic,'topic_key':signature(topic),'category':'kit recipe','subject':key,'selected_by_system':True,'selection_owner':run_id,'keywords':[]},indent=2))
    return topic

def selected_mechanism(topic):
    owner=durable.reservation_owner(topic)
    if not owner:return None
    p=Path('idea.json')
    if p.exists():
        d=json.loads(p.read_text())
        if d.get('selected_by_system') is True and str(d.get('selection_owner'))==str(owner) and d.get('topic')==topic and d.get('subject') in REGISTRY:return d['subject']
    p=Path('data/scenes/topic-ledger.json')
    if p.exists():
        matches=[r for r in json.loads(p.read_text()) if str(r.get('owner'))==str(owner) and r.get('topic')==topic and r.get('mechanism') in REGISTRY]
        if len(matches)==1:return matches[0]['mechanism']
    return None

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
    require_supported(topic)
    mechanism=selected_mechanism(topic)
    novelty.require_new(topic,mechanism,owner=owner)
    if durable.enabled():
        if mechanism:durable.reserve_remote(topic,owner,mechanism=mechanism)
        else:durable.reserve_remote(topic,owner)
    else:reserve(topic,owner=owner)
    topic_file.write_text(topic+'\n')
    return topic

def emit_review_files(work):
    from studio_lib.quality_gate import require_seal
    sealed=require_seal(work,'short')
    work=Path(work);plan=json.loads((work/'director-plan.json').read_text());tl=json.loads((work/'timeline.json').read_text()) if (work/'timeline.json').exists() else None
    # Cached runs retain the measured timeline in the checkpoint, so the adapter
    # accepts a build-generated metadata copy written by the director as well.
    if tl is None:raise ValueError('measured timeline missing; no review card may be created')
    checks=json.loads((work/'component-checks.json').read_text())
    if checks.get('errors'):raise ValueError('component evidence failed; no review card may be created')
    recipe_data=json.loads(Path('data/scenes/recipes',plan['mechanism']+'.json').read_text()) if plan['mechanism'].startswith('recipe_') and Path('data/scenes/recipes',plan['mechanism']+'.json').is_file() else None
    emoji={'wind_turbine':' 💨','photovoltaic_cell':' 🌞','piston_pump':' 💧','bascule_bridge':' 🚢'}.get(plan['mechanism'],' ⚙️')
    title=plan['title'] if any(ord(c)>0x2500 for c in plan['title']) else plan['title'].rstrip('.')+emoji
    spec={'topic':Path('topic.txt').read_text().strip() if Path('topic.txt').exists() else plan['title'],'topic_key':signature(Path('topic.txt').read_text().strip() if Path('topic.txt').exists() else plan['title']),'mode':'tested-component','title':title,'mechanism':plan['mechanism'],'visual_family':novelty.identity('',plan['mechanism']),'novelty_policy':novelty.POLICY,'story_policy':plan.get('story_policy'),'voice':tl.get('voice'),'voice_policy':tl.get('voice_policy'),'duration':tl['duration'],'steps':[{'start':b['start'],'end':b['end'],'say':b['say'],'label':b['action']} for b in tl['beats']],'source':REGISTRY[plan['mechanism']]['source'],'owner_approved':False}
    origin={'event':os.environ.get('GITHUB_EVENT_NAME'),'automatic_slot':os.environ.get('CE_AUTOMATIC_SLOT')=='true','run_id':os.environ.get('GITHUB_RUN_ID'),'attempt':int(os.environ.get('GITHUB_RUN_ATTEMPT','1')),'event_sha':os.environ.get('GITHUB_SHA'),'source_ref':os.environ.get('GITHUB_REF_NAME'),'manual_media_edits':False}
    spec['generation_origin']=origin
    if recipe_data:spec['recipe']=recipe_data
    spec['production_evidence']={'policy':'unattended-proof-v1','novelty_policy':novelty.POLICY,'width':sealed['width'],'height':sealed['height'],'duration':sealed['duration'],'media_sha256':sealed['hashes']['video.mp4'],'alignment_revision':json.loads((work/'spoken-action-timing.json').read_text()).get('alignment_revision') if (work/'spoken-action-timing.json').is_file() else None,'render_policy':plan.get('render_policy'),'voice':tl.get('voice'),'voice_policy':tl.get('voice_policy'),'errors':[],'owner_approved':False}
    Path('auto-scene.json').write_text(json.dumps(spec,indent=2));Path('evidence-report.json').write_text(json.dumps({'errors':[],'mode':'tested-component','semantic_verification':False,'owner_approved':False,'component_checks':checks,'story_checks':json.loads((work/'story-checks.json').read_text()) if (work/'story-checks.json').exists() else None,'causal_motion_checks':json.loads((work/'causal-motion-checks.json').read_text()) if (work/'causal-motion-checks.json').exists() else None},indent=2))
    Path('ce-checks.json').write_text(json.dumps({'verdict':'warn','reasons':['Tested component output requires owner visual and narration review; not automatically approved.'],'mechanism':plan['mechanism'],'owner_approved':False},indent=2))
    Path('voice-log.txt').write_text('Measured narration; provider '+str(tl.get('voice_provider','edge-tts'))+'; cached lines '+str(tl.get('cached_lines',0))+'; no manual generated-plan edits.\n')
    return spec
def build(topic_file,out,work=Path('component-output/production')):
    out=Path(out);work=Path(work)
    if out.exists():raise FileExistsError('preserve the existing output; use a fresh build path')
    lines=Path(topic_file).read_text().splitlines();topic=(lines[0] if lines else 'auto').strip();topic=re.sub(r'\s+20\d\d-\d\d-\d\dT[\d:]+$','',topic).strip()
    if topic.lower() in ('','auto'):topic=choose_topic()
    require_supported(topic)
    require_new(topic,owner=durable.reservation_owner(topic))
    try:
        mechanism=selected_mechanism(topic)
        if mechanism:run(topic,work,mechanism=mechanism)
        else:run(topic,work)
        spec=emit_review_files(work);shutil.copyfile(work/'video.mp4',out)
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

