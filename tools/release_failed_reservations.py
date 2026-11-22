"""Free machines that were reserved by a run which FAILED and never produced a video (owner request 2026-11-21).
A failed script check must not burn a machine forever. Usage: python3 tools/release_failed_reservations.py RUN_ID [RUN_ID ...]
Removes only rows that belong to those runs and have no video/tag; prints what it removed."""
import json,sys
from pathlib import Path
runs=set(sys.argv[1:]);root=Path(__file__).resolve().parent.parent
def produced(r):return any(r.get(k) for k in ('video','tag','media_sha256','published_at','scheduled_at')) or r.get('state') in ('created','rendered','scheduled','published','skipped','deleted','saved')
for name,keys in (('data/scenes/novelty-ledger.json',('owner','record_run','run_id')),('data/scenes/topic-ledger.json',('owner','record_run','run_id')),('data/scenes/history.json',('record_run','owner','run_id'))):
    p=root/name;rows=json.loads(p.read_text());keep=[];gone=[]
    for r in rows:
        mine=any(str(r.get(k)) in runs for k in keys)
        if mine and not produced(r) and (r.get('state')=='reserved' or r.get('failed') in (True,'True')):gone.append(r)
        else:keep.append(r)
    if gone:
        p.write_text(json.dumps(keep,indent=2,ensure_ascii=False)+'\n');print(name,'removed',len(gone),[g.get('topic','')[:50] for g in gone])
