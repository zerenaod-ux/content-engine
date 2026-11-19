from studio_lib.duration import require_duration,require_video_duration
"""Topic-selected tested mechanisms, with no generated geometry or scene edits.

Supported: bascule bridge, photovoltaic cell and single-acting piston pump.
Unsupported topics are rejected instead of receiving an unrelated component.
"""
import argparse,asyncio,hashlib,json,math,re,shutil,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from studio_lib.providers import call
from studio_lib import narration_timing
from studio_lib.storytelling import WRITING_RULES as STORY_RULES
from studio_lib.mesh import Scene,ease,ramp
from studio_lib.mechanisms import bridge,boat,APPROACHES
from studio_lib.render import BG,FONT,TITLE
from studio_lib.audio import narrate,assemble
from studio_lib.checkpoints import Checkpoint
from studio_lib.registry import REGISTRY
from studio_lib import solar,pump,wind
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
    actions=REGISTRY[mechanism]['actions']
    beats=plan.get('beats',[])
    if not isinstance(beats,list) or len(beats)!=8:return ['need exactly the eight supported action beats']
    for i,b in enumerate(beats):
        if not isinstance(b,dict):e.append('beat must be object');continue
        if b.get('action')!=actions[i]:e.append('preserve the engine safety order')
        if not isinstance(b.get('say'),str) or not 9<=len(b['say'].split())<=23:e.append(f'beat {i}: narration needs 9-23 words')
        text=b.get('say','').lower() if isinstance(b.get('say'),str) else ''
        if re.search(r'\b(camera|render|renderer|shot|storyboard|animation engine|close.up|view shifts)\b',text):e.append(f'beat {i}: speak about the mechanism, never production or camera instructions')
        if mechanism=='bascule_bridge' and i==2 and re.search(r'\b(begins?|starts?|starting|beginning)\b',text):e.append('pivot beat is a static close-up; opening does not begin until the balance beat')
        if mechanism=='bascule_bridge' and i==6 and re.search(r'\b(return|returns|returning|releases?|releasing|generates?)\s+energy\b',text):e.append(f'beat {i}: the rising counterweight gains gravitational potential energy while the leaf loses it; do not claim the rising weight releases energy')
        if mechanism=='bascule_bridge' and re.search(r'\bcars\b',text):e.append(f'beat {i}: this component depicts one car; use car or traffic')
        if mechanism=='photovoltaic_cell' and re.search(r'(without.{0,24}wir|no wir|wir.{0,24}(absent|hidden|not shown))',text):e.append(f'beat {i}: wires are visible in this component; do not claim they are absent')
        if mechanism=='piston_pump' and re.search(r'(each|every|both) stroke.{0,30}(deliver|push|discharg)',text):e.append(f'beat {i}: only the delivery stroke discharges water; intake does not deliver to the receiver')
        if mechanism=='piston_pump' and re.search(r'\b(upward|upwards|downward|downwards|vertically)\b',text):e.append(f'beat {i}: this pump piston moves horizontally; do not describe vertical travel')
        if mechanism=='piston_pump' and re.search(r'\b(steady|constant|continuous|uninterrupted|smooth)\s+(water|flow|discharge|stream)|\b(water|flow|discharge|stream)\s+(is|stays|remains)\s+(steady|constant|continuous|uninterrupted)',text) and not re.search(r'\b(not|never|no)\b.{0,18}\b(steady|constant|continuous|uninterrupted|smooth)\b',text):e.append(f'beat {i}: single-acting discharge is pulsating; no smoothing reservoir is shown')
        if re.search(r'\b([a-z]+)\s+\1\b',text) or re.search(r'permanent[\s\-\u2011]+magnet[\s\-\u2011]+magnets',text):e.append(f'beat {i}: remove accidentally repeated words or redundant magnet wording')
        if re.search(r'\b(today clearly|safely now|firmly still|smoothly efficiently|smoothly for all|smoothly again|significantly during operation)\b',text):e.append(f'beat {i}: replace filler added to reach a word quota with a concrete explanatory fact')
        if b.get('camera') not in ('wide','mechanism','follow'):e.append(f'beat {i}: unsupported camera')
    words=sum(len(b['say'].split()) for b in beats if isinstance(b,dict) and isinstance(b.get('say'),str))
    if not 120<=words<=176:e.append('total narration needs 120-176 words')
    if not isinstance(plan.get('hook'),str) or len(plan['hook'])>60:e.append('hook needs at most 60 characters')
    if plan.get('motion_policy')==narration_timing.VERSION:
        e.extend(narration_timing.cue_errors(plan))
        if not isinstance(plan.get('hook'),str) or not 2<=len(plan['hook'].split())<=7 or len(plan['hook'])>40:e.append('hook needs 2-7 simple words and at most 40 characters')
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

