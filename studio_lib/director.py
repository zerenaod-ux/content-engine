from studio_lib.duration import require_duration,require_video_duration
"""Topic-selected tested mechanisms, with no generated geometry or scene edits.

Supported: bascule bridge, photovoltaic cell and single-acting piston pump.
Unsupported topics are rejected instead of receiving an unrelated component.
"""
import os,argparse,asyncio,hashlib,json,math,re,shutil,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from studio_lib.providers import call
from studio_lib import novelty
from studio_lib import narration_timing
from studio_lib.storytelling import WRITING_RULES as STORY_RULES, POLICY_VERSION as STORY_VERSION, errors as story_errors
from studio_lib.mesh import Scene,ease,ramp
from studio_lib.mechanisms import bridge,boat,APPROACHES
from studio_lib.render import BG,FONT,TITLE
from studio_lib.audio import narrate,assemble
from studio_lib.checkpoints import Checkpoint
from studio_lib.registry import REGISTRY
from studio_lib import solar,pump,wind,iris,float_valve,combination_lock,electric_relay,snap_thermostat,clothespin,zipper,stapler,optical_fiber,pendulum_clock
from studio_lib import action_contracts,visual_quality
COMPONENTS={'photovoltaic_cell':solar,'piston_pump':pump,'wind_turbine':wind,'camera_iris':iris,'float_valve':float_valve,'combination_lock':combination_lock,'electric_relay':electric_relay,'snap_thermostat':snap_thermostat,'clothespin':clothespin,'zipper':zipper,'stapler':stapler,'optical_fiber':optical_fiber,'pendulum_clock':pendulum_clock}
from studio_lib.kit import register as _kit
from studio_lib import machine_spec
machine_spec.load_all(COMPONENTS)   # one machines/<key>.json per hand-built machine installs all hookups
_kit.load_saved(COMPONENTS)   # kit recipe machines: registry, contracts and families come from saved recipes
from studio_lib.topic_scope import scope_error,require_supported

# The engine owns the safe action order. The model may choose narration,
# emphasis and framing; it cannot invent joints or disconnect rigid parts.
ACTIONS=['approach','stop','pivot','balance','drive','pass','lower','resume']
BRIEF={
 'approach':'A tall ship waits before the low road bridge. Introduce the visible problem.',
 'stop':'One car stops behind the barrier. Barriers close before the bridge moves.',
 'pivot':'STATIC close-up of the fixed trunnion. The road is held closed throughout this beat. Explain the pivot as a feature, not an action beginning now. Actual opening starts in the next balance beat.',
 'balance':'Road rises while its rigidly attached heel counterweight swings downward into its chamber.',
 'drive':'The counterweight offsets much of the load; a motor and meshing gears control motion. It does not lift for free.',
 'pass':'Hold the bridge fully raised while the tall ship passes through the opening.',
 'lower':'Only after the ship clears, the bridge lowers and the counterweight swings back up.',
 'resume':'The span seats and locks, barriers rise, and the one car crosses the continuous road.'}
