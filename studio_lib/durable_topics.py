"""Conflict-safe daily reservations and append-only production records.

Concurrent stage/lease writers must never require a JSON git-rebase merge.
Only newly produced local records are merged into the latest remote document.
"""
import argparse,copy,json,os,time,urllib.error
from pathlib import Path
from studio_lib.service_queue import read_document,write_document,github
from studio_lib.topic_guard import duplicate,signature

BASE=Path('topic-record-baseline.json')
PATHS=('data/scenes/history.json','data/scenes/videos.json')
LEDGER='data/scenes/topic-ledger.json'

def enabled():
    return os.environ.get('GITHUB_ACTIONS')=='true' and bool(os.environ.get('GH_TOKEN'))

def rows(path,required=True):
    data,sha=read_document(path,None)
    if data is None and not required:return [],sha
    if not isinstance(data,list) or any(not isinstance(r,dict) for r in data):
        raise ValueError('Historical topic data missing or malformed: '+path)
    return data,sha

def refresh_history():
    baseline={}
    for path in (*PATHS,LEDGER):
        data,_=rows(path,required=path!=LEDGER)
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(data,indent=2)+'\n')
        if path in PATHS:baseline[path]=data
    BASE.write_text(json.dumps(baseline))

def reserve_remote(topic,owner,mechanism=None):
    for attempt in range(6):
        ledger,sha=rows(LEDGER,False)
        complete=[]
        for path in PATHS:complete+=rows(path)[0]
        prior=[r for r in ledger if str(r.get('owner'))==str(owner)]
        if prior and any(r.get('topic')!=topic for r in prior):
            raise ValueError('This run already reserved a different topic')
        reason=duplicate(topic,[r for r in complete if not r.get('failed')]+[r for r in ledger if not r.get('failed') and str(r.get('owner'))!=str(owner)])
        if reason:raise ValueError(reason)
        if prior:
            Path(LEDGER).write_text(json.dumps(ledger,indent=2)+'\n');return
        row={'topic':topic,'topic_key':signature(topic),'owner':str(owner),'state':'reserved'}
        if mechanism:
            from studio_lib.novelty import identity
            row.update(mechanism=mechanism,visual_family=identity(topic,mechanism))
        ledger.append(row)
        try:
            write_document(LEDGER,ledger,sha,'Reserve unique daily topic without git rebase')
            Path(LEDGER).write_text(json.dumps(ledger,indent=2)+'\n');return
        except urllib.error.HTTPError as e:
            if e.code not in (409,422) or attempt==5:raise
            time.sleep(1)

def resume_topic(source_run):
    source=github('actions/runs/'+str(source_run))
    if source.get('head_branch')!='main' or source.get('name')!='scene-factory' or source.get('conclusion')!='failure':
        raise ValueError('Untrusted daily recovery source')
    ledger,_=rows(LEDGER)
    owned=[r for r in ledger if str(r.get('owner'))==str(source_run)]
    if len(owned)!=1:raise ValueError('Original daily reservation is missing or ambiguous')
    topic=owned[0]['topic']
    Path('daily-resume-provenance.json').write_text(json.dumps({'source_run':str(source_run),'current_run':os.environ['GITHUB_RUN_ID'],'topic':topic,'new_topic_count':0}))
    return topic,str(source_run)

def reservation_owner(topic):
    p=Path('daily-resume-provenance.json')
    if p.exists():
        d=json.loads(p.read_text())
        if d.get('current_run')==os.environ.get('GITHUB_RUN_ID') and d.get('topic')==topic:return d['source_run']
    return os.environ.get('GITHUB_RUN_ID')

def key(row):return json.dumps(row,sort_keys=True,separators=(',',':'))

def save_records():
    if not enabled():raise ValueError('Remote record persistence requires the cloud job token')
    baseline=json.loads(BASE.read_text())
    for path in PATHS:
        local=json.loads(Path(path).read_text());before={key(r) for r in baseline[path]}
        changes=[copy.deepcopy(r) for r in local if key(r) not in before]
        if not changes:continue
        for row in changes:
            row.setdefault('record_run',os.environ['GITHUB_RUN_ID'])
            row.setdefault('record_attempt',os.environ.get('GITHUB_RUN_ATTEMPT','1'))
        for attempt in range(6):
            remote,sha=rows(path)
            identities={r.get('tag') or key(r) for r in remote}
            merged=list(remote)
            for row in changes:
                identity=row.get('tag') or key(row)
                if identity not in identities:
                    merged.append(row);identities.add(identity)
            if merged==remote:break
            try:
                write_document(path,merged,sha,'Retain generated records without git rebase');break
            except urllib.error.HTTPError as e:
                if e.code not in (409,422) or attempt==5:raise
                time.sleep(1)
        baseline[path]=local
    BASE.write_text(json.dumps(baseline))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['save-records'])
    parser.parse_args();save_records()
