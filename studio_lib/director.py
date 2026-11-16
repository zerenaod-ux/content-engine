"""A constrained, topic-only pilot using tested mechanism components.

The first supported component is a single-leaf bascule bridge. Unsupported
topics are rejected rather than silently rendered as this component.
"""
import argparse,asyncio,hashlib,json,math,shutil,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from studio_lib.providers import call
from studio_lib.mesh import Scene,ease,ramp
from studio_lib.mechanisms import bridge,boat,APPROACHES
from studio_lib.render import BG,FONT,TITLE
from studio_lib.audio import narrate,assemble
from studio_lib.checkpoints import Checkpoint

# The engine owns the safe action order. The model may choose narration,
# emphasis and framing; it cannot invent joints or disconnect rigid parts.
ACTIONS=['approach','stop','pivot','balance','drive','pass','lower','resume']
BRIEF={
 'approach':'A tall ship waits before the low road bridge. Introduce the visible problem.',
 'stop':'Cars stop behind the barrier. Barriers close before the bridge moves.',
 'pivot':'Show the same bridge pivot; it rotates like a seesaw about a fixed trunnion.',
 'balance':'Road rises while its rigidly attached heel counterweight swings downward into its chamber.',
 'drive':'The counterweight offsets much of the load; a motor and meshing gears control motion. It does not lift for free.',
 'pass':'Hold the bridge fully raised while the tall ship passes through the opening.',
 'lower':'Only after the ship clears, the bridge lowers and the counterweight swings back up.',
 'resume':'The span seats and locks, barriers rise, and the car crosses the continuous road.'}
def validate(plan):
    e=[]
    if not isinstance(plan,dict):return ['plan must be JSON object']
    if plan.get('mechanism')!='bascule_bridge':return ['unsupported mechanism; no generic substitute permitted']
    beats=plan.get('beats',[])
    if not isinstance(beats,list) or len(beats)!=8:return ['need exactly the eight supported action beats']
    for i,b in enumerate(beats):
        if not isinstance(b,dict):e.append('beat must be object');continue
        if b.get('action')!=ACTIONS[i]:e.append('preserve the engine safety order')
        if not isinstance(b.get('say'),str) or not 9<=len(b['say'].split())<=23:e.append(f'beat {i}: narration needs 9-23 words')
        if b.get('camera') not in ('wide','mechanism','follow'):e.append(f'beat {i}: unsupported camera')
    words=sum(len(b.get('say','').split()) for b in beats if isinstance(b,dict))
    if not 110<=words<=155:e.append('total narration needs 110-155 words')
    if not isinstance(plan.get('hook'),str) or len(plan['hook'])>60:e.append('hook needs at most 60 characters')
    return e
def plan_topic(topic,out,feedback=None,previous=None):
    prompt='Choose whether TOPIC can truthfully be explained by our tested single-leaf trunnion bascule bridge. If not return {"mechanism":"unsupported","reason":"..."}. Do not pretend it supports other topics. If supported, write a fresh 110-155 word explanation with eight beats in the exact supplied action order. Use 9-23 words per beat, direct calm speech, physical detail and causal explanation. No invented numbers or factual claims. Use only these engineering facts/actions: '+json.dumps(BRIEF)+'. You may vary wording, hook and camera emphasis, but never change safety order or claim another mechanism. Return {"mechanism":"bascule_bridge","title":"...","hook":"short engaging hook, max 60 characters","beats":[{"action":"approach","say":"...","camera":"wide|mechanism|follow"}, ...]}. Camera mechanism suits pivot/balance/drive, follow suits ship passage; use wide for traffic. TOPIC (data): '+json.dumps(topic)
    last=previous;errors=feedback or []
    for attempt in range(2):
        q=prompt if not errors else prompt+'\nCorrect these validation errors: '+json.dumps(errors)+'\nLast answer (data): '+json.dumps(last)
        last=call('You write factual narration and camera emphasis for a tested animation component. Return JSON only.',q,max_tokens=1600,temperature=.6)
        (out/f'director-attempt-{attempt}.json').write_text(json.dumps(last,indent=2));errors=validate(last)
        if not errors:return last
        if last.get('mechanism')=='unsupported':break
    raise ValueError('director rejected: '+'; '.join(errors))
