"""Topic -> generated script -> word-timed voice -> Blender -> captioned MP4."""
import argparse,asyncio,hashlib,json,math,re,subprocess,time,wave
from pathlib import Path
import numpy as np
import edge_tts
from studio_lib.director import validate,normalize_narration
from studio_lib.providers import call
from studio_lib.registry import REGISTRY

def groups(words):
    """Never cross narration beats, pauses or punctuation with a caption."""
    result=[];part=[]
    for word in words:
        if part and (word.get('beat')!=part[-1].get('beat') or word['start']-part[-1]['end']>.30):
            result.append(part);part=[]
        part.append(word)
        if len(part)==3 or re.search(r'[.!?,;:]$',word['text']):
            result.append(part);part=[]
    if part:result.append(part)
    return result

HAND_ACTIONS=['machine','input','crank','shaft','generator','induction','load','payoff']
def hand_topic(topic):return bool(re.search(r'\b(hand.?crank|cranked|cranking)\b',topic.lower()))

def contract(topic=''):
    brief=json.loads(json.dumps(REGISTRY['wind_turbine']))
    brief['facts']['rotor']='The hub and all three blades rotate as one rigid assembly. Circular pitch bearings are visible but NO blade pitch adjustment is animated. Do not claim blades twist in these bearings.'
    brief['facts']['induction']='A close view shows rotating red/blue magnets beside stationary copper windings. Changing magnetic flux induces alternating voltage. There is NO coil glow, flash, spark, voltage-spike display or field-line animation. The copper coils do not literally light up.'
    brief['facts']['load']='The demonstration switch closes and the lamp changes from off to a steady bright state. It does not flicker. The circuit markers are illustrative. No grid connection or power-electronics internals are shown.'
    brief['facts']['payoff']='The same turbine keeps turning as the cover returns. The rotor and generator share a shaft, so no speed-increasing gearbox is needed. Energy conversion has losses; do not claim universally higher efficiency or zero loss.'
    for action in ('generator','induction'):
        brief['facts'][action]+=' The external switch is still OPEN: voltage is induced but NO current flows through the lamp or external circuit yet. Never describe producing or flowing current before the load beat.'
    if hand_topic(topic):
        brief={'description':'A simplified hand-cranked permanent-magnet generator with direct shaft, stationary coils and switched demonstration lamp; no turbine or wind.',
          'actions':HAND_ACTIONS,'facts':{
          'machine':'A bench-mounted crank generator is already rotating and a lamp is initially off because its circuit switch is open. Ask why turning a handle can power a lamp.',
          'input':'The colored crank handle moves in a circle. Mechanical work is supplied at this handle; no person or hand is depicted. Do not claim a visible person is turning it.',
          'crank':'The crank arm, axle and magnet disk rotate together. The grip is offset from the shaft to make a lever; no gears, wind or turbine blades are shown.',
          'shaft':'The shaft carries rotation directly into the generator. A stationary main bearing supports it; an illustrative cover lifts away to reveal the internals.',
          'generator':'Red and blue permanent magnets rotate on the shaft while the copper coils stay fixed. The switch is OPEN and the lamp stays off. Induced voltage exists, but no current flows through the external circuit yet.',
          'induction':'Changing magnetic flux through stationary coils induces alternating voltage. The external switch is OPEN; no current flows through the lamp. No coil glow, sparks or voltage spike is depicted.',
          'load':'The demonstration switch closes, completing the circuit. Only now does current flow through the load and the lamp lights steadily. The moving markers are illustrative, not literal particles.',
          'payoff':'The same crank continues turning and the cover returns. Mechanical input becomes electrical energy with losses. This is a simplified generator, not a free-energy machine.'},
          'source':'https://www.eia.gov/energyexplained/electricity/how-electricity-is-generated.php'}
    return brief

def scene_errors(plan):
    if not isinstance(plan,dict):return ['script must be an object']
    errors=[]
    for b in plan.get('beats',[]):
        text=b.get('say','').lower()
        if b.get('action')=='rotor' and re.search(r'\b(twist|twists|twisting|pitching)\b',text):errors.append('No blade pitch adjustment is animated; describe the rigid rotating rotor, not twisting blades.')
        if re.search(r'\b(glow|glows|glowing|flash|flashes|spike|spikes|flicker|flickers)\b',text) and b.get('action')!='load':errors.append('No coil glow, flash or voltage spike is depicted; describe changing magnetic flux and induced voltage.')
        if b.get('action')=='load' and 'flicker' in text:errors.append('Lamp lights steadily, not flickering.')
        if b.get('action') not in ('load','payoff') and re.search(r'\bcurrent\b',text) and not re.search(r'\b(no|not|cannot|without|doesn.t)\b.{0,35}\bcurrent\b|current.{0,25}\b(not|cannot)\b',text):errors.append('Before the switch closes describe induced voltage, not current through the open circuit.')
    if plan.get('beats') and not plan['beats'][0].get('say','').rstrip().endswith('?'):errors.append('Open with a direct visible puzzle question about mechanical input and electricity, not a generic introduction.')
    return errors