def plan_topic(topic,out,feedback=None,previous=None):
    catalog={k:{'description':v['description'],'actions':v['actions'],'facts':v['facts']} for k,v in REGISTRY.items()}
    prompt='Select exactly one supported mechanism that truthfully matches TOPIC. If none fits return {"mechanism":"unsupported","reason":"..."}; never substitute a bridge for solar power or invent another mechanism. For a supported topic write fresh 120-176 word narration with eight beats in the exact selected action order. Each beat has 9-23 words. Title starts with How or Why and contains 4-8 words. Natural spoken sentences, physical detail, causal explanation and a concrete engaging hook. Prefer 125-155 words; never append adverbs or redundant phrases merely to meet a quota. Avoid narration about views or production. Actual measured 40-70-second duration is mandatory. Each beat names the specific inner part the viewer is looking at (from the facts for that beat) and says what it physically does, so viewers know exactly what is happening inside. Describe only what that action contract shows. Never mention camera, close-ups, shots, rendering, storyboard or production in say. Do not invent facts or numerical claims. In the bridge pivot beat the road is STATIC; explain the shaft and hinge rather than announcing motion or a view. The bridge depicts ONE car. Solar and pump internals are simplified cutaways: say so naturally once. Solar depicts a DC lamp load, not gears or AC inverter internals. Preserve physical action order; vary wording, hook and bounded camera preferences. Return {"mechanism":"selected registry id","title":"...","hook":"short engaging hook max 60 characters","beats":[{"action":"first selected action","say":"...","camera":"wide|mechanism|follow"}, ...]}. SUPPORTED COMPONENTS AND FACTS (data): '+json.dumps(catalog)+' TOPIC (data): '+json.dumps(topic)
    prompt+='\n'+STORY_RULES+'\n'+narration_timing.writing_rules()+' Hook: 2-7 everyday words, at most 40 characters; no technical subtitle.'
    last=previous;errors=feedback or []
    for attempt in range(2):
        q=prompt if not errors else prompt+'\nCorrect these validation errors: '+json.dumps(errors)+'\nLast answer (data): '+json.dumps(last)
        repaired=repair_short_sections(last,errors) if isinstance(last,dict) and errors else None
        last=repaired if repaired is not None else call('You write factual narration and camera emphasis for tested animation components. Return JSON only.',q,max_tokens=2000,temperature=.6)
        if isinstance(last,dict):last['motion_policy']=narration_timing.VERSION
        # Keep the raw response; apply a narrow automatic copy-edit before validation.
        # This changes no factual content, geometry, timing, action order or camera.
        (out/f'director-attempt-{attempt}.json').write_text(json.dumps(last,indent=2))
        last=normalize_narration(last)
        (out/f'director-normalized-{attempt}.json').write_text(json.dumps(last,indent=2));errors=validate(last)
        if not errors:return last
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
    if i==7:gate=1-ramp(action_u,.30,.65)
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
    elif i==7:carx=-6.7+13.7*ramp(action_u,.5,1)
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
    mechanism=plan['mechanism'];module={'photovoltaic_cell':solar,'piston_pump':pump,'wind_turbine':wind}[mechanism]
    beats=tl['beats'];i=min(7,next((i for i,b in enumerate(beats) if t<b['end']),7));b=beats[i];u=(t-b['start'])/(b['end']-b['start'])
    previous=beats[max(0,i-1)].get('camera','wide');mode=b.get('camera','wide')
    pref={'wide':0.0,'mechanism':1.0,'follow':.45}
    close=pref[previous]+(pref[mode]-pref[previous])*ramp(u,0,.3)
    if hasattr(module,'shot'):
        # CLOSE_SHOTS: glide from the previous line's part to this line's part over ~1.4 s, then a slow push-in.
        a0,a1=module.shot(max(0,i-1)),module.shot(i);m=ease(min(1,(t-b['start'])/1.4)) if i>0 else 1
        target=np.array(a0[0])*(1-m)+np.array(a1[0])*m
        zoom=math.exp(math.log(a0[1])*(1-m)+math.log(a1[1])*m)*(1+.07*u)
        az=a0[2]*(1-m)+a1[2]*m+.03*math.sin(t*.25)
    elif mechanism=='photovoltaic_cell':target=np.array([-.1,0,2.15]);zoom=1.55+.55*close;az=.30+.08*math.sin(t*.035)
    elif mechanism=='piston_pump':target=np.array([-.4,0,2.3]);zoom=.94+.46*close;az=.34+.06*math.sin(t*.04)
    else:
        detail=ramp(t,beats[3]['start']-.8,beats[3]['start']+1.2)*(1-ramp(t,beats[6]['start']-.8,beats[6]['start']+1.2))
        target=np.array([.5*(1-detail)-.65*detail,0,3.8+1.3*detail]);zoom=1.25+1.0*detail+.08*close;az=.35+.10*math.sin(t*.04)
    return zoom,target,az