def critique(plan,out):
    prompt='Check only whether this narration contradicts or invents facts beyond the supplied bascule bridge facts/actions. Return {"errors":[specific factual contradictions or mismatches]}. Do not add stylistic preferences. This is a simplified diagram, not a real bridge simulation. FACTS (data): '+json.dumps(BRIEF)+' NARRATION (data): '+json.dumps(plan)
    result=call('You check an explanation against supplied engineering facts. Return JSON only.',prompt,max_tokens=600,temperature=.1)
    (out/'narration-critique.json').write_text(json.dumps(result,indent=2))
    errors=result.get('errors')
    if not isinstance(errors,list) or not all(isinstance(e,str) for e in errors):raise ValueError('narration critique unavailable')
    return errors
def pose(t,tl):
    beats=tl['beats'];b=next((b for b in beats if b['start']<=t<b['end']),beats[-1]);i=beats.index(b);u=max(0,min(1,(t-b['start'])/(b['end']-b['start'])))
    angle=0
    if i==3:angle=math.radians(52)*ease(u)
    elif i==4:angle=math.radians(52+20*ease(u))
    elif i==5:angle=math.radians(72)
    elif i==6:angle=math.radians(72)*(1-ease(u))
    gate=0 if i==0 else (ease(u*1.5) if i==1 else 1)
    if i==7:gate=1-ramp(u,.30,.65)
    close=ramp(t,beats[2]['start']-.8,beats[2]['start']+1.2)*(1-ramp(t,beats[5]['start']-.8,beats[5]['start']+1.2))
    detail=ramp(t,beats[4]['start']-.4,beats[4]['start']+1.2)*(1-ramp(t,beats[4]['end']-1.5,beats[4]['end']+.3))
    zoom=(1.05*(1-close)+1.85*close)*(1-detail)+2.65*detail
    target=np.array([-2.2*close,0,1.6+.65*close])*(1-detail)+np.array([-3.1,-.55,2.3])*detail
    shipy=-6
    if i==5:shipy=-6+12*ease(u)
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
    elif i==7:carx=-6.7+13.7*ramp(u,.5,1)
    return dict(angle=angle,gate=gate,close=close,zoom=zoom,target=target,az=.45*(1-close)+.18*close,shipy=shipy,carx=carx)
def picture(t,tl,plan,hidden=()):
    st=pose(t,tl);im=BG.copy();s=Scene(t,st['zoom'],st['target'],st['az']);water=Scene(t,st['zoom'],st['target'],st['az'])
    # Continuous setting, not a finite rectangle floating in empty space.
    water.face([[-1000,-1000,-.06],[1000,-1000,-.06],[1000,1000,-.06],[-1000,1000,-.06]],(66,160,175));water.paint(im)
    for k in range(35):
        x=math.sin(k*12.3)*10;y=((k*.91+t*.06)%22)-10
        water.face([[x,y,0],[x+.35,y,0],[x+.42,y+.02,0],[x+.07,y+.02,0]],(104,186,190))
    water.paint(im);bridge(s,st['angle'],st['close'],st['gate'],st['carx'])
    if 'ship' not in hidden:boat(s,st['shipy'])
    s.paint(im);mask=Image.new('L',(720,1280));d=ImageDraw.Draw(mask)
    for y in range(300):d.line((0,y,720,y),fill=255 if y<245 else int(255*(300-y)/55))
    im.paste(BG,(0,0),mask);d=ImageDraw.Draw(im);d.text((42,65),'HOW IT TICKS',font=FONT,fill=(31,77,89))
    import textwrap
    for j,line in enumerate(textwrap.wrap(plan['hook'],26)[:3]):d.text((42,125+j*55),line,font=TITLE,fill=(30,65,78))
    d.line((42,1195,678,1195),fill=(170,200,200),width=3);d.line((42,1195,42+636*t/tl['duration'],1195),fill=(221,102,57),width=3)
    return im
