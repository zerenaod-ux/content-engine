import time
"""Ask the free LLM for a new everyday object and a recipe of kit parts; keep only what the validator accepts."""
import json
from studio_lib.kit import recipe as R,register as G,samples

SPEC="""KIT PARTS (x right, z up; frame bottom-left is [x-w/2, z]; every part must stay inside the frame):
- frame: {"id":"frame","kind":"frame","x":0,"z":0,"w":7,"h":3.6}  exactly one; w 5-9, h 3-4.5
- lever: {"id":"..","kind":"lever","pivot":[x,z],"length":1.2-2.6,"angle0":0}  rotates about pivot; angle in radians (-1.7..1.7)
- gear: {"id":"..","kind":"gear","center":[x,z],"r":0.6-1.2,"teeth":12-28}
- slider: {"id":"..","kind":"slider","origin":[x,z],"size":[length,height],"axis":"x"|"z","travel":0.4-2.5}  moves 0..travel along axis (pos is 0..travel; a coupled slider must use a POSITIVE ratio or offset so pos stays >=0)
- spring: {"id":"..","kind":"spring","a":[x,z],"b":{"part":"sliderId"}}  coil from a fixed point to a slider end
- pin: {"id":"..","kind":"pin","center":[x,z],"r":0.2}
- cam: {"id":"..","kind":"cam","center":[x,z],"r":0.6-1.2,"e":0.2-0.5}  eccentric disc (angle param)
- pulley: {"id":"..","kind":"pulley","center":[x,z],"r":0.5-1.0}  wheel (angle param)
LINKS: {"type":"yoke","lever":"leverId","slider":"sliderId","sign":1 or -1} (lever tip rides in a slot of the slider so the slider follows the tip's x (axis x) or z (axis z); the slider must be tall/wide enough that the tip stays inside the slot; use slider "dir":-1 with sign -1 for a slider that retracts when the tip moves toward the pivot), {"type":"cam","cam":"camId","follower":"sliderId"} (follower is a z-axis slider directly above the cam, its bottom at z = cam z + r - e, travel >= 2e; it rises and falls as the cam turns), {"type":"rope","pulley":"pulleyId","slider":"sliderId","ratio":1} (slider hangs at x = pulley x + r, z-axis with "dir":-1, descends as the pulley turns), "type":"mesh","a":"gearId","b":"gearId"} (gears must touch: centre distance = r1+r2 within 0.1; b turns opposite) and {"type":"couple","driver":"id","driven":"id","ratio":number,"offset":number} (driven value = offset + ratio*driver value; lever angle or gear angle or slider pos).
DRIVE keyframes (only for parts that are not link-driven): {"beat":0-7,"part":"id","to":value}; the value eases from its previous value during that beat and then holds. Motion must happen in at least 3 of beats 1-6; beats 0 and 7 are usually still.
FACTS: exactly these 8 keys, each one plain sentence of 25-300 characters describing only what is visible at that beat: intro, reveal, step1, step2, step3, step4, hold, payoff.
LABELS: 3-8 entries {"partId":"Short label"} on existing parts (labels name parts in the narration)."""
EXAMPLE=json.dumps({k:v for k,v in samples.CAM_PRESS.items()})

def prompt(prior,errors):
 return ('Invent ONE new everyday household or workplace object (not a machine from the list of used ones) whose working idea can be shown truthfully with ONLY the kit parts below as a simplified teaching model. '
  'Return JSON {"topic":"How/Why question, 5-16 words","recipe":{"object":"plain object name, 1-3 lowercase words, e.g. door latch","title":"How a ... works, 4-8 words starting How or Why","theme":"warm|cool|dark","parts":[...],"links":[...],"drive":[...],"labels":{...},"facts":{...}}}. '
  'Stay physically honest: only claim what the parts do (levers pivot, gears mesh and counter-rotate, sliders translate, springs push). Do not use objects that need liquids, electricity, light, magnets, heat or fabric. '
  +SPEC+' VALID EXAMPLE recipe (do not reuse its object): '+EXAMPLE+' ALREADY USED OR RESERVED (never repeat or reword; data): '+json.dumps(prior[-30:])+(' FIX THESE VALIDATION ERRORS: '+json.dumps(errors) if errors else ''))