def validate(plan):
    e=[]
    if not isinstance(plan,dict):return ['plan must be JSON object']
    mechanism=plan.get('mechanism')
    if not isinstance(mechanism,str) or mechanism not in REGISTRY:return ['unsupported mechanism; no generic substitute permitted']
    reason=scope_error(' '.join([str(plan.get('title',''))]+[str(b.get('say','')) for b in plan.get('beats',[]) if isinstance(b,dict)]),mechanism)
    if reason:e.append(reason)
    title=plan.get('title','')
    if not isinstance(title,str) or not 4<=len(title.split())<=8 or title.split()[0] not in ('How','Why'):e.append('title must start with How or Why and contain 4-8 words')
    if isinstance(title,str):   # the title must follow the machine's own wording rules too (no 'seesaw'/'child' on a beam-and-weight picture)
        from studio_lib import action_contracts as _ac
        for r in _ac.SPEC_RULES.get(mechanism,[]):
            if re.search(r['pattern'],title.lower()):e.append('title: '+r['message'])
    actions=REGISTRY[mechanism]['actions']
    beats=plan.get('beats',[])
    if not isinstance(beats,list) or len(beats)!=8:return e+['need exactly the eight supported action beats']
    for i,b in enumerate(beats):
        if not isinstance(b,dict):e.append('beat must be object');continue
        if b.get('action')!=actions[i]:e.append('preserve the engine safety order')
        if not isinstance(b.get('say'),str) or not 9<=len(b['say'].split())<=23:e.append(f'beat {i}: narration needs 9-23 words')
        text=b.get('say','').lower() if isinstance(b.get('say'),str) else ''
        if re.search(r'\b(show the (?:whole|complete)|return to the (?:whole|complete))\b',text):e.append(f'beat {i}: do not speak visual production directions to the audience')
        if re.search(r'\b(render|renderer|shot|storyboard|animation engine|close.up|view shifts)\b',text):e.append(f'beat {i}: speak about the mechanism, never production or camera instructions')
        if re.search(r'\bcamera\b',text) and (mechanism!='camera_iris' or re.search(r'camera (?:moves|pans|zooms|view)',text)):e.append(f'beat {i}: do not narrate production or camera instructions')
        if mechanism=='bascule_bridge' and i==2 and re.search(r'\b(begins?|starts?|starting|beginning)\b',text):e.append('pivot beat is a static close-up; opening does not begin until the balance beat')
        if mechanism=='bascule_bridge' and i==6 and re.search(r'\b(return|returns|returning|releases?|releasing|generates?)\s+energy\b',text):e.append(f'beat {i}: the rising counterweight gains gravitational potential energy while the leaf loses it; do not claim the rising weight releases energy')
        if mechanism=='bascule_bridge' and re.search(r'\bcars\b',text):e.append(f'beat {i}: this component depicts one car; use car or traffic')
        if mechanism=='photovoltaic_cell' and re.search(r'(without.{0,24}wir|no wir|wir.{0,24}(absent|hidden|not shown))',text):e.append(f'beat {i}: wires are visible in this component; do not claim they are absent')
        if mechanism=='piston_pump' and re.search(r'(each|every|both) stroke.{0,30}(deliver|push|discharg)',text):e.append(f'beat {i}: only the delivery stroke discharges water; intake does not deliver to the receiver')
        if mechanism=='piston_pump' and re.search(r'\b(upward|upwards|downward|downwards|vertically)\b',text):e.append(f'beat {i}: this pump piston moves horizontally; do not describe vertical travel')
        if mechanism=='piston_pump' and re.search(r'\b(steady|constant|continuous|uninterrupted|smooth)\s+(water|flow|discharge|stream)|\b(water|flow|discharge|stream)\s+(is|stays|remains)\s+(steady|constant|continuous|uninterrupted)',text) and not re.search(r'\b(not|never|no)\b.{0,18}\b(steady|constant|continuous|uninterrupted|smooth)\b',text):e.append(f'beat {i}: single-acting discharge is pulsating; no smoothing reservoir is shown')
        if re.search(r'\b([a-z]+)\s+\1\b',text) or re.search(r'permanent[\s\-\u2011]+magnet[\s\-\u2011]+magnets',text):e.append(f'beat {i}: remove accidentally repeated words or redundant magnet wording')
        if re.search(r'\b(today clearly|safely now|firmly still|smoothly efficiently|smoothly for all|smoothly again|significantly during operation)\b',text):e.append(f'beat {i}: replace filler added to reach a word quota with a concrete explanatory fact')
        if mechanism=='camera_iris':
            if i==7 and re.search(r'\b(?:iris|blades?|aperture|opening)\s+(?:returns?|opens?|closes?|moves?|narrows?|widens?|shrinks?)\b',text):e.append(f'beat {i}: the iris is already open and held; only the housing returns, do not announce a new iris movement')
            if i==2 and 'cutaway' not in text:e.append(f'beat {i}: name the simplified cutaway before revealing internal parts')
            if re.search(r'\b(blades?|pivots?)\b.{0,18}\b(slid\w*|translat\w*)',text):e.append(f'beat {i}: iris blades rotate about fixed pivots; they do not slide independently')
            if re.search(r'\b(doubl\w*|quadrupl\w*|sharper|focuses|zooms)\b',text):e.append(f'beat {i}: unsupported optical or numerical claim; only opening and fixed-setting exposure are illustrated')
        if b.get('camera') not in ('wide','mechanism','follow'):e.append(f'beat {i}: unsupported camera')
    words=sum(len(b['say'].split()) for b in beats if isinstance(b,dict) and isinstance(b.get('say'),str))
    minimum=128 if plan.get('story_policy')==STORY_VERSION else 120   # 128 words is about 50 s of speech: inside the 40-70 s rule; the 140 floor kept rejecting good scripts
    if not minimum<=words<=176:e.append(f'total narration needs {minimum}-176 words')
    if not isinstance(plan.get('hook'),str) or len(plan['hook'])>60:e.append('hook needs at most 60 characters')
    if plan.get('motion_policy')==narration_timing.VERSION:
        e.extend(narration_timing.cue_errors(plan))
        if not isinstance(plan.get('hook'),str) or not 2<=len(plan['hook'].split())<=7 or len(plan['hook'])>40:e.append('hook needs 2-7 simple words and at most 40 characters')
    if plan.get('story_policy')==STORY_VERSION:e.extend(story_errors(plan))
    return e
def repair_short_sections(plan,errors):
    """Repair rejected lengths without changing accepted peer sections."""
    indices=sorted({int(i) for e in errors for i in re.findall(r'beat (\d+): narration needs',e)})
    if not indices or any(not re.fullmatch(r'beat \d+: narration needs 9-23 words',e) for e in errors):return None
    request={'sections':[{'index':i,'action':plan['beats'][i]['action'],'say':plan['beats'][i]['say'],'facts':REGISTRY[plan['mechanism']]['facts'].get(plan['beats'][i]['action'],'')} for i in indices]}
    answer=call('Repair only requested narration using the supplied physical facts. Return JSON sections with index and say, each 9-23 words. Preserve all other content. '+STORY_RULES,json.dumps(request),max_tokens=1200,temperature=.3)
    result=json.loads(json.dumps(plan));seen=set()
    for row in answer.get('sections',[]):
        i=row.get('index')
        if type(i) is int and i in indices and i not in seen and isinstance(row.get('say'),str) and 9<=len(row['say'].split())<=23:
            result['beats'][i]['say']=row['say'];seen.add(i)
    return result

