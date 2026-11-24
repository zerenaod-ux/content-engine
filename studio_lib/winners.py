"""Winners loop: learn which machines and question styles the channel and the owner like, and steer the next topic toward them.

Signals, strongest first:
  1. Owner verdicts in data/scenes/review/index.json (folder 'saved' = liked, 'delete' = removed). Available for every reviewed video.
  2. YouTube views and average view percentage, when data/analytics/video-map.json links video ids to tags
     (the connected analytics report lists ids and views but not tags, so without that map views are not used; nothing is guessed).
Output: data/scenes/winners.json (readable report) and two helpers used by topic choice:
  weights()  -> {machine: -1..1}  small nudge when picking the next (machine, story); never excludes a machine
  hint()     -> one sentence of liked/removed titles for the topic prompt
Everything is fail-open: missing or broken data returns neutral values."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT='data/scenes/winners.json'

def _read(path,default):
 try:return json.loads((ROOT/path).read_text())
 except (OSError,ValueError):return default

def _machine_of(title,story=None):
 from studio_lib import novelty
 fams=novelty.families({'title':title,'topic':title,'story':story})
 inv={}
 for k,v in novelty.FAMILIES.items():inv.setdefault(novelty.story_of(v)[0],k)
 for f in sorted(fams):
  base=novelty.story_of(f)[0]
  if base in inv and not inv[base].startswith('recipe_'):return inv[base]
 return None

def collect():
 """Per machine: reviewed count, saved, deleted, views (when linked)."""
 idx=_read('data/scenes/review/index.json',{}).get('items',[])
 videos={r.get('tag'):r for r in _read('data/scenes/videos.json',[]) if isinstance(r,dict)}
 vmap=_read('data/analytics/video-map.json',{})
 stats=_read('data/analytics/howitticks-vidiq.json',{}).get('videos',[]) if isinstance(vmap,dict) and vmap else []
 byid={v.get('video'):v for v in stats if isinstance(v,dict)}
 per={};liked=[];removed=[]
 for it in idx:
  if not isinstance(it,dict) or it.get('folder') not in ('saved','delete'):continue
  row=videos.get(it.get('tag'),{});title=str(it.get('title') or row.get('title') or '')
  m=row.get('mechanism') or _machine_of(title,row.get('story'))
  if not m:continue
  d=per.setdefault(m,{'reviewed':0,'saved':0,'deleted':0,'views':0,'avp':[]})
  d['reviewed']+=1
  if it['folder']=='saved':d['saved']+=1;liked.append(title)
  else:d['deleted']+=1;removed.append(title)
 for yid,tag in (vmap.get('ids',{}) if isinstance(vmap,dict) else {}).items():
  v=byid.get(yid);row=videos.get(tag,{})
  m=row.get('mechanism') or _machine_of(str(row.get('title','')),row.get('story'))
  if v and m:
   d=per.setdefault(m,{'reviewed':0,'saved':0,'deleted':0,'views':0,'avp':[]});d['views']+=int(v.get('views',0));d['avp'].append(float(v.get('averageViewPercentage',0)))
 return per,liked,removed

def score(d,max_views=0):
 verdict=(d['saved']-d['deleted'])/(d['reviewed']+1) if d['reviewed'] else 0.
 views=(d['views']/max_views) if max_views else 0.
 w=.6*verdict+.4*views if max_views else verdict
 return max(-1.,min(1.,round(w,3)))

def report():
 per,liked,removed=collect();mx=max([d['views'] for d in per.values()] or [0])
 weights={m:score(d,mx) for m,d in per.items()}
 ranked=sorted(weights.items(),key=lambda kv:-kv[1])
 return {'policy':'winners-v1','signals':{'owner_verdicts':sum(d['reviewed'] for d in per.values()),'views_linked':bool(mx)},'weights':weights,'ranked':[m for m,_ in ranked],'liked_titles':liked[-8:],'removed_titles':removed[-8:],
         'note':'weights nudge the next pick; they never exclude a machine. Views are used only when data/analytics/video-map.json links ids to tags.'}

def weights():
 try:return report()['weights']
 except Exception:return {}

def hint():
 try:
  r=report()
  if not r['liked_titles'] and not r['removed_titles']:return ''
  return 'What the owner kept (copy this kind of plain, concrete question): '+json.dumps(r['liked_titles'][-5:])+'. What the owner removed (avoid this style): '+json.dumps(r['removed_titles'][-5:])+'. '
 except Exception:return ''

def write(path=None):
 r=report();p=Path(path) if path else ROOT/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=1)+'\n');return r

if __name__=='__main__':
 print(json.dumps(write(),indent=1))