def component_picture(t,tl,plan,hidden=()):
    mechanism=plan['mechanism'];module={'photovoltaic_cell':solar,'piston_pump':pump,'wind_turbine':wind}[mechanism]
    zoom,target,az=component_camera(t,tl,plan)
    im=BG.copy();ground=Scene(t,zoom,target,az);s=Scene(t,zoom,target,az)
    ground.face([[-1000,-1000,-.1],[1000,-1000,-.1],[1000,1000,-.1],[-1000,1000,-.1]],(218,229,224));ground.paint(im)
    module.draw(s,t,tl,hidden);s.paint(im)
    mask=Image.new('L',(720,1280));md=ImageDraw.Draw(mask)
    for y in range(300):md.line((0,y,720,y),fill=255 if y<245 else int(255*(300-y)/55))
    im.paste(BG,(0,0),mask);d=ImageDraw.Draw(im);d.text((42,65),'HOW IT TICKS',font=FONT,fill=(31,77,89))
    import textwrap
    for j,line in enumerate(textwrap.wrap(plan['hook'],26)[:3]):d.text((42,125+j*55),line,font=TITLE,fill=(30,65,78))
    beat=min(7,next((j for j,b in enumerate(tl['beats']) if t<b['end']),7))
    label=None
    if mechanism=='wind_turbine' and beat==5:label='Magnetic field · illustration'
    if mechanism=='photovoltaic_cell' and 2<=beat<=6:label='Charge carriers · illustration'
    if label:d.text((42,1120),label,font=FONT,fill=(31,77,89))
    d.line((42,1195,678,1195),fill=(170,200,200),width=3);d.line((42,1195,42+636*t/tl['duration'],1195),fill=(221,102,57),width=3)
    return im
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
    module={'photovoltaic_cell':solar,'piston_pump':pump,'wind_turbine':wind}[plan['mechanism']]
    samples=[]
    for i,fraction in [(0,.05),(0,.5),(0,.95),(7,.95)]:
        beat=tl['beats'][i];t=beat['start']+(beat['end']-beat['start'])*fraction
        zoom,target,az=component_camera(t,tl,plan);scene=Scene(t,zoom,target,az)
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
    if mechanism=='piston_pump':
        for t in np.linspace(tl['beats'][2]['start'],tl['beats'][3]['end']-.001,25):
            p=pump.phase(t,tl)
            if not p['intake'] or p['delivery']:errors.append('incorrect inlet/outlet state during intake')
        for t in np.linspace(tl['beats'][4]['start']+.001,tl['beats'][5]['end']-.001,25):
            p=pump.phase(t,tl)
            if not p['delivery'] or p['intake']:errors.append('incorrect inlet/outlet state during delivery')
        evidence=[(3,'piston'),(5,'flow')]
    elif mechanism=='photovoltaic_cell':
        if any(solar.pose((b['start']+b['end'])/2,tl)['powered'] for b in tl['beats'][:5]):errors.append('load lit before closed-circuit beat')
        evidence=[(1,'light'),(3,'carriers'),(5,'current')]
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
def run(topic,out):
    require_supported(topic)
    out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    cp=Checkpoint(topic,validator=validate,namespace='tested-library-spoken-v1');saved=cp.load()
    def contract_version(plan):return hashlib.sha256((narration_timing.VERSION+json.dumps(REGISTRY[plan['mechanism']],sort_keys=True)).encode()).hexdigest()
    def save(stage,scene,**fields):return cp.save(stage,scene,contract_version=contract_version(scene),**fields)
    if saved and saved.get('contract_version')!=contract_version(saved['scene']):saved=save('needs_audit',saved['scene'],timeline=saved.get('timeline'))
    reused=bool(saved)
    if saved:
        plan=saved['scene'];print('resume generated director plan without a new model call',flush=True)
    else:
        plan=plan_topic(topic,out);saved=save('needs_audit',plan)
    if saved['stage']=='needs_repair':
        plan=plan_topic(topic,out,saved['errors'],plan);saved=save('needs_audit',plan)
    if saved['stage']=='needs_audit':
        for review_attempt in range(2):
            errors=critique(plan,out)
            if not errors:
                prior={k:saved[k] for k in ('timeline','render_signature','silent_path','silent_sha256') if k in saved}
                saved=save('checked_scene',plan,**prior);break
            save('needs_repair',plan,errors=errors)
            if review_attempt:raise ValueError('automatic narration repair still contradicts supplied facts')
            plan=plan_topic(topic,out,errors,plan);saved=save('needs_audit',plan)
    (out/'director-plan.json').write_text(json.dumps(plan,indent=2))
    # Voice measurements drive action durations; no authored narration is read.
    spec={'title':plan['title'],'beats':[dict(b,seconds=6) for b in plan['beats']]}
    print('CE_STAGE=voice',flush=True)
    tl=saved.get('timeline')
    if not tl or not all(Path(b['voice']).is_file() for b in tl['beats']):tl=asyncio.run(narrate(spec,out,Path('.ce-cache/studio-voice')))
    require_duration(tl['duration'])
    tl=narration_timing.bind(plan,tl,out)
    (out/'timeline.json').write_text(json.dumps(tl,indent=2))
    verify(plan,tl,out)
    fields={k:saved[k] for k in ('render_signature','silent_path','silent_sha256') if k in saved}
    save('narrated',plan,timeline=tl,**fields)
    print('CE_STAGE=render',flush=True)
    render_start=time.monotonic();render_hit=False
    root=Path(__file__).resolve().parent
    render_sig=hashlib.sha256(b''.join((root/p).read_bytes() for p in ['director.py','mechanisms.py','mesh.py','solar.py','pump.py','wind.py','registry.py'])+json.dumps(tl,sort_keys=True).encode()).hexdigest()
    cached=Path(fields.get('silent_path','/nonexistent'))
    if fields.get('render_signature')==render_sig and cached.is_file() and hashlib.sha256(cached.read_bytes()).hexdigest()==fields.get('silent_sha256'):
        shutil.copyfile(cached,out/'silent.mp4');render_hit=True
    else:
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x1280','-framerate','30','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(out/'silent.mp4')],stdin=subprocess.PIPE)
        n=math.ceil(tl['duration']*30)
        for i in range(n):
            p.stdin.write(picture(i/30,tl,plan).tobytes())
            if i%150==0:print(f'component render {i}/{n}',flush=True)
        p.stdin.close()
        if p.wait():raise RuntimeError('component render failed')
        cached=Path('.ce-cache/studio-renders')/(cp.key+'.mp4');cached.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(out/'silent.mp4',cached)
    save('rendered',plan,timeline=tl,render_signature=render_sig,silent_path=str(cached),silent_sha256=hashlib.sha256(cached.read_bytes()).hexdigest())
    assemble(spec,tl,out)
    require_video_duration(out/'video.mp4')
    from studio_lib.daily_quality import verify as verify_output
    print('CE_STAGE=audio',flush=True)
    verify_output(plan,tl,out,critique)
    subprocess.run(['ffmpeg','-v','error','-i',str(out/'video.mp4'),'-f','null','-'],check=True)
    result={'status':'component_rendered_editorial_pending','topic':topic,'mechanism':plan['mechanism'],'automatic_narration':True,'tested_geometry_component':True,'manual_generated_plan_edits':False,'arbitrary_topic_support':False,'supported_mechanisms':list(REGISTRY),'owner_approved':False,'director_checkpoint_reused':reused,'render_cache_hit':render_hit,'duration':tl['duration'],'wall_seconds':time.monotonic()-start,'render_seconds':time.monotonic()-render_start}
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--topic',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.topic,a.out)
if __name__=='__main__':main()
