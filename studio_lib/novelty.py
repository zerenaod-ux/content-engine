"""Permanent, conservative novelty gate across formats and review outcomes.

An unfamiliar paraphrase is not a proof of semantic novelty. Known visual
families are single-use; missing history or unknown families hold production.
"""
import hashlib,json,os,re,time,urllib.error
from pathlib import Path
from studio_lib.topic_guard import duplicate

POLICY='original-idea-and-visuals-v1'
MEMORY='data/scenes/novelty-ledger.json'
FAMILIES={
 'pendulum_clock':'pendulum_escapement','zipper':'interlocking_zipper','stapler':'staple_clinching','optical_fiber':'step_index_guidance',
 'electric_relay':'electromagnetic_relay','snap_thermostat':'snap_disc_switch','clothespin':'torsion_peg',
 'float_valve':'tank_float_control','combination_lock':'gated_padlock',
 'camera_iris':'optical_iris',
 'bascule_bridge':'bascule_bridge', 'photovoltaic_cell':'photovoltaic_cell',
 'piston_pump':'piston_pump', 'wind_turbine':'rotary_generator', 'hand_generator':'rotary_generator',
 'rack_pinion':'mechanism_bench','lead_screw':'mechanism_bench','cam_follower':'mechanism_bench',
 'lever_balance':'science_diagram','resistive_circuit':'science_diagram','hydraulic_lift':'science_diagram',
 'thermal_contact':'science_diagram','dna_pairing':'science_diagram','water_transfer':'science_diagram',
}
PATTERNS={
 'pendulum_clock':r'\b(pendulum|grandfather clock|escapement|clock)\b',
 'zipper':r'\b(zipper|zip fastener)\b',
 'stapler':r'\b(stapler|stapling|clinching anvil)\b',
 'optical_fiber':r'\b(optical fib(?:er|re)|fibre.optic|fiber.optic|total internal reflection)\b',
 'electric_relay':r'\brelay\b','snap_thermostat':r'\b(thermostat|bimetal|snap.disc)\b','clothespin':r'\b(clothespin|clothes.peg|clothes.pin)\b',
 'float_valve':r'\b(float valve|ballcock|tank.{0,30}float|float.{0,30}tank)\b',
 'combination_lock':r'\b(padlock|combination lock|tumbler wheel|locking bar)\b',
 'camera_iris':r'\b(camera|lens)\b.{0,60}\b(aperture|iris|diaphragm)\b|\b(aperture|iris)\b.{0,60}\b(camera|lens)\b',
 'bascule_bridge':r'\b(bascule|drawbridge|bridge|trunnion)\b',
 'photovoltaic_cell':r'\b(solar|photovoltaic)\b',
 'piston_pump':r'\b(piston pump|pump|pumping)\b',
 'wind_turbine':r'\b(wind|turbine|turbines)\b',
 'hand_generator':r'\b(hand.?crank|cranked|cranking|crank handle|handle.{0,25}lamp|generator)\b',
 'rack_pinion':r'\b(rack|pinion)\b','lead_screw':r'\blead.?screw\b','cam_follower':r'\b(cam|follower)\b',
 'lever_balance':r'\b(lever|seesaw)\b','resistive_circuit':r'\b(resistor|resistive|ohmic)\b',
 'hydraulic_lift':r'\bhydraulic\b','thermal_contact':r'\b(thermal|heat|temperature)\b',
 'dna_pairing':r'\bdna\b','water_transfer':r'\bwater.{0,20}reservoir\b',
}

def entities(value):
 if isinstance(value,list):
  for item in value:yield from entities(item)
 elif isinstance(value,dict):
  if any(k in value for k in ('topic','title','mechanism','visual_family','subject','tag','video')):yield value
  for item in value.values():
   if isinstance(item,(dict,list)):yield from entities(item)

def story_of(value):
 """'family::story' -> ('family','story'); a plain family has no story."""
 return tuple(value.split('::',1)) if isinstance(value,str) and '::' in value else (value,None)

def families(row):
 found=set();storied=bool(row.get('story'))
 for key in ('visual_family','mechanism','subject','prototype'):
  value=row.get(key)
  if isinstance(value,str):
   if '::' in value and story_of(value)[0] in set(FAMILIES.values()):found.add(value);storied=True;continue
   if value in FAMILIES:found.add(FAMILIES[value])
   elif value in set(FAMILIES.values()):found.add(value)
   elif value.startswith('recipe_'):found.add(value)   # kit recipe machines: the family is the recipe key itself
 text=' '.join(str(row.get(k,'')) for k in ('topic','title','topic_key','description')).lower().replace('_',' ')
 if storied:return found   # a story video names its own story; its words must not also spend the machine's original story
 for key,pattern in PATTERNS.items():
  if re.search(pattern,text):found.add(FAMILIES[key])
 return found