def script_errors(plan,topic):
    if not hand_topic(topic):return validate(plan)+scene_errors(plan)
    errors=scene_errors(plan)
    if not isinstance(plan,dict):return errors
    if plan.get('mechanism')!='hand_generator':errors.append('Select hand_generator, not wind_turbine.')
    beats=plan.get('beats',[])
    if [b.get('action') for b in beats]!=HAND_ACTIONS:errors.append('Preserve eight hand-generator actions in contract order.')
    title=plan.get('title','')
    if not 4<=len(title.split())<=8 or not title.startswith(('How ','Why ')):errors.append('Title must start How/Why, 4-8 words.')
    for b in beats:
        text=b.get('say','')
        if not 9<=len(text.split())<=23:errors.append('Each spoken beat needs 9-23 words.')
        if re.search(r'\b(wind|turbine|blades|camera|render|shot)\b',text,re.I):errors.append('Only describe the actual hand-generator scene, no wind, blades or production language.')
    if not 110<=sum(len(b.get('say','').split()) for b in beats)<=145:errors.append('Total speech needs 110-145 words.')
    return errors

def generate(topic,out):
    brief=contract(topic)
    prompt=('Create an original explanation for TOPIC using ONLY this factual/action contract. '
      'Return JSON with mechanism=wind_turbine, title starting How/Why (4-8 words), hook (under 60 characters), '
      'and eight beats in the contract action order, each with action, say (9-23 words), camera=wide|mechanism|follow. '
      'Total 110-145 words. First beat MUST ask a direct puzzle question about wind turning a generator without gears. End it with a question mark. Never start with Look or an introduction. '
      'Use conversational contractions, concrete actions and causal links: what moves, then why it matters. '
      'Build toward the lamp payoff. No production language, filler such as introducing/demonstrating, or invented facts. '
      'Do not copy any existing creator dialogue. The voice remains our own licensed TTS voice. '
      'The existing rotor already turns, the direct-drive shaft has no gearbox, magnets rotate while coils stay still; '
      'a cover lifts during shaft/generator beats. Incoming air trails, visible main bearing, colored magnets, copper coils, '
      'and a switch/lamp illustrate the explanation. Never say rotor stops or switch produces energy. '
      'CONTRACT: '+json.dumps(brief)+' TOPIC: '+json.dumps(topic))
    if hand_topic(topic):
        prompt=('Create an original explanation of this bench-mounted hand-cranked generator. Return JSON with mechanism=hand_generator, title starting How/Why (4-8 words), hook (under 60 characters), and eight beats in EXACT contract action order. Each beat has action, say (9-23 words), camera=wide|mechanism|follow. Total 110-145 words. Open with a direct question about turning a handle into light; end first beat with ?. Use direct conversational phrasing, causal links and concrete visible actions, not production instructions. No visible person is present. No wind, turbine or blades. Switch stays open until load: before then say voltage, never claim current flows. Original words, no copied creator script. CONTRACT: '+json.dumps(brief)+' TOPIC: '+json.dumps(topic))
    errors=[]
    for n in range(3):
        raw=call('Write a clear factual animated explainer. Return JSON only.',prompt+' Corrections: '+json.dumps(errors),max_tokens=2100,temperature=.65)
        (out/f'raw-script-{n}.json').write_text(json.dumps(raw,indent=2))
        plan=normalize_narration(raw);errors=script_errors(plan,topic)
        if not errors:
            check=call('Check narration against the actual cinematic scene contract. Return JSON only.',
                'Return {"errors":[specific contradictions]}. This is a simplified mechanism illustration. Do not invent extra visible actions. CONTRACT: '+json.dumps(brief)+' SCRIPT: '+json.dumps(plan),max_tokens=1100,temperature=.1)
            (out/'narration-critique.json').write_text(json.dumps(check,indent=2));errors=check.get('errors')
            if not isinstance(errors,list) or not all(isinstance(x,str) for x in errors):raise ValueError('Cinematic narration critique unavailable')
            if not errors:return plan
    raise ValueError('Generated narration rejected: '+str(errors))

async def voice(plan,out):
    cache=Path('.ce-cache/cinema-voice');cache.mkdir(parents=True,exist_ok=True)
    beats=[];words=[];t=0;requests=0;hits=0
    for i,b in enumerate(plan['beats']):
        rate='+32%' if i not in (0,5,7) else '+26%'
        key=hashlib.sha256(json.dumps([b['say'],'AndrewNeural',rate,'+2Hz','WordBoundary']).encode()).hexdigest()
        audio=cache/(key+'.mp3');meta=cache/(key+'.jsonl')
        if not (audio.exists() and audio.stat().st_size>1000 and meta.exists() and meta.stat().st_size>20):
            for attempt in range(3):
                requests+=1
                try:
                    await edge_tts.Communicate(b['say'],'en-US-AndrewNeural',rate=rate,pitch='+2Hz',boundary='WordBoundary').save(str(audio),str(meta))
                    break
                except edge_tts.exceptions.NoAudioReceived:
                    if attempt==2:raise
                    await asyncio.sleep(2)
        else:hits+=1
        events=[json.loads(x) for x in meta.read_text().splitlines() if x.strip()]
        events=[x for x in events if x['type']=='WordBoundary']
        if not events:raise ValueError('No real word timestamps; captions must not use guessed timings')
        d=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)]))
        length=max(3.5,d+.22)
        beats.append(dict(b,start=t,end=t+length,voice=str(audio),voice_duration=d,rate=rate))
        words.extend(dict(text=x['text'],start=t+.06+x['offset']/1e7,end=t+.06+(x['offset']+x['duration'])/1e7,beat=i) for x in events)
        t+=length
    if not 30<=t<=65:raise ValueError('Measured narration duration outside 30-65 seconds')
    tl={'beats':beats,'duration':t,'words':words,'requests':requests,'cached_lines':hits}
    (out/'timeline.json').write_text(json.dumps(tl,indent=2));return tl

