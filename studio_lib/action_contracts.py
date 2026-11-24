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

CONTRACTS.update({
 'electric_relay':{
  'subjects':[r'relay|circuit|signal|coil',r'cutaway',r'switch|coil|current',r'armature|contact|attraction',r'contact|coil|circuit|lamp',r'switch|spring|coil',r'contact|spring|coil|lamp',r'relay|circuit|electromagnet'],
  'moves':{1:{'cut':1},2:{'current':1,'switch':1},3:{'angle':-1,'gap':-1,'powered':1},5:{'angle':1,'gap':1,'powered':-1},7:{'cut':-1}},
  'holds':{0:['angle','current','powered'],1:['angle','current','powered'],2:['angle','powered'],4:['angle','current','powered'],6:['angle','current','powered'],7:['angle','current','powered']},
  'visible':[(2,'coil'),(2,'field'),(3,'armature'),(3,'core'),(5,'spring'),(4,'load')]},
 'snap_thermostat':{
  'subjects':[r'thermostat|heat|temperature|switch',r'cutaway',r'heat|temperature|metal|disc',r'disc|pin|contact',r'contact|disc|circuit|lamp',r'heat|cool|temperature',r'disc|pin|contact|reset',r'thermostat|temperature|switch|circuit'],
  'moves':{1:{'cut':1},2:{'temperature':1},3:{'hot':1,'pin_top':1,'gap':1,'powered':-1},5:{'temperature':-1},6:{'hot':-1,'pin_top':-1,'gap':-1,'powered':1},7:{'cut':-1}},
  'holds':{0:['hot','gap','powered'],1:['hot','gap','powered'],2:['hot','gap','powered'],4:['hot','gap','powered'],5:['hot','gap','powered'],7:['hot','gap','powered']},
  'visible':[(3,'disc'),(3,'pin'),(3,'contacts'),(2,'heat'),(7,'current')]},
 'clothespin':{
  'subjects':[r'peg|clothespin|handle|jaw|fabric',r'spring|fulcrum|coil',r'handle|input|squeeze',r'jaw|spring|handle',r'fabric|cloth|fold',r'spring|input|jaw|release',r'fabric|jaw|spring|grip',r'peg|clothespin|spring|grip|fabric'],
  'moves':{2:{'angle':1,'gap':1,'spring_twist':1},4:{'cloth_x':-1,'inserted':1},5:{'angle':-1,'gap':-1,'spring_twist':-1}},
  'holds':{0:['angle','gap','spring_twist'],1:['angle','gap','spring_twist'],3:['angle','gap','spring_twist'],4:['angle','gap','spring_twist'],6:['angle','gap','spring_twist','cloth_x'],7:['angle','gap','spring_twist','cloth_x']},
  'visible':[(2,'jaws'),(2,'spring'),(2,'input'),(4,'cloth')]}
})


