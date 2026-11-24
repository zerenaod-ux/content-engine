"""Many stories per machine: one video per (machine, story), never the same story twice.

A story is a different question about the same machine, with its own hero part, focus beat and camera view.
The first video of a machine is its 'original' story (family name only). Extra stories are listed in machines/meta/stories.json
and are identified as '<family>::<story id>' in the permanent novelty ledger, so the old no-repeat promise still holds per story."""
import json,os,re
from pathlib import Path
PATH=Path(__file__).resolve().parent.parent/'machines'/'meta'/'stories.json'
VIEW_LIMITS={'az':(-.8,.8),'zoom':(.85,1.15),'elev':(-5,6)}

def _data(path=None):
 try:return json.loads(Path(path or PATH).read_text())
 except (OSError,ValueError):return {'enabled':False,'stories':{}}

def enabled(path=None):return _data(path).get('enabled') is True

def stories_for(key,path=None):
 d=_data(path)
 return list(d.get('stories',{}).get(key,[])) if d.get('enabled') is True else []

def find(key,sid,path=None):
 return next((s for s in stories_for(key,path) if s['id']==sid),None)

def current(path=None):
 """Story chosen for this run (CE_STORY), or None for a machine's original video."""
 return os.environ.get('CE_STORY') or None

def validate(data,known_machines):
 """Raise ValueError naming the first problem; used by tests and before enabling."""
 seen=set()
 for key,rows in data.get('stories',{}).items():
  if key not in known_machines:raise ValueError('stories for unknown machine: '+key)
  views=[]
  for s in rows:
   if not re.fullmatch(r'[a-z][a-z0-9_]{2,40}',s.get('id','')) or s['id']=='original':raise ValueError(f'{key}: bad story id')
   if (key,s['id']) in seen:raise ValueError(f'{key}: duplicate story {s["id"]}')
   seen.add((key,s['id']))
   if not (isinstance(s.get('question'),str) and 4<=len(s['question'].split())<=20 and s['question'].endswith('?')):raise ValueError(f'{key}/{s["id"]}: question needs 4-20 words and a question mark')
   if not (isinstance(s.get('hero'),str) and s['hero'].strip()):raise ValueError(f'{key}/{s["id"]}: hero part missing')
   if not (isinstance(s.get('focus_beat'),int) and 1<=s['focus_beat']<=6):raise ValueError(f'{key}/{s["id"]}: focus_beat must be 1-6')
   v=s.get('view',{})
   for name,(lo,hi) in VIEW_LIMITS.items():
    if not isinstance(v.get(name),(int,float)) or not lo<=v[name]<=hi:raise ValueError(f'{key}/{s["id"]}: view.{name} outside {lo}..{hi}')
   views.append((round(v['az'],2),round(v['zoom'],2),round(v['elev'],1)))
  if len(set(views))!=len(views):raise ValueError(f'{key}: two stories share the same camera view')
  qs=[s['question'].lower() for s in rows]
  if len(set(qs))!=len(qs):raise ValueError(f'{key}: two stories ask the same question')
 return True

def brief(key,sid,path=None):
 s=find(key,sid,path)
 if not s:return ''
 return (f'STORY BRIEF (this video must be a different story from every earlier video of this machine): answer the question "{s["question"]}" '
         f'Make the {s["hero"]} the hero part and spend the longest, most detailed explanation on beat {s["focus_beat"]}. '
         'Use only the supplied facts; do not repeat the opening line, the hook or the reveal wording of earlier videos.')

def view_for(key,sid,path=None):
 s=find(key,sid,path);return dict(s['view']) if s else None

def pick(pairs,rows,weights=None):
 """Choose which (machine, story) to build next. Prefer machines with the fewest finished videos, so the channel stays varied;
 winners weights (from views and owner verdicts) break ties and favour what works. Deterministic for a given history."""
 import collections
 used=collections.Counter()
 for r in rows:
  m=r.get('mechanism') or r.get('subject')
  if isinstance(m,str):used[m]+=1
 w=weights or {}
 return sorted(pairs,key=lambda p:(used[p[0]]-round(float(w.get(p[0],0.))*2,1),p[0],p[1] or ''))[0]