def repair_causal_sections(plan,issues,diagnostic=None):
    """Ask the writer to repair only rejected sections; retain valid peers."""
    if not isinstance(plan,dict) or plan.get('mechanism') not in action_contracts.CONTRACTS:return None
    beats=plan.get('beats')
    if not isinstance(beats,list) or len(beats)!=8 or not all(isinstance(b,dict) for b in beats):return None
    indices={int(i) for issue in issues for i in re.findall(r'beat (\d+):',issue)}
    global_issues=[issue for issue in issues if not re.search(r'beat \d+:',issue)]
    allowed=('total narration needs','Explain at least three','Repeated narration','Use audience-facing')
    if any(not issue.startswith(allowed) for issue in global_issues):return None
    if global_issues:
        # Preserve concise accepted hook/reveal beats. Length repair belongs in
        # the explanatory mechanism steps, not another long introduction.
        pool=range(2,8) if all(9<=len(str(beats[i].get('say','')).split())<=13 for i in (0,1)) else range(8)
        available=sorted(pool,key=lambda i:len(str(beats[i].get('say','')).split()))
        indices.update(available[:4])
    indices=sorted(i for i in indices if 0<=i<8)[:4]
    if not indices:return None
    request={'issues':issues,'sections':[{'index':i,'action':beats[i]['action'],'target_words':12 if i<2 else 22 if global_issues else 18,'state_only':i>0 and beats[i]['action']!='cutaway' and i in action_contracts.CONTRACTS[plan['mechanism']]['holds'] and not any(key!='cut' for key in action_contracts.CONTRACTS[plan['mechanism']]['moves'].get(i,{})),'facts':REGISTRY[plan['mechanism']]['facts'][beats[i]['action']]} for i in indices]}
    answer=call('Repair only these requested narration sections with fresh everyday words. Return JSON {"sections":[{"index":integer,"say":"9-23 words"}]}. Aim for target_words with factual substance, never padding or copied production directions. Preserve the action and facts. The first section, if index zero, is a concrete question ending with ?. Keep all accepted sections untouched. For a state_only section describe what is ALREADY held, seated, resting or remaining in position. Never retell how it moved there: no rising, lifting, pivoting, sealing or new closure. Write a fresh sentence from the verified snapshot; the rejected sentence is deliberately omitted. '+STORY_RULES,json.dumps(request),max_tokens=1600,temperature=.25)
    if diagnostic is not None:Path(diagnostic).write_text(json.dumps({'request':request,'response':answer},indent=2))
    result=json.loads(json.dumps(plan));seen=set()
    for row in answer.get('sections',[]):
        i=row.get('index')
        if type(i) is int and i in indices and i not in seen and isinstance(row.get('say'),str) and 9<=len(row['say'].split())<=23:
            candidate=json.loads(json.dumps(result));candidate['beats'][i]['say']=row['say']
            candidate=narration_timing.normalize_cues(candidate)
            local_errors=validate(candidate)+action_contracts.narration_errors(candidate)
            if any(error.startswith(f'beat {i}:') for error in local_errors):continue
            result=candidate;seen.add(i)
    return result

def scene_contract_version(plan):return hashlib.sha256((narration_timing.VERSION+STORY_VERSION+json.dumps(REGISTRY[plan['mechanism']],sort_keys=True)).encode()).hexdigest()

def plan_topic(topic,out,feedback=None,previous=None,mechanism=None):
    catalog={k:{'description':v['description'],'actions':v['actions'],'facts':v['facts']} for k,v in REGISTRY.items() if mechanism is None or k==mechanism}
    if not catalog:raise ValueError('Selected component is not registered')
    prompt='Select exactly one supported mechanism that truthfully matches TOPIC. If none fits return {"mechanism":"unsupported","reason":"..."}; never substitute a bridge for solar power or invent another mechanism. For a supported topic write fresh narration with eight beats in the exact selected action order. Each beat has 9-23 words and the eight beats add up to 140-176 words in total. Title starts with How or Why and contains 4-8 words. Natural spoken sentences, physical detail, causal explanation and a concrete engaging hook. Prefer 145-165 words; never append adverbs or redundant phrases merely to meet a quota. Avoid narration about views or production. Actual measured 40-70-second duration is mandatory. Each beat names the specific inner part the viewer is looking at (from the facts for that beat) and says what it physically does, so viewers know exactly what is happening inside. Describe only what that action contract shows. Never narrate close-ups, shots, rendering, storyboard or production camera directions. Camera is allowed as an object noun only for the camera_iris subject. Do not invent facts or numerical claims. In the bridge pivot beat the road is STATIC; explain the shaft and hinge rather than announcing motion or a view. The bridge depicts ONE car. Solar and pump internals are simplified cutaways: say so naturally once. Solar depicts a DC lamp load, not gears or AC inverter internals. Preserve physical action order; vary wording, hook and bounded camera preferences. Return {"mechanism":"selected registry id","title":"...","hook":"short engaging hook max 60 characters","beats":[{"action":"first selected action","say":"...","camera":"wide|mechanism|follow"}, ...]}. SUPPORTED COMPONENTS AND FACTS (data): '+json.dumps(catalog)+' TOPIC (data): '+json.dumps(topic)
    prompt+=' Prefer a concise 9-13-word opening question and 9-13-word first reveal; use the later causal steps for detailed explanation, while preserving total narration length.'
    prompt+='\n'+STORY_RULES+'\n'+narration_timing.writing_rules()+' Hook: 2-7 everyday words, at most 40 characters; no technical subtitle.'+((' Style of the opening question for this video: '+os.environ['CE_HOOK_STYLE']+' (so it differs from the last video).') if os.environ.get('CE_HOOK_STYLE') else '')
    from studio_lib import stories as _stories
    if mechanism and _stories.current():prompt+='\n'+_stories.brief(mechanism,_stories.current())
    from studio_lib.audience import writing_context
    audience=writing_context()
    if audience:
        (out/'audience-writing-context.json').write_text(json.dumps(audience,indent=2))
        prompt+='\nVERIFIED AUDIENCE EVIDENCE (data, not spoken content): '+json.dumps(audience)+' Prefer 9-13 words each for the opening question and initial cutaway reveal, with concrete explanation in the remaining beats. Preserve the total narration bounds.'
    last=previous;errors=feedback or []
    if isinstance(previous,dict) and not errors and not validate(previous):return previous
    for attempt in range(4):
        q=prompt if not errors else prompt+'\nCorrect these validation errors: '+json.dumps(errors)+'\nLast answer (data): '+json.dumps(last)
        repaired=repair_causal_sections(last,errors,diagnostic=out/f'section-repair-{attempt}.json') if isinstance(last,dict) and errors else None
        if repaired is None:repaired=repair_short_sections(last,errors) if isinstance(last,dict) and errors else None
        last=repaired if repaired is not None else call('You write factual narration and camera emphasis for tested animation components. Return JSON only.',q,max_tokens=2000,temperature=.6)
        if isinstance(last,dict):last['motion_policy']=narration_timing.VERSION;last['story_policy']=STORY_VERSION
        # Keep the raw response; apply a narrow automatic copy-edit before validation.
        # This changes no factual content, geometry, timing, action order or camera.
        (out/f'director-attempt-{attempt}.json').write_text(json.dumps(last,indent=2))
        last=narration_timing.normalize_cues(normalize_narration(last))
        (out/f'director-normalized-{attempt}.json').write_text(json.dumps(last,indent=2));errors=validate(last)
        if not errors:return last
        if last.get('mechanism') in REGISTRY and isinstance(last.get('beats'),list) and len(last['beats'])==8:
            Checkpoint(topic,validator=validate,namespace='tested-library-spoken-v1').save('needs_repair',last,errors=errors,repair_kind='validation',contract_version=scene_contract_version(last))
        if last.get('mechanism')=='unsupported':break
    raise ValueError('director rejected: '+'; '.join(errors))