CONTRACTS.update({
 'pendulum_clock':{
  'subjects':[r'clock|pendulum|weight|hand',r'cutaway',r'pendulum|rod|bob|swing',r'anchor|pallet|escape|wheel|teeth',r'tooth|teeth|wheel|hand|tick',r'weight|cord|drum|gear',r'pendulum|anchor|wheel|weight|push',r'clock|pendulum|hand|weight'],
  'moves':{1:{'cut':1},3:{'turn':1},4:{'turn':1},5:{'weight_z':-1},7:{'cut':-1}},
  'holds':{0:['cut'],2:['cut'],3:['cut'],4:['cut'],5:['cut'],6:['cut']},
  'visible':[(2,'pendulum'),(3,'anchor'),(3,'escape'),(5,'weight')]},
 'ratchet_wrench':{
  'subjects':[r'wrench|ratchet|handle|bolt',r'cutaway',r'handle|pawl|wheel|tooth|teeth|bolt',r'handle|pawl|tooth|teeth|wheel|click|bolt',r'pawl|spring|tooth|teeth|wheel|handle',r'handle|pawl|tooth|teeth|click|bolt|wheel',r'tooth|teeth|pawl|slope|sloped|steep|face|wheel|bolt',r'wrench|ratchet|bolt|handle|pawl'],
  'moves':{1:{'cut':1},2:{'handle':1,'wheel':1},3:{'handle':-1},4:{'handle':1,'wheel':1},5:{'handle':-1},7:{'cut':-1}},
  'holds':{0:['handle','wheel','cut'],1:['handle','wheel'],2:['cut'],3:['wheel','cut'],4:['cut'],5:['wheel','cut'],6:['handle','wheel','cut'],7:['handle','wheel']},
  'visible':[(2,'wheel'),(2,'input'),(3,'pawl'),(4,'spring'),(5,'bolt')]},
 'zipper':{
  'subjects':[r'zipper|teeth|tape|slider',r'cutaway',r'slider|guide|teeth',r'slider|head|teeth',r'slider|stop|chain',r'head|teeth|slider',r'slider|divider|teeth',r'zipper|slider|tapes'],
  'moves':{1:{'cut':1},2:{'slider':1,'joined':1},3:{'slider':1,'joined':1},4:{'slider':1,'joined':1},6:{'slider':-1,'joined':-1},7:{'cut':-1}},
  'holds':{0:['slider','joined'],1:['slider','joined'],5:['slider','joined'],7:['slider','joined']},
  'visible':[(2,'teeth'),(2,'guides'),(2,'divider'),(3,'tapes'),(3,'slider')]},
 'stapler':{
  'subjects':[r'stapler|paper|staple|handle',r'cutaway',r'spring|magazine|staple',r'handle|driver|leg',r'leg|anvil|driver',r'staple|driver|leg',r'handle|driver|magazine',r'stapler|handle|staple'],
  'moves':{1:{'cut':1},2:{'feed':1},3:{'driver_z':-1,'crown_z':-1},4:{'crown_z':-1,'bend':1},6:{'driver_z':1,'next_feed':1},7:{'cut':-1}},
  'holds':{0:['feed','driver_z','bend'],1:['feed','driver_z','bend'],2:['driver_z','bend'],3:['bend'],5:['driver_z','crown_z','bend'],6:['crown_z','bend'],7:['driver_z','crown_z','bend']},
  'visible':[(2,'magazine'),(2,'spring'),(3,'driver'),(4,'anvil'),(3,'input')]},
 'optical_fiber':{
  'subjects':[r'cable|fibre|fiber|light',r'cutaway',r'pulse|light|core',r'pulse|light|cladding|reflect',r'pulse|core|light|receiver',r'pulse|light|path',r'pulse|receiver|indicator',r'cable|receiver|fibre|fiber'],
  'moves':{1:{'cut':1},2:{'front':1},3:{'front':1},4:{'front':1,'output':1},7:{'cut':-1}},
  'holds':{0:['front','output'],1:['front','output'],5:['front','output'],6:['front','output'],7:['front','output']},
  'visible':[(3,'rays'),(3,'core'),(3,'cladding'),(5,'pulse'),(6,'detector')]}
})