def identity(topic,mechanism=None,story=None):
 if mechanism is not None:
  if mechanism not in FAMILIES:raise ValueError('Unregistered visual family; novelty cannot be established')
  from studio_lib import stories
  story=story if story is not None else stories.current()
  if story:
   if not stories.find(mechanism,story):raise ValueError('Unknown story for this machine; novelty cannot be established')
   return FAMILIES[mechanism]+'::'+story
  return FAMILIES[mechanism]
 found=families({'topic':topic})
 if len(found)!=1:raise ValueError('A single registered visual family is required before generation')
 return next(iter(found))

def pending_owner(row,owner):
 if owner is None:return False
 belongs=any(str(row.get(k))==str(owner) for k in ('owner','record_run','run_id'))
 if not belongs and os.environ.get('GITHUB_ACTIONS')=='true':
  provenance=Path('daily-resume-provenance.json')
  if provenance.exists():
   data=json.loads(provenance.read_text())
   trusted=data.get('source_run')==str(owner) and data.get('current_run')==os.environ.get('GITHUB_RUN_ID') and data.get('topic')==row.get('topic')
   if trusted:belongs=str(row.get('record_run')) in data.get('verified_recovery_run_ids',[])
 produced=any(row.get(k) for k in ('video','tag','media_sha256','published_at','scheduled_at')) or row.get('state') in ('created','rendered','scheduled','published','skipped','deleted','saved')
 return belongs and not produced and (row.get('state')=='reserved' or row.get('failed') is True)

def reason(topic,mechanism,rows,owner=None):
 try:family=identity(topic,mechanism)
 except ValueError as e:return str(e)
 prior=[row for row in rows if not pending_owner(row,owner)]
 repeated=duplicate(topic,prior)
 if repeated:return repeated+'; no reworded or corrected copy is allowed'
 if any(family in families(row) for row in prior):
  return 'Visual setup already used or reserved: '+family+'; a new title, format or camera angle is not a new video'
 return ''

def records(root=None):
 base=Path(root) if root else Path(__file__).resolve().parent.parent
 paths=[MEMORY,'data/scenes/history.json','data/scenes/videos.json','data/scenes/topic-ledger.json']
 rows=[]
 cloud=root is None and os.environ.get('GITHUB_ACTIONS')=='true' and bool(os.environ.get('GH_TOKEN'))
 for name in paths:
  if cloud:
   from studio_lib.service_queue import read_document
   data,_=read_document(name,None)
  else:
   path=base/name
   if not path.is_file():raise ValueError('Permanent novelty history missing; generation held: '+name)
   data=json.loads(path.read_text())
  if not isinstance(data,list) or any(not isinstance(r,dict) for r in data):raise ValueError('Permanent novelty history is invalid: '+name)
  if name==MEMORY and (not data or any(not isinstance(r.get('topic'),str) or not r['topic'].strip() or not isinstance(r.get('state'),str) for r in data)):
   raise ValueError('Permanent novelty history was emptied or damaged; never reset originality memory')
  rows.extend(data)
 for name in ('data/scenes/publishing-status.json','data/scenes/review/index.json'):
  path=base/name
  if path.exists():rows.extend(entities(json.loads(path.read_text())))
 review=base/'data/scenes/review'
 if review.exists():
  for path in review.glob('*/*/*.json'):rows.extend(entities(json.loads(path.read_text())))
 return rows

def require_new(topic,mechanism=None,owner=None,root=None):
 owner=os.environ.get('GITHUB_RUN_ID') if owner is None else owner
 error=reason(topic,mechanism,records(root),owner)
 if error:raise ValueError('Permanent no-repeat policy: '+error)
 return identity(topic,mechanism)

_STOP=set('a an the and or of to in on is are does do how why what when which that this it its before until only for with from by as at be can'.split())
def _words(t):
 t=re.sub(r'[^a-z ]',' ',str(t).lower().replace('\u2011','-'))
 return {w[:5] for w in t.split() if w not in _STOP and len(w)>2}
def story_repeats_earlier(question,mechanism,rows,limit=.5):
 """True when a story's question mostly repeats the topic or title of an earlier finished video of the same machine."""
 q=_words(question)
 if not q:return False
 for r in rows:
  if r.get('failed') or r.get('failure_cause'):continue
  if (r.get('mechanism') or r.get('subject'))!=mechanism:continue
  for key in ('topic','title'):
   t=_words(r.get(key,''))
   if t and len(q&t)/len(q)>=limit:return True
 return False

