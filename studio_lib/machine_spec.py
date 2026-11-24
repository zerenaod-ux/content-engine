"""One spec file per hand-built machine installs every hookup the engine needs.

A spec (machines/<key>.json) names the machine's python module (geometry and motion) and carries everything
that used to be edited by hand in ten places: registry facts, causal motion contract, narration rules,
speech-cue anchors, novelty family, topic detection and limits, caption label and motion bounds.
Adding a machine = write its module + one spec. Bad specs fail validation with a plain message and are never half-installed."""
import importlib,json,re
from pathlib import Path

SPEC_DIR=Path(__file__).resolve().parent.parent/'machines'
BEATS=8
LABELS={}        # key -> (first beat, last beat, caption text)
SPECS={}         # key -> validated spec
_STATE={'loading':False,'done':False}

class SpecError(ValueError):pass

def _regex(value,where):
 if not isinstance(value,str) or not value:raise SpecError(f'{where}: needs a regular expression string')
 try:re.compile(value)
 except re.error as e:raise SpecError(f'{where}: bad regular expression ({e})')

def validate(spec):
 """Return the spec with int beat keys, or raise SpecError naming the first problem."""
 if not isinstance(spec,dict):raise SpecError('spec must be an object')
 for k in ('key','module','family','pattern','detect','block','description','actions','facts','source','contract','transitions','anchors'):
  if k not in spec:raise SpecError(f'missing field: {k}')
 key=spec['key']
 if not isinstance(key,str) or not re.fullmatch(r'[a-z][a-z0-9_]{2,40}',key):raise SpecError('key must be lowercase letters, digits, underscore')
 if not isinstance(spec['family'],str) or not re.fullmatch(r'[a-z][a-z0-9_]{2,40}',spec['family']):raise SpecError('family must be a lowercase name')
 for k in ('pattern','detect','block'):_regex(spec[k],k)
 actions=spec['actions']
 if not isinstance(actions,list) or len(actions)!=BEATS or len(set(actions))!=BEATS or not all(isinstance(a,str) and re.fullmatch(r'[a-z_]+',a) for a in actions):raise SpecError('actions needs 8 different lowercase names')
 facts=spec['facts']
 if not isinstance(facts,dict) or set(facts)!=set(actions):raise SpecError('facts needs exactly one entry per action')
 for a,v in facts.items():
  if not isinstance(v,str) or not 25<=len(v)<=600:raise SpecError(f'fact {a} needs 25-600 characters')
 if not str(spec['source']).startswith('https://'):raise SpecError('source must be a https link')
 c=spec['contract']
 if not isinstance(c,dict) or set(c)-{'subjects','moves','holds','visible'} or set(c)!={'subjects','moves','holds','visible'}:raise SpecError('contract needs subjects, moves, holds, visible')
 if not isinstance(c['subjects'],list) or len(c['subjects'])!=BEATS:raise SpecError('contract.subjects needs 8 patterns, one per beat')
 for i,p in enumerate(c['subjects']):_regex(p,f'subjects[{i}]')
 def beats(d,name):
  out={}
  for b,v in d.items():
   if not str(b).isdigit() or not 0<=int(b)<BEATS:raise SpecError(f'{name}: beat must be 0-7')
   out[int(b)]=v
  return out
 moves=beats(c['moves'],'moves');holds=beats(c['holds'],'holds')
 for b,m in moves.items():
  if not isinstance(m,dict) or not m or any(s not in (1,-1) for s in m.values()):raise SpecError(f'moves[{b}]: channel to 1 or -1')
 for b,h in holds.items():
  if not isinstance(h,list) or not h or not all(isinstance(x,str) for x in h):raise SpecError(f'holds[{b}]: list of channel names')
  clash=set(h)&set(moves.get(b,{}))
  if clash:raise SpecError(f'beat {b}: {sorted(clash)} cannot both move and hold')
 visible=[]
 for row in c['visible']:
  if not (isinstance(row,list) and len(row)==2 and isinstance(row[0],int) and 0<=row[0]<BEATS and isinstance(row[1],str)):raise SpecError('visible rows look like [beat, "part"]')
  visible.append((row[0],row[1]))
 trans=spec['transitions'];anchors=spec['anchors']
 if not isinstance(trans,list) or not set(trans)<=set(actions):raise SpecError('transitions must be actions of this machine')
 if not isinstance(anchors,dict) or set(anchors)!=set(trans):raise SpecError('anchors needs one pattern per transition action')
 for a,p in anchors.items():_regex(p,f'anchors.{a}')
 rules=spec.get('narration_rules',[]);bans=spec.get('cue_bans',[]);bounds=spec.get('bounds',[])
 for r in rules:
  _regex(r.get('pattern'),'narration_rules.pattern')
  if not isinstance(r.get('message'),str) or not r['message']:raise SpecError('narration_rules need a message')
  if 'beats' in r and not (isinstance(r['beats'],list) and all(isinstance(b,int) and 0<=b<BEATS for b in r['beats'])):raise SpecError('narration_rules.beats must be beat numbers 0-7')
 for r in bans:
  _regex(r.get('pattern'),'cue_bans.pattern')
  if not isinstance(r.get('message'),str) or not r['message']:raise SpecError('cue_bans need a message')
 for b in bounds:
  if not isinstance(b.get('channel'),str) or not isinstance(b.get('message'),str):raise SpecError('bounds need channel and message')
  for end in ('min','max'):
   if not isinstance(b.get(end),(int,float,str)):raise SpecError(f'bounds.{end} must be a number or a module constant name')
 lab=spec.get('label')
 if lab is not None and not (isinstance(lab,dict) and isinstance(lab.get('text'),str) and isinstance(lab.get('from'),int) and isinstance(lab.get('to'),int)):raise SpecError('label needs from, to, text')
 out=json.loads(json.dumps(spec))
 out['contract']={'subjects':c['subjects'],'moves':{b:dict(v) for b,v in moves.items()},'holds':{b:list(v) for b,v in holds.items()},'visible':visible}
 return out

