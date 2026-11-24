"""Machine writer: an AI model designs a NEW hand-built machine, and nothing it writes is trusted until it passes the same gates as a human-built one.

The model returns JSON: object words, eight beat facts, narration words and the machine's python code. This module then
  1. checks the code against a strict allow-list (no files, network, imports outside the drawing helpers, dunders, loops without end),
  2. runs it in a separate, time- and memory-limited python process,
  3. MEASURES the motion contract from what state() really does (the model never states what moves),
  4. proves each listed part is visible (hiding it changes the picture),
  5. runs the picture check (richness, motion) on a fixture timeline,
  6. only then writes machines/<key>.json (code included) for the normal spec loader.
Failures go back to the model as plain feedback, up to three tries. Videos made from the new machine still wait for the owner's review."""
import ast,json,os,re,subprocess,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
MAX_CODE=24000
ALLOWED_MODULES={'math','functools','numpy','studio_lib.mesh','studio_lib.narration_timing','studio_lib.solid_parts','studio_lib.parts_rich'}
ALLOWED_FROM_STUDIO={'mesh','narration_timing','solid_parts','parts_rich'}
BAD_NAMES={'eval','exec','open','compile','__import__','getattr','setattr','delattr','globals','locals','vars','input','breakpoint','type','object','memoryview','classmethod','staticmethod','super','exit','quit','print'}
BAD_NODES=(ast.While,ast.ClassDef,ast.Global,ast.Nonlocal,ast.AsyncFunctionDef,ast.Await,ast.AsyncFor,ast.AsyncWith,ast.Yield,ast.YieldFrom,ast.Delete)
ACTIONS=['intro','cutaway','drive','response','hold','repeat','limit','payoff']
NEVER=r'(?!x)x'   # regular expression that matches nothing

class WriterError(ValueError):pass