def available_pairs(catalog,rows,owner=None):
 """Every (machine, story) still unspent: story None = the machine's original video. Hand-built machines only (kit recipes stay paused)."""
 from studio_lib import stories
 blocked=set().union(*(families(r) for r in rows if not pending_owner(r,owner))) if rows else set()
 out=[]
 for k in catalog:
  if k not in FAMILIES or k.startswith('recipe_'):continue
  if FAMILIES[k] not in blocked:out.append((k,None))
  for s in stories.stories_for(k):
   if FAMILIES[k]+'::'+s['id'] in blocked:continue
   if story_repeats_earlier(s.get('question',''),k,rows):continue   # same question as an earlier video of this machine = same video to a viewer
   out.append((k,s['id']))
 firsts=[x for x in out if x[1] is None]
 if firsts:return firsts   # owner rule 2026-11-24: no machine is shown a second time until every machine has had its first video
 return out if os.environ.get('CE_STORIES')=='on' else []   # owner 2026-11-24: a retelling of a machine already published looks like the same video; OFF until the owner asks (CE_STORIES=on)

def unused(catalog,rows,owner=None):
 blocked=set().union(*(families(r) for r in rows if not pending_owner(r,owner))) if rows else set()
 return {k:v for k,v in catalog.items() if k in FAMILIES and FAMILIES[k] not in blocked}

def reserve_new(topic,mechanism=None):
 """Claim the visual family atomically before any writing/voice/render call."""
 family=identity(topic,mechanism)
 if os.environ.get('GITHUB_ACTIONS')!='true' or not os.environ.get('GH_TOKEN'):
  raise ValueError('Production novelty reservation requires the cloud job')
 from studio_lib.service_queue import read_document,write_document
 from studio_lib.durable_topics import reservation_owner
 owner=reservation_owner(topic)
 for attempt in range(6):
  ledger,sha=read_document(MEMORY,None)
  if not isinstance(ledger,list) or not ledger:raise ValueError('Permanent novelty ledger unavailable or emptied')
  error=reason(topic,mechanism,records()+ledger,owner)
  if error:raise ValueError('Permanent no-repeat policy: '+error)
  if any(r.get('owner')==owner and r.get('topic')==topic and r.get('state')=='reserved' for r in ledger):return family
  entry={'topic':topic,'visual_family':family,'owner':owner,'state':'reserved','policy':POLICY}
  if mechanism:entry['mechanism']=mechanism
  ledger.append(entry)
  try:write_document(MEMORY,ledger,sha,'Reserve an unused idea and visual setup before media');return family
  except urllib.error.HTTPError as error:
   if error.code not in (409,422) or attempt==5:raise
   time.sleep(1)

def record_created(topic,mechanism,path):
 """Remember the first encoded video even if later quality or delivery fails."""
 if os.environ.get('GITHUB_ACTIONS')!='true' or not os.environ.get('GH_TOKEN'):
  raise ValueError('Production novelty records must be saved by the cloud job')
 from studio_lib.service_queue import read_document,write_document
 from studio_lib.durable_topics import reservation_owner
 row={'topic':topic,'mechanism':mechanism,'visual_family':identity(topic,mechanism),
      'state':'created','owner':reservation_owner(topic),'encoded_run':os.environ['GITHUB_RUN_ID'],'policy':POLICY,
      'media_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
 for attempt in range(6):
  ledger,sha=read_document(MEMORY,None)
  if not isinstance(ledger,list) or not ledger:raise ValueError('Permanent novelty ledger unavailable or emptied')
  if any(r.get('media_sha256')==row['media_sha256'] for r in ledger):return
  error=reason(topic,mechanism,ledger,row['owner'])
  if error:raise ValueError('Permanent no-repeat policy: '+error)
  ledger.append(row)
  try:write_document(MEMORY,ledger,sha,'Remember rendered visual family permanently, regardless of review result');return
  except urllib.error.HTTPError as error:
   if error.code not in (409,422) or attempt==5:raise
   time.sleep(1)

def audit():
 from studio_lib.registry import REGISTRY
 rows=records()
 return {'policy':POLICY,'history_records':len(rows),'used_visual_families':sorted(set().union(*(families(r) for r in rows))),
         'unused_daily_components':list(unused(REGISTRY,rows)),'generation_requests':0,'rendered_videos':0}

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description='Read-only audit of permanent novelty history; never generates media')
 parser.add_argument('--audit',action='store_true',required=True);parser.parse_args()
 print(json.dumps(audit(),indent=2))

from studio_lib import machine_spec
machine_spec.ensure_loaded()