def check_module(spec,module):
 """The machine module must offer what the director and the motion checks call."""
 missing=[n for n in ('state','draw','background','elevation','shot') if not hasattr(module,n)]
 if missing:raise SpecError('machine module lacks: '+', '.join(missing))
 for b in spec.get('bounds',[]):
  for end in ('min','max'):
   if isinstance(b[end],str) and not hasattr(module,b[end]):raise SpecError(f'bounds.{end}: module has no constant {b[end]}')

def install(spec,components=None):
 """Validate and register in-process; returns the mechanism key. Nothing is registered if anything is wrong."""
 from studio_lib.registry import REGISTRY
 from studio_lib import action_contracts,narration_timing,novelty,topic_scope
 spec=validate(spec);key=spec['key']
 module=importlib.import_module(spec['module']);check_module(spec,module)
 others={v for k,v in novelty.FAMILIES.items() if k!=key}
 if spec['family'] in others:raise SpecError('visual family is already used by another machine')
 bounds=[{'channel':b['channel'],'min':getattr(module,b['min']) if isinstance(b['min'],str) else b['min'],'max':getattr(module,b['max']) if isinstance(b['max'],str) else b['max'],'message':b['message']} for b in spec.get('bounds',[])]
 REGISTRY[key]={'description':spec['description'],'actions':list(spec['actions']),'facts':dict(spec['facts']),'source':spec['source']}
 action_contracts.CONTRACTS[key]=spec['contract'];action_contracts.SPEC_RULES[key]=spec.get('narration_rules',[]);action_contracts.SPEC_BOUNDS[key]=bounds
 narration_timing.TRANSITIONS[key]=set(spec['transitions']);narration_timing.ANCHORS[key]=dict(spec['anchors']);narration_timing.CUE_BANS[key]=spec.get('cue_bans',[])
 if spec.get('short_cutaway',True):narration_timing.SHORT_CUTAWAY.add(key)
 novelty.FAMILIES[key]=spec['family'];novelty.PATTERNS[key]=spec['pattern']
 topic_scope.SPEC_DETECT[key]=spec['detect'];topic_scope.SPEC_BLOCK[key]=spec['block']
 if spec.get('label'):LABELS[key]=(spec['label']['from'],spec['label']['to'],spec['label']['text'])
 SPECS[key]=spec
 if components is not None:components[key]=module
 return key

def load_all(components=None,root=None):
 """Install every spec in machines/. A broken spec is skipped and reported, never fatal to the others."""
 if _STATE['loading']:return []
 _STATE['loading']=True;keys=[];problems={}
 try:
  folder=Path(root) if root else SPEC_DIR
  for f in sorted(folder.glob('*.json')) if folder.is_dir() else []:
   try:keys.append(install(json.loads(f.read_text()),components))
   except Exception as e:problems[f.name]=str(e)[:200]
  _STATE['done']=True;_STATE['problems']=problems
 finally:_STATE['loading']=False
 return keys

def ensure_loaded():
 if not _STATE['done'] and not _STATE['loading']:load_all()

def render_files():
 """Files that change the picture: every installed spec and its geometry module (part of the render cache signature)."""
 files=[]
 for key in sorted(SPECS):
  mod=importlib.import_module(SPECS[key]['module']);files.append(Path(mod.__file__))
  p=SPEC_DIR/(key+'.json')
  if p.is_file():files.append(p)
 return files