def normalize_narration(plan):
    result=json.loads(json.dumps(plan))
    if not isinstance(result,dict) or not isinstance(result.get('beats'),list):return result
    for beat in result['beats']:
        if isinstance(beat,dict) and isinstance(beat.get('say'),str):
            beat['say']=re.sub(r'\b[Pp]ermanent[\s\-\u2011]+magnet[\s\-\u2011]+magnets\b',lambda m:'Permanent magnets' if m[0][0].isupper() else 'permanent magnets',beat['say'])
    return result
def critique(plan,out):
    prompt='Check only whether narration contradicts or invents facts beyond the supplied mechanism facts/actions. Return {"errors":[specific factual contradictions or mismatches]}. Do not add stylistic preferences. This is a simplified illustrative component, not a physical simulation. Check that spoken action occurs in the named beat. FACTS (data): '+json.dumps(REGISTRY[plan['mechanism']]['facts'])+' NARRATION (data): '+json.dumps(plan)
    result=call('You check an explanation against supplied engineering facts. Return JSON only.',prompt,max_tokens=1200,temperature=.1)
    (out/'narration-critique.json').write_text(json.dumps(result,indent=2))
    errors=result.get('errors')
    if not isinstance(errors,list) or not all(isinstance(e,str) for e in errors):raise ValueError('narration critique unavailable')
    return errors
def pose(t,tl):
    beats=tl['beats'];b=next((b for b in beats if b['start']<=t<b['end']),beats[-1]);i=beats.index(b);u=max(0,min(1,(t-b['start'])/(b['end']-b['start'])))
    action_u=narration_timing.progress(t,b)
    angle=0
    if i==3:angle=math.radians(52)*ease(action_u)
    elif i==4:angle=math.radians(52+20*ease(action_u))
    elif i==5:angle=math.radians(72)
    elif i==6:angle=math.radians(72)*(1-ease(action_u))
    gate=0 if i==0 else (ease(action_u*1.5) if i==1 else 1)
    if i==7:
        gate=1-ease(narration_timing.progress(t,dict(b,motion_window=b['gate_window']))) if 'gate_window' in b else 1-ramp(action_u,.30,.65)
    close=ramp(t,beats[2]['start']-.8,beats[2]['start']+1.2)*(1-ramp(t,beats[5]['start']-.8,beats[5]['start']+1.2))
    detail=ramp(t,beats[4]['start']-.4,beats[4]['start']+1.2)*(1-ramp(t,beats[4]['end']-1.5,beats[4]['end']+.3))
    balance_view=ramp(t,beats[3]['start']-.4,beats[3]['start']+1.0)*(1-ramp(t,beats[3]['end']-.8,beats[4]['start']+.3))
    zoom=(1.05*(1-close)+1.85*close)*(1-detail)+2.65*detail
    target=np.array([-2.2*close,0,1.6+.65*close])*(1-detail)+np.array([-3.1,-.55,2.3])*detail
    target=target*(1-balance_view)+np.array([-3.6,0,1.8])*balance_view
    zoom=zoom*(1-balance_view)+2.2*balance_view
    shipy=-6
    if i==5:shipy=-6+12*ease(action_u)
    elif i>=6:shipy=6+2*ease((t-beats[5]['end'])/(tl['duration']-beats[5]['end']))
    # The generated camera preference affects composition within safe bounds.
    # Ease between preferences rather than jumping at narration boundaries.
    mode=b.get('camera','wide');prior=beats[max(0,i-1)].get('camera','wide')
    values={'wide':0.0,'mechanism':1.0,'follow':.35}
    preference=values[prior]+(values[mode]-values[prior])*ramp(u,0,.3)
    zoom*=.96+.08*preference
    if i==5 and mode=='follow':target[1]+=.12*shipy*ramp(u,0,.25)
    carx=-6.7
    if i==0:carx=-8.5+1.8*ease(u)
    elif i==7:carx=-6.7+13.7*(ease(action_u) if 'gate_window' in b else ramp(action_u,.5,1))
    return dict(angle=angle,gate=gate,close=close,zoom=zoom,target=target,az=.45*(1-close)+.18*close,shipy=shipy,carx=carx)
def picture(t,tl,plan,hidden=()):
    if plan['mechanism']!='bascule_bridge':return component_picture(t,tl,plan,hidden)
    st=pose(t,tl);im=BG.copy();s=Scene(t,st['zoom'],st['target'],st['az']);water=Scene(t,st['zoom'],st['target'],st['az'])
    # Continuous setting, not a finite rectangle floating in empty space.
    water.face([[-1000,-1000,-.06],[1000,-1000,-.06],[1000,1000,-.06],[-1000,1000,-.06]],(66,160,175));water.paint(im)
    for k in range(35):
        x=math.sin(k*12.3)*10;y=((k*.91+t*.06)%22)-10
        water.face([[x,y,0],[x+.35,y,0],[x+.42,y+.02,0],[x+.07,y+.02,0]],(104,186,190))
    water.paint(im);bridge(s,st['angle'],st['close'],st['gate'],st['carx'],hidden)
    if 'ship' not in hidden:boat(s,st['shipy'])
    s.paint(im);mask=Image.new('L',(720,1280));d=ImageDraw.Draw(mask)
    for y in range(300):d.line((0,y,720,y),fill=255 if y<245 else int(255*(300-y)/55))
    im.paste(BG,(0,0),mask);d=ImageDraw.Draw(im);d.text((42,65),'HOW IT TICKS',font=FONT,fill=(31,77,89))
    import textwrap
    for j,line in enumerate(textwrap.wrap(plan['hook'],26)[:3]):d.text((42,125+j*55),line,font=TITLE,fill=(30,65,78))
    d.line((42,1195,678,1195),fill=(170,200,200),width=3);d.line((42,1195,42+636*t/tl['duration'],1195),fill=(221,102,57),width=3)
    return im