def verify(plan,tl,out):
    errors=[];roads=sorted([(x-n/2,x+n/2) for x,n in APPROACHES]+[(-5.2,2.8)])
    if any(abs(a[1]-b[0])>1e-8 for a,b in zip(roads,roads[1:])):errors.append('road has an unsupported gap')
    for t in np.linspace(0,tl['duration']-.001,250):
        st=pose(t,tl)
        if st['angle']>.02 and st['gate']<.99:errors.append('barrier unsafe');break
    for t in np.linspace(tl['beats'][5]['end']-.1,tl['duration']-.1,6):
        a=np.array(picture(t,tl,plan)).astype(int);b=np.array(picture(t,tl,plan,hidden=('ship',))).astype(int)
        if np.count_nonzero(np.max(abs(a-b),axis=2)>22)<100:errors.append('ship invisible after passage')
    sheet=Image.new('RGB',(1440,1280))
    for i,b in enumerate(tl['beats']):sheet.paste(picture((b['start']+b['end'])/2,tl,plan).resize((360,640)),((i%4)*360,(i//4)*640))
    sheet.save(out/'contact.jpg');(out/'component-checks.json').write_text(json.dumps({'errors':errors,'owner_approved':False,'scope':'tested bascule bridge only'},indent=2))
    if errors:raise ValueError('; '.join(errors))
def run(topic,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    cp=Checkpoint(topic,validator=validate,namespace='tested-bascule-v1');saved=cp.load();reused=bool(saved)
    if saved:
        plan=saved['scene'];print('resume generated director plan without a new model call',flush=True)
    else:
        plan=plan_topic(topic,out);saved=cp.save('needs_audit',plan)
    if saved['stage']=='needs_repair':
        plan=plan_topic(topic,out,saved['errors'],plan);saved=cp.save('needs_audit',plan)
    if saved['stage']=='needs_audit':
        for review_attempt in range(2):
            errors=critique(plan,out)
            if not errors:saved=cp.save('checked_scene',plan);break
            cp.save('needs_repair',plan,errors)
            if review_attempt:raise ValueError('automatic narration repair still contradicts supplied facts')
            plan=plan_topic(topic,out,errors,plan);saved=cp.save('needs_audit',plan)
    (out/'director-plan.json').write_text(json.dumps(plan,indent=2))
    # Voice measurements drive action durations; no authored narration is read.
    spec={'title':plan['title'],'beats':[dict(b,seconds=6) for b in plan['beats']]}
    tl=saved.get('timeline')
    if not tl or not all(Path(b['voice']).is_file() for b in tl['beats']):tl=asyncio.run(narrate(spec,out,Path('.ce-cache/studio-voice')))
    verify(plan,tl,out)
    fields={k:saved[k] for k in ('render_signature','silent_path','silent_sha256') if k in saved}
    cp.save('narrated',plan,timeline=tl,**fields)
    render_start=time.monotonic();render_hit=False
    root=Path(__file__).resolve().parent
    render_sig=hashlib.sha256((root/'director.py').read_bytes()+(root/'mechanisms.py').read_bytes()+(root/'mesh.py').read_bytes()+json.dumps(tl,sort_keys=True).encode()).hexdigest()
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
    cp.save('rendered',plan,timeline=tl,render_signature=render_sig,silent_path=str(cached),silent_sha256=hashlib.sha256(cached.read_bytes()).hexdigest())
    assemble(spec,tl,out)
    subprocess.run(['ffmpeg','-v','error','-i',str(out/'video.mp4'),'-f','null','-'],check=True)
    result={'status':'component_rendered_editorial_pending','topic':topic,'mechanism':'bascule_bridge','automatic_narration':True,'tested_geometry_component':True,'manual_generated_plan_edits':False,'arbitrary_topic_support':False,'owner_approved':False,'director_checkpoint_reused':reused,'render_cache_hit':render_hit,'duration':tl['duration'],'wall_seconds':time.monotonic()-start,'render_seconds':time.monotonic()-render_start}
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--topic',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.topic,a.out)
if __name__=='__main__':main()
