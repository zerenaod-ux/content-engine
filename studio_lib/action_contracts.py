"""Component-owned narration and kinematic release checks, not acting scores."""
import json,re,hashlib,math
from pathlib import Path
import numpy as np

CONTRACTS={
 'float_valve':{
  'subjects':[r'tank|water|float|level',r'cutaway',r'float|ball',r'washer|seal|stem|seat|plug|valve',r'valve|washer|inlet|seal',r'outlet|drain|draw.off|tap',r'float|water|level|valve',r'tank|level|water|float'],
  'moves':{1:{'cut':1},2:{'level':1,'float_z':1,'gap':-1},3:{'level':1,'float_z':1,'gap':-1},5:{'level':-1,'float_z':-1,'gap':1},6:{'level':1,'float_z':1,'gap':-1},7:{'cut':-1}},
  'holds':{0:['level','float_z'],1:['level','float_z'],4:['level','float_z','gap'],7:['level','float_z','gap']},
  'visible':[(2,'float'),(2,'rod'),(3,'plug'),(3,'seat'),(2,'flow'),(5,'drain')]},
 'combination_lock':{
  'subjects':[r'lock|shackle|wheel|combination',r'cutaway',r'first|wheel',r'second|wheel',r'third|wheel|gate',r'bar|tab|fence',r'shackle|loop',r'lock|shackle|gate|wheel|bar'],
  'moves':{1:{'cut':1},2:{'wheel0':-1},3:{'wheel1':1},4:{'wheel2':-1,'bar_z':-1},6:{'shackle':1},7:{'cut':-1}},
  'holds':{0:['wheel0','wheel1','wheel2','bar_z','shackle'],1:['wheel0','wheel1','wheel2','bar_z','shackle'],2:['wheel1','wheel2','shackle'],3:['wheel0','wheel2','shackle'],5:['wheel0','wheel1','wheel2','bar_z','shackle'],6:['wheel0','wheel1','wheel2','bar_z'],7:['wheel0','wheel1','wheel2','bar_z','shackle']},
  'visible':[(2,'wheels'),(5,'gates'),(5,'bar'),(5,'spring'),(6,'shackle')]},
}

def narration_errors(plan):
 kind=plan.get('mechanism');contract=CONTRACTS.get(kind);errors=[]
 if not contract:return errors
 for i,b in enumerate(plan.get('beats',[])):
  if i>=8:break
  text=b.get('say','').lower()
  if not re.search(contract['subjects'][i],text):errors.append(f'beat {i}: name the actual visible part for this action, not a generic description')
  if kind=='float_valve':
   if i in (4,7) and re.search(r'\b(float|ball|water|level|washer|inlet|valve)\s+(rises|falls|opens|closes|moves|refills|returns|starts)\b',text):errors.append(f'beat {i}: water, float and inlet are already held; do not announce another movement')
   if re.search(r'\b(float|ball)\s+(plugs|seals|blocks)\s+(the\s+)?(inlet|pipe|seat)\b',text):errors.append(f'beat {i}: the washer seals the inlet; the floating ball does not plug it')
   if i in (0,1) and re.search(r'\b(water|float|ball|level)\s+(rises|falls|starts|fills)\b',text):errors.append(f'beat {i}: the low-water pose is held until the fill beat')
  else:
   if i==5 and re.search(r'\b(bar|fence|tab)\s+(drops|falls|descends|moves|slides|settles)\b',text):errors.append(f'beat {i}: the bar is already seated; describe its held clearance, not another drop')
   if i in (0,1,2,3,4,5,7) and re.search(r'\b(shackle|loop)\s+(lifts|rises|opens|jumps|springs|moves|returns)\b',text):errors.append(f'beat {i}: only the pull beat lifts the shackle; all other beats hold it')
   if re.search(r'\b(hand|motor|battery|key)\s+(turns|spins|drives|opens|powers)\b',text):errors.append(f'beat {i}: no hand, motor, key or battery is depicted')
 return errors

def channels(state):
 d={k:float(v) for k,v in state.items() if isinstance(v,(int,float))}
 for i,a in enumerate(state.get('angles',[])):d['wheel'+str(i)]=float(a)
 return d

def fingerprint(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def verify_motion(kind,module,tl,out,plan=None):
 contract=CONTRACTS.get(kind)
 if not contract:raise ValueError('No component-owned causal motion contract; hold before encoding')
 rows=[];errors=[]
 for i,beat in enumerate(tl['beats']):
  a,b=beat.get('motion_window',(beat['start'],beat['end']))
  samples=[channels(module.state(t,tl)) for t in np.linspace(a+1e-5,b-1e-5,41)]
  for key,sign in contract['moves'].get(i,{}).items():
   delta=samples[-1][key]-samples[0][key]
   if sign*delta<.02:errors.append(f'beat {i}: narrated {key} movement is absent or reversed')
   rows.append({'beat':i,'channel':key,'expected_direction':sign,'delta':delta})
  for key in contract['holds'].get(i,[]):
   span=max(s[key] for s in samples)-min(s[key] for s in samples)
   if span>1e-5:errors.append(f'beat {i}: {key} changed during a held-state explanation')
   rows.append({'beat':i,'channel':key,'expected':'held','range':span})
  for t in np.linspace(a+1e-5,b-1e-5,41):
   p=module.state(t,tl)
   if kind=='float_valve':
    if p['gap']<-1e-7 or (p['gap']<1e-7 and p['flow']>1e-6):errors.append('Water crosses a closed inlet')
    if abs(np.linalg.norm(np.array(p['float_center'])-module.PIVOT)-module.ARM)>1e-6:errors.append('Float rod stretched or disconnected')
   else:
    if p['shackle']>0 and p['free']<.999:errors.append('Shackle lifted before all gates and locking tab cleared')
    if p['bar_z']<module.BAR_HIGH-1e-5 and not module.aligned(p['angles']):errors.append('Locking bar crossed an unaligned wheel rim')
 result={'plan_sha256':fingerprint(plan),'timeline_sha256':fingerprint(tl),'contract':'component-causal-motion-v1','mechanism':kind,'errors':sorted(set(errors)),'measurements':rows,'scope':'Measured timeline linked to actual renderer state; pixel visibility is checked separately'}
 Path(out,'causal-motion-checks.json').write_text(json.dumps(result,indent=2))
 return result['errors']


def evidence_errors(report,plan,timeline):
 errors=[];contract=CONTRACTS.get(plan.get('mechanism'))
 if not contract:return ['No registered causal motion contract']
 if report.get('plan_sha256')!=fingerprint(plan) or report.get('timeline_sha256')!=fingerprint(timeline):errors.append('Causal motion evidence belongs to a different plan or timeline')
 expected={(i,key):('move',sign) for i,values in contract['moves'].items() for key,sign in values.items()}
 expected.update({(i,key):('held',None) for i,keys in contract['holds'].items() for key in keys})
 rows=report.get('measurements',[]);seen=set()
 for row in rows:
  key=(row.get('beat'),row.get('channel'))
  if key not in expected or key in seen:errors.append('Unexpected or duplicate causal measurement');continue
  seen.add(key);mode,sign=expected[key];value=row.get('delta') if mode=='move' else row.get('range')
  if not isinstance(value,(int,float)) or not math.isfinite(value):errors.append('Missing finite causal measurement');continue
  if mode=='move' and value*sign<.02:errors.append('Measured causal action is absent or reversed')
  if mode=='held' and abs(value)>1e-5:errors.append('Measured held state changed')
 if seen!=set(expected):errors.append('Causal motion evidence is incomplete')
 return errors