def component_camera(t,tl,plan):
    mechanism=plan['mechanism'];module=COMPONENTS[mechanism]
    beats=tl['beats'];i=min(7,next((i for i,b in enumerate(beats) if t<b['end']),7));b=beats[i];u=(t-b['start'])/(b['end']-b['start'])
    previous=beats[max(0,i-1)].get('camera','wide');mode=b.get('camera','wide')
    pref={'wide':0.0,'mechanism':1.0,'follow':.45}
    close=pref[previous]+(pref[mode]-pref[previous])*ramp(u,0,.3)
    if hasattr(module,'shot'):
        from studio_lib.camera_direction import tracked_shot
        zoom,target,az=tracked_shot(t,beats,i,module)
        from studio_lib.camera_direction import flourish
        zoom,target,az=flourish(t,beats[i],i,len(beats),zoom,target,az)
    elif mechanism=='photovoltaic_cell':target=np.array([-.1,0,2.15]);zoom=1.55+.55*close;az=.30+.08*math.sin(t*.035)
    elif mechanism=='piston_pump':target=np.array([-.4,0,2.3]);zoom=.94+.46*close;az=.34+.06*math.sin(t*.04)
    else:
        detail=ramp(t,beats[3]['start']-.8,beats[3]['start']+1.2)*(1-ramp(t,beats[6]['start']-.8,beats[6]['start']+1.2))
        target=np.array([.5*(1-detail)-.65*detail,0,3.8+1.3*detail]);zoom=1.25+1.0*detail+.08*close;az=.35+.10*math.sin(t*.04)
    v=plan.get('story_view')
    if v:zoom*=float(v['zoom']);az+=float(v['az'])   # a story looks at the same machine from a different side
    return zoom,target,az

def component_picture(t,tl,plan,hidden=(),want_scene=False,zoom_scale=1.0):
    mechanism=plan['mechanism'];module=COMPONENTS[mechanism]
    zoom,target,az=component_camera(t,tl,plan);zoom*=float(plan.get('picture_zoom',1.0))*zoom_scale   # picture check can ask for a bigger or smaller view
    base_bg=module.background() if hasattr(module,'background') else BG
    scale=visual_quality.SAMPLE_SCALE;base_bg=base_bg.resize((720*scale,1280*scale),Image.Resampling.BICUBIC)
    dark=getattr(module,'DARK',mechanism=='camera_iris')
    height=(module.elevation(t,tl) if hasattr(module,'elevation') else 10)+float((plan.get('story_view') or {}).get('elev',0))
    im=base_bg.copy();ground=Scene(t,zoom,target,az,elevation=height,raster_scale=scale,lighting=True);s=Scene(t,zoom,target,az,elevation=height,raster_scale=scale,lighting=True)
    floor=getattr(module,'FLOOR',.35 if mechanism=='camera_iris' else -.1)
    if hasattr(module,'GROUND_ALPHA'):ground.glass([[-1000,-1000,floor],[1000,-1000,floor],[1000,1000,floor],[-1000,1000,floor]],tuple(module.GROUND)+(module.GROUND_ALPHA,));ground.paint(im)   # see-through stage floor: the spotlight glows through
    else:
        ground.face([[-1000,-1000,floor],[1000,-1000,floor],[1000,1000,floor],[-1000,1000,floor]],getattr(module,'GROUND',(28,33,40) if mechanism=='camera_iris' else (218,229,224)));ground.paint(im)
    module.draw(s,t,tl,hidden);visual_quality.shadow(s,im,floor);s.paint(im)
    mask=Image.new('L',im.size);md=ImageDraw.Draw(mask)
    for y in range(300*scale):md.line((0,y,720*scale,y),fill=255 if y<245*scale else int(255*(300*scale-y)/(55*scale)))
    im.paste(base_bg,(0,0),mask);d=ImageDraw.Draw(im);d.text((42*scale,65*scale),'HOW IT TICKS',font=visual_quality.font(FONT),fill=(225,231,230) if dark else (31,77,89))
    import textwrap
    for j,line in enumerate(textwrap.wrap(plan['hook'],26)[:3]):d.text((42*scale,(125+j*55)*scale),line,font=visual_quality.font(TITLE),fill=(242,231,208) if dark else (30,65,78))
    beat=min(7,next((j for j,b in enumerate(tl['beats']) if t<b['end']),7))
    label=None
    if mechanism=='wind_turbine' and beat==5:label='Magnetic field · illustration'
    if mechanism=='photovoltaic_cell' and 2<=beat<=6:label='Charge carriers · illustration'
    if mechanism=='camera_iris' and 1<=beat<=5:label='Light paths · illustration'
    if mechanism=='camera_iris' and beat==6:label='Fixed-setting exposure illustration'
    if mechanism=='float_valve' and 2<=beat<=6:label='Water flow · illustration'
    if mechanism=='electric_relay' and 2<=beat<=5:label='Magnetic field · slowed illustration'
    if mechanism=='snap_thermostat' and 2<=beat<=6:label='Thermal action · slowed illustration'
    if mechanism=='clothespin' and beat in (2,3,4):label='Input force · illustration'
    if mechanism=='pendulum_clock' and 1<=beat<=6:label='Cutaway · simplified escapement'
    if mechanism in machine_spec.LABELS and machine_spec.LABELS[mechanism][0]<=beat<=machine_spec.LABELS[mechanism][1]:label=machine_spec.LABELS[mechanism][2]
    if mechanism.startswith('recipe_') and 1<=beat<=6:label='Simplified model · illustration'
    if mechanism=='zipper' and 1<=beat<=6:label='Enlarged slider section'
    if mechanism=='stapler' and 1<=beat<=6:label='Paper section · input force illustrated'
    if mechanism=='optical_fiber' and 1<=beat<=6:label='Enlarged ray model · slowed illustration'
    if label:d.text((42*scale,1120*scale),label,font=visual_quality.font(FONT),fill=(225,231,230) if dark else (31,77,89))
    if hasattr(module,'callouts'):
        f=visual_quality.font(FONT);placed=[]
        for text,(px,py) in module.callouts(s,t,tl):
            tb=d.textbbox((0,0),text,font=f);w=(tb[2]-tb[0])/scale+26;h=(tb[3]-tb[1])/scale+16
            x=min(max(px-w/2,20),700-w);y=min(max(py-62,300),1130)
            while any(abs(x-a)<w and abs(y-b)<h+6 for a,b in placed):y-=h+10
            placed.append((x,y))
            d.line((px*scale,py*scale,(x+w/2)*scale,(y+h)*scale),fill=(255,255,255) if dark else (31,77,89),width=2*scale)
            d.rounded_rectangle((x*scale,y*scale,(x+w)*scale,(y+h)*scale),radius=12*scale,fill=(250,244,226) if not dark else (36,48,66),outline=(31,77,89) if not dark else (140,190,220),width=2*scale)
            d.text(((x+13)*scale,(y+7)*scale),text,font=f,fill=(31,57,66) if not dark else (232,240,246))
    if mechanism.startswith('recipe_'):   # big burned-in speech captions, 3 words at a time (what the 1K+ hits had)
        from studio_lib.camera_direction import clause_starts
        b=tl['beats'][beat];cs=clause_starts(b);bend=float(b['start'])+.08+float(b.get('voice_duration') or 4.)
        parts=[q for q in re.split(r'(?<=[,;:.!?])\s+',str(b.get('say',''))) if q.strip()]
        for k,(st,txt) in enumerate(zip(cs,parts)):
            en=cs[k+1] if k+1<len(cs) else bend
            if st<=t<en:
                w=txt.split();gs=[' '.join(w[i:i+3]) for i in range(0,len(w),3)] or [txt];g=gs[min(len(gs)-1,int((t-st)/max(.01,en-st)*len(gs)))]
                f=TITLE.font_variant(size=58*scale);tb=d.textbbox((0,0),g,font=f);x=(720*scale-(tb[2]-tb[0]))/2
                d.text((x,1040*scale),g,font=f,fill=(255,255,255),stroke_width=5*scale,stroke_fill=(8,10,16));break
    d.line((42*scale,1195*scale,678*scale,1195*scale),fill=(170,200,200),width=3*scale);d.line((42*scale,1195*scale,(42+636*t/tl['duration'])*scale,1195*scale),fill=(221,102,57),width=3*scale)
    return (visual_quality.finish(im),s) if want_scene else visual_quality.finish(im)