def narration_errors(plan):
 kind=plan.get('mechanism');contract=CONTRACTS.get(kind);errors=[]
 if not contract:return errors
 for i,b in enumerate(plan.get('beats',[])):
  if i>=8:break
  text=b.get('say','').lower()
  if not re.search(contract['subjects'][i],text):errors.append(f'beat {i}: name the actual visible part for this action, not a generic description')
  if kind=='float_valve':
   if re.search(r'\b(keeps?|controls?|regulates?|maintains?)\s+(?:the\s+)?pressure\b|\bpressure\s+(?:steady|constant)\b',text):errors.append(f'beat {i}: the float valve controls level, not regulated pressure')
   if re.search(r'\bfloating (disc|disk)\b',text):errors.append(f'beat {i}: the visible float is a ball, not a disc')
   if re.search(r'\b(burst\w*|explod\w*)\b',text):errors.append(f'beat {i}: the open tank depicts overflow prevention, not a burst or explosion')
   if i==4 and not re.search(r'\b(held|holds?|holding|still|stays?|remains?|rests?|resting|seated|already)\b',text):errors.append(f'beat {i}: explicitly explain the already held high level and seated washer, without announcing the motion again')
   if i in (4,7) and re.search(r'\b(float|ball|water|level|washer|inlet|valve)\s+(rises|falls|opens|closes|moves|refills|returns|starts)\b',text):errors.append(f'beat {i}: water, float and inlet are already held; do not announce another movement')
   if re.search(r'\b(float|ball)\s+(plugs|seals|blocks)\s+(the\s+)?(inlet|pipe|seat)\b',text):errors.append(f'beat {i}: the washer seals the inlet; the floating ball does not plug it')
   if i in (0,1) and re.search(r'\b(water|float|ball|level)\s+(rises|falls|starts|fills)\b',text):errors.append(f'beat {i}: the low-water pose is held until the fill beat')
  elif kind=='combination_lock':
   if i==5 and not re.search(r'\b(held|holds?|holding|still|stays?|remains?|rests?|resting|seated|already)\b',text):errors.append(f'beat {i}: the locking bar is already seated; explain that held state')
   if i==5 and re.search(r'\b(bar|fence|tab)\s+(drops|falls|descends|moves|slides|settles)\b',text):errors.append(f'beat {i}: the bar is already seated; describe its held clearance, not another drop')
   if i in (0,1,2,3,4,5,7) and re.search(r'\b(shackle|loop)\s+(lifts|rises|opens|jumps|springs|moves|returns)\b',text):errors.append(f'beat {i}: only the pull beat lifts the shackle; all other beats hold it')
   if re.search(r'\b(hand|motor|battery|key)\s+(turns|spins|drives|opens|powers)\b',text):errors.append(f'beat {i}: no hand, motor, key or battery is depicted')
  elif kind=='electric_relay':
   if i in (1,2,4,6,7) and re.search(r'\barmature\s+(moves|pivots|lowers|rises|descends|returns|turns)\b',text):errors.append(f'beat {i}: the armature is held in this phase; do not announce another stroke')
   if i in (4,6,7) and re.search(r'\bcontacts?\s+(open|opens|close|closes|separate|separates|touch|touches)\b',text):errors.append(f'beat {i}: contacts are already held in their documented state')
   if re.search(r'\bcoil\s+(creates|generates|supplies)\s+(?:the\s+)?load (?:power|energy)\b',text):errors.append(f'beat {i}: the separate load supply provides its energy')
  elif kind=='snap_thermostat':
   if i in (1,2,4,5,7) and re.search(r'\b(disc|pin|contact)\s+(snaps|moves|rises|lowers|bends|opens|closes|returns)\b',text):errors.append(f'beat {i}: the mechanism is held until its assigned snap/reset phase')
   if re.search(r'\b(melts|melting|burns|fire|digital processor)\b',text):errors.append(f'beat {i}: no melting, fire or digital controller is depicted')
  elif kind=='pendulum_clock':
   if re.search(r'\b(spring|battery|quartz|motor|electric\w*|minute hand|hour hand)\b',text):errors.append(f'beat {i}: only a falling weight and one seconds hand are depicted; no spring, motor, battery or minute/hour hands')
   if re.search(r'\b(never loses|perfectly accurate|exactly accurate|speeds up|slows down)\b',text):errors.append(f'beat {i}: do not claim perfect accuracy or changing swing speed')
   if re.search(r'\bheavier (?:bob|pendulum)\b[^.!?]{0,40}(?:faster|slower)',text):errors.append(f'beat {i}: swing time depends on rod length, not bob mass')
  elif kind=='ratchet_wrench':
   if re.search(r'\b(motor|battery|electric\w*|torque wrench|impact wrench|cordless)\b',text):errors.append(f'beat {i}: only a manual one-way ratchet is depicted')
   if re.search(r'\b(reverse|reverses|reversing|reversible|switch|flip the)\b',text):errors.append(f'beat {i}: no reversing switch is depicted')
   if i in (3,5) and re.search(r'\bbolt\s+(turns|rotates|spins|loosens|tightens|moves|backs)\b',text):errors.append(f'beat {i}: the bolt holds still while the handle swings back')
   if re.search(r'\b(hand|finger)\s+(pushes|pulls|swings|turns|grips)\b',text):errors.append(f'beat {i}: input is shown with an arrow, not a hand')
  elif kind=='zipper':
   if re.search(r'\bteeth\s+(bend|stretch|melt|flex)\b',text):errors.append(f'beat {i}: metal teeth translate rigidly; only fabric tapes bend')
   if i in (0,1,5,7) and re.search(r'\bslider\s+(moves|travels|reverses|advances|slides)\b',text):errors.append(f'beat {i}: slider is held during this explanation')
   if re.search(r'automatic lock|locking pawl|waterproof',text):errors.append(f'beat {i}: no locking pawl or waterproof seal is depicted')
  elif kind=='stapler':
   if i<4 and re.search(r'\blegs?\s+(bend|bends|curl|curls|fold|folds)\b',text):errors.append(f'beat {i}: staple legs stay straight until the anvil-clinching phase')
   if i in (5,6,7) and re.search(r'\bstaple\s+(bends|moves|descends|rises|returns)\b',text):errors.append(f'beat {i}: the clinched staple stays in the paper')
   if re.search(r'\b(hand|motor|finger)\s+(presses|pushes|drives)\b',text):errors.append(f'beat {i}: manual input is illustrated with arrows; no hand or motor is shown')
  elif kind=='optical_fiber':
   if re.search(r'\b(perfect|lossless|every angle|all angles|no loss)\b',text):errors.append(f'beat {i}: this accepted ray model does not establish lossless guidance at every angle')
   if re.search(r'critical angle[^.!?]{0,40}(?:from|to) the (?:axis|surface)\b',text):errors.append(f'beat {i}: incidence/critical angle is measured from the interface normal')
   if re.search(r'\b(electrons|electricity|packets?|bits?)\b',text):errors.append(f'beat {i}: only guided light and a receiver indicator are depicted')
  elif kind=='clothespin':
   if i in (1,3,4,6,7) and re.search(r'\bjaws?\s+(open|opens|close|closes|move|moves|rotate|rotates)\b',text):errors.append(f'beat {i}: the jaws are held; no extra movement occurs here')
   if re.search(r'\bwood\s+(bends|flexes|stretches)\b',text):errors.append(f'beat {i}: the wooden members rotate rigidly; only the metal spring elastically deforms')
   if re.search(r'\b(hand|finger|motor)\s+(pushes|squeezes|turns|drives)\b',text):errors.append(f'beat {i}: input is shown with labeled arrows, not a hand or motor')
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
   elif kind=='electric_relay':
    if p['powered'] and (p['gap']>.003 or p['current']<=0):errors.append('Relay load powered without energized touching contacts')
   elif kind=='snap_thermostat':
    if p['powered'] and p['gap']>.001:errors.append('Thermostat lamp powered across an open gap')
   elif kind=='clothespin':
    if p['beat']>=5 and p['gap']<module.THICKNESS-1e-6:errors.append('Jaws passed through the inserted fabric')
   elif kind=='ratchet_wrench':
    if p['pawl_r']<module.R0-1e-6 or p['pawl_r']>module.R1+1e-6:errors.append('Pawl tip left the tooth profile')
   elif kind=='stapler':
    if p['bend']>1e-6 and p['crown_z']>module.CONTACT+1e-6:errors.append('Staple bends before touching its anvil')
    for side in (-1,1):
     if module.leg_points(p['crown_z'],side)[-1][2]<module.ANVIL-1e-6:errors.append('Staple penetrated the anvil floor')
   elif kind=='optical_fiber':
    if math.pi/2-module.AXIAL<=module.CRITICAL:errors.append('Illustrated ray fails the total-internal-reflection condition')
    if p['output'] and p['front']<.999:errors.append('Receiver activates before pulse arrival')
   elif kind=='combination_lock':
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