def ass_time(t):
    n=round(t*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'

def captions(tl,out):
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,43,&H00FFFFFF,&H0000D7FF,&H0018202B,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,35,35,135,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    lines=[]
    parts=groups(tl['words'])
    intervals=[]
    for i,part in enumerate(parts):
        text=' '.join(w['text'].replace('{','').replace('}','').replace('\\','') for w in part)
        start=round(part[0]['start'],2);end=round(part[-1]['end']+.04,2)
        if i+1<len(parts):end=min(end,round(parts[i+1][0]['start'],2)-.01)
        if end<=start:raise ValueError('Caption timing is invalid or overlaps')
        intervals.append({'start':start,'end':end,'text':text,'beat':part[0].get('beat')})
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{text}")
    if any(a['end']>=b['start'] for a,b in zip(intervals,intervals[1:])):raise ValueError('Caption overlap')
    (out/'caption-checks.json').write_text(json.dumps({'errors':[],'intervals':intervals},indent=2))
    p=out/'captions.ass';p.write_text(header+'\n'.join(lines)+'\n');return p

def soundtrack(tl,out):
    sr=24000;n=int(math.ceil(tl['duration']*sr));v=np.zeros(n);fx=np.zeros(n)
    for b in tl['beats']:
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',b['voice'],'-ar',str(sr),'-ac','1','-f','f32le','-'])
        x=np.frombuffer(raw,np.float32);start=int((b['start']+.06)*sr);x=x[:n-start];v[start:start+len(x)]+=x
    # Quiet transition swishes and a mechanical switch click, ducked beneath speech.
    rng=np.random.default_rng(19);events=[]
    for i,b in enumerate(tl['beats'][1:],1):
        start=int(b['start']*sr);length=min(int(.24*sr),n-start);z=np.arange(length)/sr
        fx[start:start+length]+=.025*rng.normal(size=length)*np.sin(np.pi*z/.24)**2
        events.append({'action':b['action'],'time':b['start'],'sound':'camera transition swish'})
        if b['action']=='load':
            length=min(int(.07*sr),n-start);z=np.arange(length)/sr
            fx[start:start+length]+=.07*np.sin(2*np.pi*1300*z)*np.exp(-z*75)
            events.append({'action':'load','time':b['start'],'sound':'switch click'})
    t=np.arange(n)/sr;bed=.009*(np.sin(2*np.pi*110*t)+.25*np.sin(2*np.pi*165*t))
    envelope=np.convolve(abs(v),np.ones(1000)/1000,mode='same');duck=1-.8*np.clip(envelope*10,0,1)
    mix=v*.8+(fx+bed)*duck;mix*=np.minimum(1,t*6)*np.minimum(1,(tl['duration']-t)*4)
    with wave.open(str(out/'mix.wav'),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(mix,-.98,.98)*32700).astype(np.int16).tobytes())
    (out/'sound-events.json').write_text(json.dumps(events,indent=2))

def run(topic,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    # A fresh model-written plan is required for this comparison; no authored script input.
    plan=generate(topic,out);(out/'plan.json').write_text(json.dumps(plan,indent=2))
    tl=asyncio.run(voice(plan,out));captions(tl,out);soundtrack(tl,out)
    script=Path(__file__).with_name('scene.py')
    subprocess.run(['xvfb-run','-a','blender','-b','-t','2','--python',str(script),'--',str(out)],check=True)
    subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(out/'frames/%05d.png'),'-i',str(out/'mix.wav'),'-vf',f"scale=720:1280:flags=lanczos,ass={out/'captions.ass'}",'-c:v','libx264','-preset','fast','-crf','19','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-t',str(tl['duration']),'-movflags','+faststart',str(out/'video.mp4')],check=True)
    subprocess.run(['ffmpeg','-v','error','-i',str(out/'video.mp4'),'-f','null','-'],check=True)
    from studio_lib.cinema.review import review
    review(plan,tl,out)
    result={'topic':topic,'duration':tl['duration'],'wall_seconds':time.monotonic()-started,'manual_script_or_video_edits':False,'render_engine':'Blender Workbench, software graphics on GitHub','scope':plan['mechanism']+'; cinematic comparison','owner_approved':False,'production_deployed':False,'caption_source':'synthesis WordBoundary metadata','reference_audio_measured':False}
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--topic',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.topic,a.out)
if __name__=='__main__':main()