def verify(plan,tl,out):
    if plan['mechanism']!='bascule_bridge':return verify_component(plan,tl,out)
    errors=[];roads=sorted([(x-n/2,x+n/2) for x,n in APPROACHES]+[(-5.2,2.8)])
    if any(abs(a[1]-b[0])>1e-8 for a,b in zip(roads,roads[1:])):errors.append('road has an unsupported gap')
    for t in np.linspace(0,tl['duration']-.001,250):
        st=pose(t,tl)
        if st['angle']>.02 and st['gate']<.99:errors.append('barrier unsafe');break
    for t in np.linspace(tl['beats'][5]['end']-.1,tl['duration']-.1,6):
        a=np.array(picture(t,tl,plan)).astype(int);b=np.array(picture(t,tl,plan,hidden=('ship',))).astype(int)
        if np.count_nonzero(np.max(abs(a-b),axis=2)>22)<100:errors.append('ship invisible after passage')
    for u in (.15,.5,.85):
        beat=tl['beats'][3];t=beat['start']+(beat['end']-beat['start'])*u
        a=np.array(picture(t,tl,plan)).astype(int);b=np.array(picture(t,tl,plan,hidden=('counterweight',))).astype(int)
        if np.count_nonzero(np.max(abs(a-b),axis=2)>22)<1500:errors.append('essential counterweight is obscured during its explanation')
    sheet=Image.new('RGB',(1440,1280))
    for i,b in enumerate(tl['beats']):sheet.paste(picture((b['start']+b['end'])/2,tl,plan).resize((360,640)),((i%4)*360,(i//4)*640))
    sheet.save(out/'contact.jpg');(out/'component-checks.json').write_text(json.dumps({'errors':errors,'owner_approved':False,'scope':'tested bascule bridge only'},indent=2))
    if errors:raise ValueError('; '.join(errors))
def verify_overview(plan,tl,out):
    module=COMPONENTS[plan['mechanism']]
    samples=[]
    for i,fraction in [(0,.05),(0,.5),(0,.95),(7,.95)]:
        beat=tl['beats'][i];t=beat['start']+(beat['end']-beat['start'])*fraction
        zoom,target,az=component_camera(t,tl,plan);scene=Scene(t,zoom,target,az,elevation=(module.elevation(t,tl) if hasattr(module,'elevation') else 10)+float((plan.get('story_view') or {}).get('elev',0)))
        module.draw(scene,t,tl,hidden=('light','wind'))
        points=np.array([p for _,polygon,_ in scene.faces for p in polygon])
        bounds=[points.min(axis=0).tolist(),points.max(axis=0).tolist()]
        errors=[]
        if bounds[0][0]<24 or bounds[1][0]>696 or bounds[0][1]<300 or bounds[1][1]>1165:
            errors.append('Whole-object overview clips essential physical geometry or overlaps the hook')
        samples.append({'beat':i,'fraction':fraction,'projected_bounds':bounds,'errors':errors})
    (out/'overview-checks.json').write_text(json.dumps({'samples':samples,'scope':'Whole physical component bounds in context views; not occlusion or aesthetic approval'},indent=2))
    return [error for sample in samples for error in sample['errors']]

def verify_component(plan,tl,out):
    errors=verify_overview(plan,tl,out) if tl.get('motion_policy') else []
    mechanism=plan['mechanism'];measure=[]
    if mechanism.startswith('recipe_'):
        from studio_lib.kit.recipe import framing_errors
        errors+=framing_errors(COMPONENTS[mechanism],tl)
    if mechanism in action_contracts.CONTRACTS:
        errors+=action_contracts.verify_motion(mechanism,COMPONENTS[mechanism],tl,out,plan=plan)
        evidence=action_contracts.CONTRACTS[mechanism]['visible']
    elif mechanism=='piston_pump':
        intake_start=tl['beats'][2].get('motion_window',[tl['beats'][2]['start']])[0]
        delivery_start=tl['beats'][4].get('motion_window',[tl['beats'][4]['start']])[0]
        for t in np.linspace(intake_start+.001,tl['beats'][3]['end']-.001,25):
            p=pump.phase(t,tl)
            if not p['intake'] or p['delivery']:errors.append('incorrect inlet/outlet state during intake')
        for t in np.linspace(delivery_start+.001,tl['beats'][5]['end']-.001,25):
            p=pump.phase(t,tl)
            if not p['delivery'] or p['intake']:errors.append('incorrect inlet/outlet state during delivery')
        evidence=[(3,'piston'),(5,'flow')]
    elif mechanism=='photovoltaic_cell':
        if any(solar.pose((b['start']+b['end'])/2,tl)['powered'] for b in tl['beats'][:5]):errors.append('load lit before closed-circuit beat')
        evidence=[(1,'light'),(3,'carriers'),(5,'current')]
    elif mechanism=='camera_iris':
        samples=[iris.state(t,tl) for t in np.linspace(0,tl['duration']-.001,100)]
        if any(x['area']<=0 or not 0<x['brightness']<=1.000001 for x in samples):errors.append('invalid iris opening or light relation')
        evidence=[(3,'blades'),(3,'ring'),(3,'pins'),(6,'sensor')]
    else:
        for t in np.linspace(0,tl['duration']-.001,100):
            p=wind.pose(t,tl)
            if p['angle']!=p['shaft_angle'] or p['angle']!=p['magnet_angle']:errors.append('direct-drive shaft and generator lost coupling')
        evidence=[(2,'blades'),(4,'magnets'),(6,'current')]
    for i,part in evidence:
        b=tl['beats'][i];t=(b['start']+b['end'])/2;a=np.array(picture(t,tl,plan)).astype(int);z=np.array(picture(t,tl,plan,hidden=(part,))).astype(int)
        pixels=int(np.count_nonzero(np.max(abs(a-z),axis=2)>22));measure.append({'beat':i,'part':part,'visible_pixels':pixels})
        if pixels<45:errors.append(f'{part} not visibly exposed')
    sheet=Image.new('RGB',(1440,1280))
    for i,b in enumerate(tl['beats']):sheet.paste(picture((b['start']+b['end'])/2,tl,plan).resize((360,640)),((i%4)*360,(i//4)*640))
    sheet.save(out/'contact.jpg');(out/'component-checks.json').write_text(json.dumps({'errors':errors,'measurements':measure,'owner_approved':False,'scope':mechanism},indent=2))
    if errors:raise ValueError('; '.join(errors))
def run(topic,out,mechanism=None):
    require_supported(topic)
    reserved_family=novelty.reserve_new(topic,mechanism)
    out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    cp=Checkpoint(topic,validator=validate,namespace='tested-library-spoken-v1');saved=cp.load()
    def contract_version(plan):return scene_contract_version(plan)
    def save(stage,scene,**fields):return cp.save(stage,scene,contract_version=contract_version(scene),**fields)
    if saved and saved['scene'].get('story_policy')!=STORY_VERSION:saved=save('needs_repair',saved['scene'],errors=['Upgrade the accepted narration to the current causal story policy; preserve the original topic and physical facts'])
    if saved and saved.get('contract_version')!=contract_version(saved['scene']):
        issues=validate(saved['scene'])
        if issues or saved['stage']=='needs_repair':saved=save('needs_repair',saved['scene'],errors=issues or saved.get('errors',[]),repair_kind='validation' if issues else saved.get('repair_kind'))
        else:saved=save('needs_audit',saved['scene'],timeline=saved.get('timeline'))
    reused=bool(saved)
    if saved:
        plan=narration_timing.normalize_cues(saved['scene'])
        if plan!=saved['scene'] and saved['stage']!='needs_repair':
            prior={k:saved[k] for k in ('timeline','render_signature','silent_path','silent_sha256') if k in saved}
            saved=save('needs_audit',plan,**prior)
        print('resume generated director plan without rewriting its narration',flush=True)
    else:
        plan=plan_topic(topic,out,mechanism=mechanism);saved=save('needs_audit',plan)
    if saved['stage']=='needs_repair':
        plan=plan_topic(topic,out,validate(plan) if saved.get('repair_kind')=='validation' else saved['errors'],plan,mechanism=mechanism);saved=save('needs_audit',plan)
    if saved['stage']=='needs_audit':
        for review_attempt in range(3):   # 2026-11-23: one more repair pass before giving up
            errors=critique(plan,out)
            if not errors:
                prior={k:saved[k] for k in ('timeline','render_signature','silent_path','silent_sha256') if k in saved}
                saved=save('checked_scene',plan,**prior);break
            save('needs_repair',plan,errors=errors)
            if review_attempt>=2:raise ValueError('automatic narration repair still contradicts supplied facts')
            plan=plan_topic(topic,out,errors,plan,mechanism=mechanism);saved=save('needs_audit',plan)
    if novelty.identity(topic,plan['mechanism'])!=reserved_family:raise ValueError('Planner changed the reserved visual family; no media allowed')
    if plan['mechanism']!='bascule_bridge':plan['render_policy']=visual_quality.POLICY
    from studio_lib import stories as _stories
    if _stories.current():plan['story']=_stories.current();plan['story_view']=_stories.view_for(plan['mechanism'],plan['story'])
    story_issues=story_errors(plan)
    (out/'story-checks.json').write_text(json.dumps({'policy':STORY_VERSION,'plan_sha256':action_contracts.fingerprint(plan),'errors':story_issues,'scope':'Concrete opening, causal wording, distinct narration and component-owned held-state claims; not an acting-quality score'},indent=2))
    if story_issues:raise ValueError('Causal story contract failed: '+str(story_issues))
    (out/'director-plan.json').write_text(json.dumps(plan,indent=2))
    # Voice measurements drive action durations; no authored narration is read.
    spec={'title':plan['title'],'beats':[dict(b,seconds=3.5) for b in plan['beats']]}
    print('CE_STAGE=voice',flush=True)
    tl=saved.get('timeline')
    from studio_lib.voice_policy import matches as narrator_matches
    if not tl or not narrator_matches(tl) or tl.get('pacing_policy')!='measured-pace-v1' or not all(Path(b['voice']).is_file() for b in tl['beats']):tl=asyncio.run(narrate(spec,out,Path('.ce-cache/studio-voice')))
    require_duration(tl['duration'])
    tl=narration_timing.bind(plan,tl,out)
    (out/'timeline.json').write_text(json.dumps(tl,indent=2))
    verify(plan,tl,out)
    fields={k:saved[k] for k in ('render_signature','silent_path','silent_sha256') if k in saved}
    save('narrated',plan,timeline=tl,**fields)
    if plan['mechanism']!='bascule_bridge':
        from studio_lib import picture_check
        print('CE_STAGE=picture_check',flush=True)
        picture_verdict=picture_check.run(lambda x,z:(lambda r:(r[0],r[1].faces))(component_picture(x,tl,plan,want_scene=True,zoom_scale=z/float(plan.get('picture_zoom',1.0)))),tl,plan,action_contracts.CONTRACTS[plan['mechanism']],out)
    else:picture_verdict=None
    print('CE_STAGE=render',flush=True)
    render_start=time.monotonic();render_hit=False
    root=Path(__file__).resolve().parent
    render_sig=hashlib.sha256(b''.join((root/p).read_bytes() for p in ['director.py','narration_timing.py','mechanisms.py','mesh.py','solar.py','pump.py','wind.py','iris.py','float_valve.py','combination_lock.py','solid_parts.py','camera_direction.py','electric_relay.py','snap_thermostat.py','clothespin.py','zipper.py','stapler.py','optical_fiber.py','pendulum_clock.py','machine_spec.py','kit/recipe.py','kit/register.py','action_contracts.py','visual_quality.py','registry.py'])+b''.join(p.read_bytes() for p in machine_spec.render_files())+json.dumps([tl,plan.get('picture_zoom',1.0)],sort_keys=True).encode()).hexdigest()
    cached=Path(fields.get('silent_path','/nonexistent'))
    if fields.get('render_signature')==render_sig and cached.is_file() and hashlib.sha256(cached.read_bytes()).hexdigest()==fields.get('silent_sha256'):
        shutil.copyfile(cached,out/'silent.mp4');render_hit=True
    else:
        width,height=picture(0,tl,plan).size
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate','30','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p',str(out/'silent.mp4')],stdin=subprocess.PIPE)
        n=math.ceil(tl['duration']*30)
        for i in range(n):
            p.stdin.write(picture(i/30,tl,plan).tobytes())
            if i%150==0:print(f'component render {i}/{n}',flush=True)
        p.stdin.close()
        if p.wait():raise RuntimeError('component render failed')
        cached=Path('.ce-cache/studio-renders')/(cp.key+'.mp4');cached.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(out/'silent.mp4',cached)
    save('rendered',plan,timeline=tl,render_signature=render_sig,silent_path=str(cached),silent_sha256=hashlib.sha256(cached.read_bytes()).hexdigest())
    track=None
    try:
        from studio_lib import foley
        if foley.enabled():track=foley.render(COMPONENTS[plan['mechanism']],tl,plan['mechanism']);print('foley track made',flush=True)
    except Exception as e:print('foley skipped:',str(e)[:200],flush=True)
    assemble(spec,tl,out,foley_track=track)
    novelty.record_created(topic,plan['mechanism'],out/'video.mp4')
    require_video_duration(out/'video.mp4')
    from studio_lib.daily_quality import verify as verify_output
    print('CE_STAGE=audio',flush=True)
    verify_output(plan,tl,out,critique)
    subprocess.run(['ffmpeg','-v','error','-i',str(out/'video.mp4'),'-f','null','-'],check=True)
    result={'picture_check':{'pass':True,'score':picture_verdict['score'],'zoom':picture_verdict['zoom'],'faces':picture_verdict['measures']['faces'],'colours':picture_verdict['measures']['colours'],'vision_score':(picture_verdict.get('vision') or {}).get('score'),'vision_blocks':picture_verdict.get('vision_blocks')} if picture_verdict else None,'status':'component_rendered_editorial_pending','topic':topic,'mechanism':plan['mechanism'],'automatic_narration':True,'tested_geometry_component':True,'manual_generated_plan_edits':False,'arbitrary_topic_support':False,'supported_mechanisms':list(REGISTRY),'owner_approved':False,'director_checkpoint_reused':reused,'render_cache_hit':render_hit,'visual_quality':visual_quality.POLICY if plan['mechanism']!='bascule_bridge' else 'legacy','duration':tl['duration'],'wall_seconds':time.monotonic()-start,'render_seconds':time.monotonic()-render_start}
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--topic',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.topic,a.out)
if __name__=='__main__':main()