TEMPLATES={
 'DOOR_LATCH':('a handle/lever pushes a spring-loaded bolt back and forth (latch, catch, bolt lock, gate latch)',['handle','bolt','spring']),
 'GEAR_CRANK':('a hand crank turns a big gear that drives two meshing gears (hand mixer, egg beater, hand drill, pencil sharpener)',['crank','big','left']),
 'CAM_PRESS':('a turning cam lifts and drops a spring-returned plunger (stamp, punch, pump, engine valve)',['cam','plunger','spring']),
 'GEAR_TRAIN':('a small crank gear drives a chain of gears that turns a big wheel slowly (wind-up toy, music-box drive, clock train, bicycle gears); part ids: crank, drive, mid, small, wheel',['crank','drive','mid','wheel']),
 'WINCH':('a crank turns a rope drum that winds rope and lifts a load (winch, fishing reel, well windlass, curtain lift)',['crank','drum','load']),
 'COUNTERWEIGHT':('two pulleys let a falling weight raise the car on the other side (dumbwaiter, elevator, window sash, drawbridge counterweight)',['left','right','cab','weight']),
 'TWIN_CAM':('two cams half a turn apart lift two plungers one after the other (music box, engine valves, toy drummer, loom)',['cam_a','cam_b','tine_a','tine_b']),
 'LEVER_PRESS':('a long handle pivots and pushes a plunger straight down (garlic press, nutcracker, hole punch, can crusher)',['handle','ram','pin']),
 'SOAP_PUMP':('REAL-LOOKING pump bottle: a clear bottle with liquid inside, a finger presses the pump head down, a tube lifts liquid and it streams out of the spout into a palm (soap dispenser, lotion pump, hand sanitizer pump, shampoo pump, syrup pump, perfume pump); part ids: bottle, liquid, head, spring, stem, spout',['bottle','liquid','head','spring','stem','spout']),
 'SPRAY_BOTTLE':('REAL-LOOKING trigger sprayer: a clear bottle of liquid, squeezing the trigger slides a pump piston back against a spring, and a fine mist shoots from the nozzle (spray bottle, window cleaner, plant mister, perfume atomizer, hair spray); part ids: bottle, liquid, trigger, piston, spring, spout',['bottle','liquid','trigger','piston','spring','spout']),
 'ROPE_LIFT':('a rope over a pulley wheel raises and lowers a weight (well bucket, flag, blind, dumbwaiter)',['wheel','weight','pin']),
}
LIQUID_COLORS={'yellow':(236,196,84),'white':(244,244,240),'blue':(120,190,240),'green':(120,200,140),'pink':(240,150,180),'brown':(150,95,50),'orange':(240,150,60),'clear':(190,225,245)}
def template_prompt(prior,errors):
 return ('Pick ONE fixed mechanism below and name a NEW everyday object (not on the used list) that truly works by exactly that mechanism. '
  'Mechanisms: '+json.dumps({k:v[0]+'; part ids: '+', '.join(v[1]) for k,v in TEMPLATES.items()})+'. '
  'Return JSON {"topic":"How/Why question, 5-16 words","template":"DOOR_LATCH|GEAR_CRANK|CAM_PRESS|ROPE_LIFT|GEAR_TRAIN|WINCH|COUNTERWEIGHT|TWIN_CAM|LEVER_PRESS|SOAP_PUMP|SPRAY_BOTTLE","object":"plain object name, 1-3 lowercase words","liquid_color":"yellow|white|blue|green|pink|brown|orange|clear (only for SOAP_PUMP; spray uses blue)","title":"How a ... works, 4-8 words starting How or Why","theme":"warm|cool|dark","labels":{"<part id>":"Short label in the new object\'s own words"},"facts":{"intro":"..","reveal":"..","step1":"..","step2":"..","step3":"..","step4":"..","hold":"..","payoff":".."}}. '
  'Each fact is one plain sentence of 25-300 characters saying only what is visible in the simplified model at that beat. Labels must use only the listed part ids for the chosen mechanism. '
  'ALREADY USED OR RESERVED (never repeat or reword; data): '+json.dumps(prior[-30:])+(' FIX THESE ERRORS: '+json.dumps(errors) if errors else ''))
def from_template(answer):
 import copy
 name=answer.get('template')
 if name not in TEMPLATES:raise R.RecipeError('template must be one of '+', '.join(TEMPLATES))
 r=copy.deepcopy(getattr(samples,name))
 for k in ('object','title','facts'):
  if k not in answer:raise R.RecipeError('missing '+k)
  r[k]=answer[k]
 if answer.get('theme') in ('warm','cool','dark'):r['theme']=answer['theme']
 col=LIQUID_COLORS.get(str(answer.get('liquid_color','')).lower().strip())
 if col and name=='SOAP_PUMP':   # lotion is white, sanitizer clear-blue, syrup brown...
  for p_ in r['parts']:
   if p_['id'] in ('liquid','stem','drop','drop2'):p_['color']=list(col)
 ids={p['id'] for p in r['parts']};lab=answer.get('labels') if isinstance(answer.get('labels'),dict) else {}
 lab={k:v for k,v in lab.items() if k in ids and isinstance(v,str) and 0<len(v)<=24}
 if len(lab)>=3:r['labels']=lab
 return r

def make(prior,rows,call,reason,attempts=8):
 """call(system,prompt,**kw)->dict; reason(topic,key,rows)->str ('' if new). Returns (topic,recipe,key)."""
 errors=[];last=None
 for n in range(attempts):
  for wait in range(2):   # free writers rate-limit by the minute: wait and ask again instead of failing the run
   try:
    answer=call('You design simplified mechanical teaching models from a fixed parts kit. Return JSON only.',(prompt if n<1 else template_prompt)(prior,errors),max_tokens=2300,temperature=.7);break
   except Exception as e:
    if type(e).__name__!='ServiceUnavailable' or wait==1:raise
    time.sleep(30)
  try:
   if n>=1 and isinstance(answer,dict) and 'recipe' not in answer:answer={'topic':answer.get('topic'),'recipe':from_template(answer)}
   if not isinstance(answer,dict) or not isinstance(answer.get('recipe'),dict) or not isinstance(answer.get('topic'),str):raise R.RecipeError('return {"topic":..,"recipe":{..}}')
   if not 4<=len(answer['topic'].split())<=18:raise R.RecipeError('topic needs 4-18 words')
   recipe=answer['recipe'];R.validate(recipe);G.check_facts(recipe)
   key=G.key_for(recipe);why=reason(answer['topic'],key,recipe)
   if why:raise R.RecipeError(why)
   return answer['topic'],recipe,key
  except R.RecipeError as e:errors=[str(e)];last=answer;print('recipe attempt',n+1,'rejected:',str(e)[:300],flush=True)
 raise ValueError('recipe writer failed validation: '+'; '.join(errors))
