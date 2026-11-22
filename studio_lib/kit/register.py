"""Install a validated recipe as a full mechanism: registry facts, causal motion contract, narration rules and a single-use visual family.
Everything is derived from the recipe, so there is no per-object code and no hand-written contract."""
import json,re
from pathlib import Path
import numpy as np
from studio_lib.kit import recipe as R
ACTIONS=['intro','reveal','step1','step2','step3','step4','hold','payoff']
RECIPE_DIR=Path('data/scenes/recipes')
STOP={'the','and','with','that','this','from','into','door','how','why','does','what','works','work','its','their','a','of','to','in','on','for','an','is','are','it'}

def slug(text):return re.sub(r'[^a-z0-9]+','_',text.lower()).strip('_')[:40]
def key_for(recipe):return 'recipe_'+slug(recipe['title'])
def words(text):return [w for w in re.findall(r'[a-z]{3,}',text.lower()) if w not in STOP]
def label_pattern(recipe):
 ws=sorted({w for v in recipe['labels'].values() for w in words(v)})
 return '|'.join(ws)

def simulate(machine):
 """Per-beat movement signs and holds measured from the machine itself (not from words)."""
 tl={'beats':[{'start':k*6.,'end':(k+1)*6.} for k in range(8)]};moves={};holds={}
 ids=[p['id'] for p in machine.r['parts'] if p['kind'] in R.PARAM]
 for i in range(8):
  a,b=i*6+1e-5,(i+1)*6-1e-5;ss=[machine.state(float(t),tl) for t in np.linspace(a,b,41)]
  for pid in ids:
   d=ss[-1][pid]-ss[0][pid];span=max(s[pid] for s in ss)-min(s[pid] for s in ss)
   if abs(d)>=.02:moves.setdefault(i,{})[pid]=1 if d>0 else -1
   elif span<=1e-5:holds.setdefault(i,[]).append(pid)
 return moves,holds

def build_entries(recipe):
 m=R.Machine(recipe);moves,holds=simulate(m);key=key_for(recipe)
 lp=label_pattern(recipe);title=' '.join(words(recipe['title']))
 tw='|'.join(sorted(set(words(recipe['title']))|set(lp.split('|'))))
 subjects=[tw]*8  # any label, title or object word counts as naming a visible part
 # a moving beat must also be narrated: first label of the part that moves
 visible=[]
 for i in (2,3,4,5):
  mv=[p for p in moves.get(i,{}) if m.parts[p]['kind']!='frame']
  if mv:visible.append((i,mv[0]))
 facts=recipe['facts']
 return key,{
  'registry':{'description':recipe['title']+' (simplified model built from kit parts: '+', '.join(sorted({p['kind'] for p in recipe['parts']}))+')','actions':list(ACTIONS),'facts':{a:facts[a] for a in ACTIONS},'source':recipe.get('source','simplified teaching model')},
  'contract':{'subjects':subjects,'moves':moves,'holds':holds,'visible':visible},
  'family':key,'pattern':r'\b'+re.escape(recipe['object'].lower())+r's?\b','machine':m}

def check_facts(recipe):
 f=recipe.get('facts')
 if not isinstance(f,dict) or set(f)!=set(ACTIONS) or any(not isinstance(v,str) or not 25<=len(v)<=420 for v in f.values()):
  raise R.RecipeError('facts needs exactly these 8 keys, each 25-420 characters: '+', '.join(ACTIONS))
 if not isinstance(recipe.get('object'),str) or not 3<=len(recipe['object'])<=30 or not re.fullmatch(r'[a-z][a-z \-]+',recipe['object'].lower()):raise R.RecipeError('object must be the plain object name, 3-30 letters, e.g. door latch')
 if not isinstance(recipe.get('title'),str) or not 3<=len(recipe['title'].split())<=9:raise R.RecipeError('title needs 3-9 words')

def install(recipe,components=None):
 """Validate and register in-process; returns the mechanism key."""
 from studio_lib.registry import REGISTRY
 from studio_lib import action_contracts,narration_timing,novelty
 R.validate(recipe);check_facts(recipe)
 key,e=build_entries(recipe)
 REGISTRY[key]=e['registry'];action_contracts.CONTRACTS[key]=e['contract']
 narration_timing.TRANSITIONS[key]=set();narration_timing.ANCHORS[key]={}
 novelty.FAMILIES[key]=e['family'];novelty.PATTERNS[key]=e['pattern']
 if components is not None:components[key]=e['machine']
 return key

def save(recipe,root=RECIPE_DIR):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);p=root/(key_for(recipe)+'.json');p.write_text(json.dumps(recipe,indent=1));return p

def load_saved(components=None,roots=(RECIPE_DIR,),videos='data/scenes/videos.json'):
 """Re-register every known recipe (local files plus recipes recorded with finished videos). Bad files are skipped, never fatal."""
 found={}
 for root in roots:
  for f in sorted(Path(root).glob('recipe_*.json')) if Path(root).is_dir() else []:
   try:found[f.stem]=json.loads(f.read_text())
   except ValueError:pass
 try:
  for row in json.loads(Path(videos).read_text()):
   r=row.get('recipe') if isinstance(row,dict) else None
   if isinstance(r,dict) and r.get('title'):found.setdefault(key_for(r),r)
 except (OSError,ValueError):pass
 keys=[]
 for k,r in found.items():
  try:keys.append(install(r,components))
  except Exception:continue
 return keys
