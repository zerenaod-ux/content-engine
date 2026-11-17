"""Persistent full-history topic guard; no expiry or recent-history truncation.

Rejects exact/canonical and close lexical repeats. This is not a proof that all
possible paraphrases are semantically distinct. Reservations persist before media.
"""
import json,re,unicodedata
from pathlib import Path
STOP=set('a an the how why what does do is are of in on to from with and or for its it your you that this into up down out by at as be can make makes work works so than when where which who'.split())
ALIASES={'bulb':'lamp','bulbs':'lamp','lamps':'lamp','lights':'light','lighting':'light','turning':'turn','turns':'turn','rotating':'rotate','rotation':'rotate','electricity':'electric','electrical':'electric','power':'electric','powers':'electric'}
def signature(text):
    text=unicodedata.normalize('NFKD',str(text)).lower()
    tokens=[ALIASES.get(w,w) for w in re.findall(r'[a-z0-9]+',text) if w not in STOP]
    return ' '.join(sorted(set(tokens)))
def read_list(path,required=False):
    p=Path(path)
    if not p.exists():
        if required:raise ValueError('Historical topic data is missing; refusing to reset no-repeat memory')
        return []
    rows=json.loads(p.read_text())
    if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):raise ValueError('Topic history is malformed; no generation allowed')
    return rows

def history(root=Path('data/scenes'),owner=None):
    root=Path(root)
    rows=read_list(root/'history.json',True)+read_list(root/'videos.json',True)
    rows += [r for r in read_list(root/'topic-ledger.json') if str(r.get('owner'))!=str(owner) or owner is None]
    return [r for r in rows if not r.get('failed')]

def duplicate(topic,rows):
    key=signature(topic);words=set(key.split())
    if len(words)<2:return 'Topic is too vague'
    for row in rows:
        for prior in (row.get('topic',''),row.get('title',''),row.get('topic_key','')):
            old=signature(prior);other=set(old.split())
            if old and (key==old or (len(words&other)>=3 and len(words&other)/max(1,len(words|other))>=.65)):
                return 'Topic repeats an existing or reserved explanation'
    return ''

def require_new(topic,root=Path('data/scenes'),owner=None):
    reason=duplicate(topic,history(root,owner))
    if reason:raise ValueError(reason)
    return signature(topic)

def reserve(topic,root=Path('data/scenes'),owner=None):
    if not owner:raise ValueError('A durable generation owner is required for reservations')
    root=Path(root);key=require_new(topic,root,owner)
    rows=read_list(root/'topic-ledger.json')
    if any(str(r.get('owner'))==str(owner) and r.get('topic_key')==key for r in rows):return key
    rows.append({'topic':topic,'topic_key':key,'owner':str(owner),'state':'reserved'})
    p=root/'topic-ledger.json';temp=p.with_suffix('.tmp');temp.write_text(json.dumps(rows,indent=2)+'\n');temp.replace(p)
    return key
