from studio_lib.cinema.topic_memory import prompt_history
"""Select and reserve a supported new topic on GitHub before media generation."""
import base64,json,os,time,urllib.request,urllib.error
from pathlib import Path
from studio_lib.providers import call
from studio_lib import novelty
from studio_lib.topic_guard import duplicate,signature
from studio_lib.cinema.coverage import topic_brief
from studio_lib.science.components import SPECS

REPO='zerenaod-ux/content-engine'

def api(path,body=None):
    headers={'Accept':'application/vnd.github+json'}
    token=os.environ.get('GH_TOKEN','')
    if token:headers['Authorization']='Bearer '+token
    if body is not None:headers['Content-Type']='application/json'
    req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers=headers,data=json.dumps(body).encode() if body is not None else None,method='PUT' if body is not None else 'GET')
    with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)

def read(path):
    item=api('contents/'+path+'?ref=main')
    return json.loads(base64.b64decode(item['content'])),item['sha']

def candidate_valid(candidate,rows):
    if not isinstance(candidate,dict) or not isinstance(candidate.get('topic'),str):return 'Missing topic'
    brief=topic_brief(candidate['topic'])
    if brief['mechanism']!=candidate.get('mechanism') or not brief['mechanism']:return 'Topic does not match its implemented component'
    reason=novelty.reason(candidate['topic'],candidate['mechanism'],rows)
    if reason:return reason
    # For this proof, a new wording of a previously covered cinematic component
    # is insufficient. This is deliberately stricter than the daily topic guard.
    for row in rows:
        old=row.get('topic') or row.get('title') or ''
        try:
            if topic_brief(old)['mechanism']==brief['mechanism']:return 'This component has already been covered; select an uncovered component'
        except ValueError:pass
    return ''

def main():
    out=Path('cinema-output');out.mkdir(exist_ok=True)
    rows=[]
    for path in ('data/scenes/history.json','data/scenes/videos.json'):
        data,_=read(path)
        if not isinstance(data,list):raise ValueError('Invalid full-history data')
        rows.extend(data)
    ledger,sha=read('data/scenes/topic-ledger.json');rows+=ledger
    rows+=novelty.records()
    recovery=Path('publish/cinema.resume.json')
    config=json.loads(recovery.read_text()) if recovery.exists() else {}
    if config.get('repair') is True:
        raise ValueError('Completed-video regeneration is forbidden by the permanent no-repeat policy')
        source=api('actions/runs/'+str(config['run_id']))
        if source.get('head_branch')!='studio-cinematic-proof' or source.get('name')!='Cinematic system comparison (not posted)' or source.get('conclusion')!='success':raise ValueError('Untrusted repair source')
        topic=config['topic']
        if not any(str(r.get('owner'))==str(config['run_id']) and r.get('topic')==topic for r in ledger):raise ValueError('Repair topic lacks its original automatic reservation')
        Path('publish/cinema.topic').write_text(topic+'\n')
        (out/'automatic-topic-selection.json').write_text(json.dumps({'selected_by_system':True,'repair_of_run':config['run_id'],'topic':topic,'new_topic_count':0},indent=2))
        return
    owned=[r for r in ledger if str(r.get('owner'))==str(os.environ['GITHUB_RUN_ID']) and r.get('format')!='original_full']
    if owned:
        topic=owned[-1]['topic'];Path('publish/cinema.topic').write_text(topic+'\n')
        (out/'automatic-topic-selection.json').write_text(json.dumps({'selected_by_system':True,'resumed_reservation':True,'topic':topic},indent=2))
        return
    covered=set()
    for row in rows:
        for key in ('topic','title'):
            try:
                found=topic_brief(row.get(key,''))['mechanism']
                if found:covered.add(found)
            except ValueError:pass
    phrases={'lever_balance':'lever','resistive_circuit':'resistor circuit','hydraulic_lift':'hydraulic lift','thermal_contact':'thermal contact','dna_pairing':'DNA base pairing','water_transfer':'water between reservoirs'}
    available={key:{'scope':value[0],'required_topic_phrase':phrases[key]} for key,value in SPECS.items() if key not in covered}
    available=novelty.unused(available,rows,os.environ.get('GITHUB_RUN_ID'))
    if not available:raise ValueError('No uncovered supported component remains; no repeat will be generated')
    rejected=[]
    for attempt in range(4):
        candidate=call('Choose an original supported explainer subject. Return JSON only.',
            'The system must select a genuinely new topic, never a paraphrase of a past video. Pick an uncovered implemented component. Return {"topic":"How/Why topic","mechanism":"exact supported id"}. '
            'Choose only one of the UNCOVERED scopes below and include its required_topic_phrase literally inside the topic. Explain only that precise scope, not a whole process absent from the diagram. Prefer visible causal changes. UNCOVERED: '+json.dumps(available)+' FULL HISTORY: '+json.dumps(prompt_history(rows))+' REJECTIONS: '+json.dumps(rejected),max_tokens=700,temperature=.6)
        (out/f'topic-candidate-{attempt}.json').write_text(json.dumps(candidate,indent=2))
        error=candidate_valid(candidate,rows)
        if error:rejected.append(error);continue
        topic=candidate['topic'];owner=str(os.environ['GITHUB_RUN_ID'])
        for conflict in range(4):
            ledger,sha=read('data/scenes/topic-ledger.json')
            if duplicate(topic,[r for r in ledger if str(r.get('owner'))!=owner]):raise ValueError('Topic was concurrently reserved; no media generated')
            if not any(str(r.get('owner'))==owner for r in ledger):ledger.append({'topic':topic,'topic_key':signature(topic),'owner':owner,'state':'reserved','mechanism':candidate['mechanism']})
            body={'message':'Reserve system-selected new cinematic topic','branch':'main','sha':sha,'content':base64.b64encode((json.dumps(ledger,indent=2)+'\n').encode()).decode()}
            try:api('contents/data/scenes/topic-ledger.json',body);break
            except urllib.error.HTTPError as e:
                if e.code not in (409,422) or conflict==3:raise
                time.sleep(2)
        Path('publish/cinema.topic').write_text(topic+'\n')
        (out/'automatic-topic-selection.json').write_text(json.dumps({'selected_by_system':True,'candidate':candidate,'history_records':len(rows),'reserved_before_media':True},indent=2))
        print('System selected and reserved a previously uncovered component topic',flush=True);return
    raise ValueError('No genuinely new supported topic passed selection; no media generated')
if __name__=='__main__':main()
