"""Topic -> generated script -> word-timed voice -> Blender -> captioned MP4."""
import argparse,asyncio,hashlib,json,math,re,subprocess,time,wave
from pathlib import Path
import numpy as np
import edge_tts
from studio_lib.director import validate,normalize_narration,critique
from studio_lib.providers import call
from studio_lib.registry import REGISTRY

def groups(words):
    """Keep actual synthesis word offsets; show at most three words at once."""
    return [words[i:i+3] for i in range(0,len(words),3)]

def generate(topic,out):
    brief=REGISTRY['wind_turbine']
    prompt=('Create an original wind-turbine explanation for TOPIC, using this factual/action contract. '
      'Return JSON with mechanism=wind_turbine, title starting How/Why (4-8 words), hook (under 60 characters), '
      'and eight beats in the contract action order, each with action, say (9-23 words), camera=wide|mechanism|follow. '
      'Total 110-145 words. Start directly with a surprising visible problem or question, never an introduction. '
      'Use conversational contractions, concrete actions and causal links: what moves, then why it matters. '
      'Build toward the lamp payoff. No production language, filler such as introducing/demonstrating, or invented facts. '
      'Do not copy any existing creator dialogue. The voice remains our own licensed TTS voice. '
      'The existing rotor already turns, the direct-drive shaft has no gearbox, magnets rotate while coils stay still; '
      'a cover lifts during shaft/generator beats. Incoming air trails, visible main bearing, colored magnets, copper coils, '
      'and a switch/lamp illustrate the explanation. Never say rotor stops or switch produces energy. '
      'CONTRACT: '+json.dumps(brief)+' TOPIC: '+json.dumps(topic))
    errors=[]
    for n in range(3):
        raw=call('Write a clear factual animated explainer. Return JSON only.',prompt+' Corrections: '+json.dumps(errors),max_tokens=2100,temperature=.65)
        (out/f'raw-script-{n}.json').write_text(json.dumps(raw,indent=2))
        plan=normalize_narration(raw);errors=validate(plan)
        if not errors:
            errors=critique(plan,out)
            if not errors:return plan
    raise ValueError('Generated narration rejected: '+str(errors))

async def voice(plan,out):
    cache=Path('.ce-cache/cinema-voice');cache.mkdir(parents=True,exist_ok=True)
    beats=[];words=[];t=0;requests=0;hits=0
    for i,b in enumerate(plan['beats']):
        rate='+24%' if i not in (0,5,7) else '+18%'
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
        words.extend(dict(text=x['text'],start=t+.06+x['offset']/1e7,end=t+.06+(x['offset']+x['duration'])/1e7) for x in events)
        t+=length
    if not 30<=t<=65:raise ValueError('Measured narration duration outside 30-65 seconds')
    tl={'beats':beats,'duration':t,'words':words,'requests':requests,'cached_lines':hits}
    (out/'timeline.json').write_text(json.dumps(tl,indent=2));return tl

def ass_time(t):
    n=round(t*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'

def captions(tl,out):
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,43,&H00FFFFFF,&H0000D7FF,&H0018202B,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,35,35,135,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    lines=[]
    for part in groups(tl['words']):
        text=' '.join(w['text'].replace('{','').replace('}','').replace('\\','') for w in part)
        lines.append(f"Dialogue: 0,{ass_time(part[0]['start'])},{ass_time(part[-1]['end']+.07)},Default,,0,0,0,,{text}")
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
    result={'topic':topic,'duration':tl['duration'],'wall_seconds':time.monotonic()-started,'manual_script_or_video_edits':False,'render_engine':'Blender Workbench, software graphics on GitHub','scope':'wind turbine only; cinematic comparison','owner_approved':False,'production_deployed':False,'caption_source':'synthesis WordBoundary metadata','reference_audio_measured':False}
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--topic',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.topic,a.out)
if __name__=='__main__':main()