def check_code(code):
 """Raise WriterError naming the first thing the allow-list does not permit."""
 if not isinstance(code,str) or not code.strip():raise WriterError('code is empty')
 if len(code)>MAX_CODE:raise WriterError('code is longer than %d characters'%MAX_CODE)
 try:tree=ast.parse(code)
 except SyntaxError as e:raise WriterError('code does not parse: %s (line %s)'%(e.msg,e.lineno))
 names=set()
 for n in ast.walk(tree):
  if isinstance(n,BAD_NODES):raise WriterError('not allowed in machine code: '+type(n).__name__+' (line %s)'%getattr(n,'lineno','?'))
  if isinstance(n,ast.Import):
   for a in n.names:
    if a.name not in ALLOWED_MODULES:raise WriterError('import not allowed: '+a.name)
  elif isinstance(n,ast.ImportFrom):
   if n.level:raise WriterError('relative import not allowed')
   if n.module=='studio_lib':
    bad=[a.name for a in n.names if a.name not in ALLOWED_FROM_STUDIO]
    if bad:raise WriterError('import not allowed: studio_lib.'+bad[0])
   elif n.module not in ALLOWED_MODULES:raise WriterError('import not allowed: '+str(n.module))
  elif isinstance(n,ast.Attribute) and n.attr.startswith('_'):raise WriterError('private attribute not allowed: '+n.attr)
  elif isinstance(n,ast.Name):
   if n.id in BAD_NAMES or n.id.startswith('__'):raise WriterError('name not allowed: '+n.id)
   names.add(n.id)
  elif isinstance(n,ast.Constant) and isinstance(n.value,str) and '__' in n.value:raise WriterError('text with double underscores is not allowed')
 defs={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
 for need in ('state','draw','background','elevation','shot'):
  if need not in defs:raise WriterError('code must define '+need+'()')

def _import(name,globals=None,locals=None,fromlist=(),level=0):
 if level or (name not in ALLOWED_MODULES and name!='studio_lib'):raise ImportError('import not allowed: '+name)
 import importlib
 mod=importlib.import_module(name)
 if name=='studio_lib':
  for f in fromlist or ():
   if f not in ALLOWED_FROM_STUDIO:raise ImportError('import not allowed: studio_lib.'+f)
   importlib.import_module('studio_lib.'+f)
 return mod

def _safe_builtins():
 import builtins
 keep='abs all any bool dict divmod enumerate filter float int isinstance len list map max min pow range reversed round set sorted str sum tuple zip slice repr hasattr callable iter next frozenset complex True False None ValueError TypeError KeyError IndexError ZeroDivisionError ArithmeticError Exception StopIteration'.split()
 b={k:getattr(builtins,k) for k in keep if hasattr(builtins,k)};b['__import__']=_import;b['__build_class__']=None
 return b

def build_module(name,code):
 """Compile checked code into a module object that only sees the safe builtins."""
 check_code(code)
 mod=types.ModuleType(name);mod.__dict__['__builtins__']=_safe_builtins()
 exec(compile(code,'<machine:%s>'%name,'exec'),mod.__dict__)
 return mod

def fixture_tl():
 return {'beats':[{'start':i*6.,'end':(i+1)*6.,'action':a,'camera':'wide' if i in (0,7) else 'mechanism'} for i,a in enumerate(ACTIONS)],'duration':48.}

def derive_contract(module):
 """Per-beat movement signs and holds, measured from state(). Returns (moves,holds)."""
 import numpy as np
 from studio_lib.action_contracts import channels
 tl=fixture_tl();moves={};holds={};names=None
 for i in range(8):
  ss=[channels(module.state(float(t),tl)) for t in np.linspace(i*6+1e-5,(i+1)*6-1e-5,41)]
  if names is None:names=set(ss[0])
  if any(set(s)!=names for s in ss):raise WriterError('state() must return the same channels at every moment')
  for k in sorted(names):
   if k=='beat':continue
   d=ss[-1][k]-ss[0][k];span=max(s[k] for s in ss)-min(s[k] for s in ss)
   if abs(d)>=.02:moves.setdefault(str(i),{})[k]=1 if d>0 else -1
   elif span<=1e-5:holds.setdefault(str(i),[]).append(k)
 moving=[b for b in moves if 1<=int(b)<=6]
 if len(moving)<3:raise WriterError('at least three of beats 1-6 must show a measurable movement in state(); found %d'%len(moving))
 return moves,holds

def _words(items):
 out=[]
 for w in items:
  w=re.sub(r'[^a-z0-9 \-]','',str(w).lower()).strip()
  if 2<=len(w)<=30:out.append(w)
 return sorted(set(out))

def assemble(draft,key,moves,holds,visible):
 """Build the spec dict (everything but derived values comes from the draft)."""
 words=_words(draft.get('words',[]))
 if not 1<=len(words)<=8:raise WriterError('words needs 1-8 short names people use for this object')
 pat=r'\b('+'|'.join(re.escape(w) for w in words)+r')s?\b'
 subs=draft.get('subjects')
 if not isinstance(subs,list) or len(subs)!=8:raise WriterError('subjects needs 8 lists of words, one per beat')
 subjects=[]
 for i,s in enumerate(subs):
  w=_words(s if isinstance(s,list) else [])
  if not w:raise WriterError('subjects[%d] needs at least one visible-part word'%i)
  subjects.append(r'\b('+'|'.join(re.escape(x) for x in w)+r')')
 cues=draft.get('cues',{})
 anchors={}
 for a in ('cutaway','payoff'):
  w=_words(cues.get(a,[]) if isinstance(cues,dict) else [])
  if not w:raise WriterError('cues.%s needs words that the narration says at that moment'%a)
  anchors[a]='|'.join(re.escape(x) for x in w)
 title=str(draft.get('title','')).strip()[:60]
 return {'key':key,'module':'studio_lib.'+key,'family':key,'pattern':pat,'detect':'|'.join(re.escape(w) for w in words),'block':NEVER,
  'description':str(draft.get('description',title))[:300],'actions':list(ACTIONS),'facts':dict(draft.get('facts',{})),
  'source':str(draft.get('source','')),'contract':{'subjects':subjects,'moves':moves,'holds':holds,'visible':visible},
  'transitions':['cutaway','payoff'],'anchors':anchors,'narration_rules':[],'cue_bans':[],'bounds':[],
  'label':{'from':1,'to':6,'text':'Simplified model · illustration'},'title':title,'writer':'machine_writer','code':draft['code']}

def prove_visible(key,module,parts):
 """A part counts as visible only when hiding it really changes the picture."""
 import numpy as np
 from studio_lib import director
 tl=fixture_tl();plan={'mechanism':key,'hook':'Test','picture_zoom':1.0};director.COMPONENTS[key]=module;rows=[]
 for part in parts[:8]:
  for b in (2,3,4,5):
   t=b*6+3.;a=np.array(director.component_picture(t,tl,plan)).astype(int);z=np.array(director.component_picture(t,tl,plan,hidden=(part,))).astype(int)
   if np.abs(a-z).sum()>2500:rows.append([b,part]);break
 if len({p for _,p in rows})<3:raise WriterError('at least three listed parts must visibly change the picture when hidden (found %d); make draw() honour the hidden argument'%len({p for _,p in rows}))
 return rows

def check_spec(draft,key,outdir):
 """Everything that executes the model's code. Returns the finished spec or raises WriterError."""
 from studio_lib import machine_spec,director,action_contracts,picture_check
 module=build_module('studio_lib.'+key,draft['code'])
 for n in ('state','draw'):
  if not callable(getattr(module,n,None)):raise WriterError(n+' is not callable')
 moves,holds=derive_contract(module)
 parts=[str(p) for p in draft.get('parts',[]) if re.fullmatch(r'[a-z][a-z0-9_]{1,24}',str(p))]
 visible=prove_visible(key,module,parts)
 spec=assemble(draft,key,moves,holds,visible)
 try:machine_spec.validate(spec)
 except machine_spec.SpecError as e:raise WriterError('spec: '+str(e))
 for other,pat in __import__('studio_lib.novelty',fromlist=['x']).PATTERNS.items():
  if other!=key and re.search(pat,' '.join(_words(draft.get('words',[])))):raise WriterError('name words collide with the existing machine '+other)
 machine_spec.install(spec,director.COMPONENTS)
 tl=fixture_tl();plan={'mechanism':key,'hook':'How it works','picture_zoom':1.0}
 def picture(x,z):
  r=director.component_picture(x,tl,plan,want_scene=True,zoom_scale=z/float(plan.get('picture_zoom',1.0)));return r[0],r[1].faces
 os.environ['CE_VISION_CHECK']='off';Path(outdir).mkdir(parents=True,exist_ok=True)
 try:verdict=picture_check.run(picture,tl,plan,action_contracts.CONTRACTS[key],outdir)
 except ValueError as e:raise WriterError(str(e))
 spec['picture_check']={'score':verdict['score'],'zoom':verdict['zoom'],'faces':verdict['measures']['faces'],'colours':verdict['measures']['colours']}
 return spec

def run_sandbox(draft,key,outdir,timeout=300):
 """Run check_spec in a fresh limited python process; the parent never executes the model's code."""
 outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
 inp=outdir/'draft.json';res=outdir/'checked.json';inp.write_text(json.dumps(draft))
 def limits():
  try:
   import resource;resource.setrlimit(resource.RLIMIT_AS,(3<<30,3<<30));resource.setrlimit(resource.RLIMIT_CPU,(timeout,timeout))
  except Exception:pass
 env={k:v for k,v in os.environ.items() if k in ('PATH','PYTHONPATH','HOME','LANG','CE_VISION_CHECK')};env['WRITER_PATH']=os.pathsep.join(filter(None,[str(ROOT),env.get('PYTHONPATH','')]))
 try:p=subprocess.run([sys.executable,'-I','-c',"import os,sys;[sys.path.insert(0,x) for x in reversed(os.environ['WRITER_PATH'].split(os.pathsep))];from studio_lib import machine_writer as m;m._cli(sys.argv[1:])",str(inp),key,str(res)],cwd=str(ROOT),env=env,capture_output=True,text=True,timeout=timeout,preexec_fn=limits)
 except subprocess.TimeoutExpired:raise WriterError('machine code took too long to run')
 if res.exists():
  data=json.loads(res.read_text())
  if data.get('error'):raise WriterError(data['error'])
  return data['spec']
 raise WriterError('machine code crashed: '+(p.stderr or p.stdout)[-300:])

def _cli(argv):
 inp,key,res=argv
 try:
  spec=check_spec(json.loads(Path(inp).read_text()),key,Path(res).parent/'picture')
  Path(res).write_text(json.dumps({'spec':spec}))
 except Exception as e:Path(res).write_text(json.dumps({'error':(type(e).__name__+': ' if not isinstance(e,WriterError) else '')+str(e)[:400]}))

PROMPT='''You design ONE new simplified machine for a vertical (9:16) science-explainer channel called How It Ticks. Return JSON only.
Machine idea: {idea}
{feedback}
Return {{"title","description","words","parts","subjects","cues","facts","source","code"}}:
- title: short plain name. description: one line saying what is shown and what is NOT shown.
- words: 1-6 lowercase names people use for the object (used to detect topics).
- parts: 5-8 lowercase_names of parts that draw() hides when its `hidden` tuple contains the name; each must visibly change the picture.
- subjects: list of 8 lists of words, one list per beat, naming what is visible and described in that beat.
- cues: {{"cutaway":[words spoken when the cover lifts],"payoff":[words spoken at the final result]}}.
- facts: object with exactly these 8 keys {actions}; each 25-400 characters, plain, saying what that beat shows and what is not shown.
- source: an https link to a trustworthy page about the real machine.
- code: python source defining state(t,tl), draw(s,t,tl,hidden=()), background(), elevation(t,tl), shot(i). Rules:
  * imports ONLY: math, functools, numpy, and from studio_lib: mesh (ease), narration_timing (progress), solid_parts (background), parts_rich (P). No other imports, no classes, no while loops, no names starting with underscore, no open/eval/exec/getattr/type/print.
  * tl['beats'] is a list of 8 dicts with start/end seconds. Beat 0 intro, 1 cover lifts (cutaway), 2 drive, 3 response, 4 hold (nothing moves), 5 repeat, 6 limit, 7 payoff.
  * state(t,tl) returns a dict with 'beat' and float channels (e.g. cut, turn, slide) that really move per beat; a channel must stay constant in the beats where nothing moves it. At least three of beats 1-6 must move something.
  * draw() uses parts_rich helpers: P.plate, P.gear, P.spring, P.tube, P.disc, P.annulus, P.hex_prism, P.piston_cylinder, P.rivets, P.hook_link, P.chamfer_box, P.tooth_profile. Use several colours and many faces: a rich, detailed model, never plain boxes.
  * shot(i) returns ((x,y,z) target, zoom, floor) per beat, framing the machine inside a 9:16 frame.
  * EXACT signatures of the parts helpers (call them exactly like this; every argument without a default is REQUIRED, colour is always a (r,g,b) tuple; the first argument s is the scene passed to draw):
{signatures}
Here is a working example of the module shape:
{example}'''

def part_signatures():
 import inspect
 from studio_lib import parts_rich as _p
 names=('plate','gear','spring','tube','disc','annulus','hex_prism','piston_cylinder','rivets','hook_link','chamfer_box','tooth_profile')
 return '\n'.join('    P.'+n+str(inspect.signature(getattr(_p,n))) for n in names if hasattr(_p,n))

def example_code():
 text=(ROOT/'tools'/'new_machine.py').read_text();a=text.index("MODULE='''")+10;b=text.index("'''",a)
 return text[a:b].replace('{title}','Example').replace('{key}','example')

def write(idea,ask=None,workdir='machine-writer',max_tries=6):
 """Ask the model for a machine; return the checked spec (also saved to machines/<key>.json by save()). ask(prompt)->dict."""
 if ask is None:
  from studio_lib import providers
  ask=lambda p:providers.call('You write careful, safe python for a small 3D animation library.',p,max_tokens=12000,temperature=.6)
 slug=re.sub(r'[^a-z0-9]+','_',str(idea).lower()).strip('_')[:24] or 'machine';key='mw_'+slug
 feedback='';last=None
 for attempt in range(1,max_tries+1):
  draft=ask(PROMPT.format(idea=idea,feedback=feedback,actions=', '.join(ACTIONS),example=example_code(),signatures=part_signatures()))
  try:
   if not isinstance(draft,dict):raise WriterError('answer was not a JSON object')
   check_code(draft.get('code'))
   spec=run_sandbox(draft,key,Path(workdir)/('try%d'%attempt));spec['writer_tries']=attempt;return spec
  except WriterError as e:
   last=str(e);feedback='Your previous attempt was rejected: %s\nFix exactly that and return the full JSON again.'%last;print('machine writer try %d rejected: %s'%(attempt,last),flush=True)
 raise WriterError('No acceptable machine after %d tries. Last problem: %s'%(max_tries,last))

def save(spec,folder=None):
 folder=Path(folder) if folder else ROOT/'machines';folder.mkdir(parents=True,exist_ok=True)
 p=folder/(spec['key']+'.json');p.write_text(json.dumps(spec,indent=1)+'\n');return p

IDEAS=['bicycle derailleur','door latch','retractable ballpoint pen','pop-up toaster lever','garage door torsion spring','mechanical pencil','toilet flush valve','hand-crank pencil sharpener','car jack scissor lift','window blind cord lock','tape measure with locking blade','bottle opener lever','revolving door','manual can opener','salad spinner','drip coffee valve','sewing machine bobbin hook','music box comb','hand egg beater','spring-loaded mousetrap']
MAX_WRITTEN=12

def pick_idea(specs_dir=None):
 from studio_lib import novelty
 have=sorted((Path(specs_dir) if specs_dir else ROOT/'machines').glob('mw_*.json'))
 if len(have)>=MAX_WRITTEN:return None
 used={json.loads(f.read_text()).get('title','').lower() for f in have}
 for i in IDEAS:
  if i in used or any(re.search(p,i) for p in novelty.PATTERNS.values()):continue
  return i
 return None

def auto(ask=None,workdir='machine-writer'):
 idea=os.environ.get('MACHINE_IDEA') or pick_idea()
 if not idea:print('No new machine idea left or limit reached');return None
 spec=write(idea,ask=ask,workdir=workdir);print('wrote',save(spec));return spec

if __name__=='__main__':
 if len(sys.argv)>=2 and sys.argv[1]=='--check':_cli(sys.argv[2:])
 else:
  auto()
