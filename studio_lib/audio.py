"""Measured cached narration and a quiet generated soundtrack, free services only."""
import asyncio,hashlib,json,subprocess,time,wave
from pathlib import Path
import numpy as np
import edge_tts
SR=24000
async def narrate(spec,out,cache):
    out=Path(out);cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);t=0;beats=[];calls=0;hits=0
    for b in spec['beats']:
        key=hashlib.sha256(json.dumps([b['say'],'en-US-AndrewNeural','+30%','+8Hz']).encode()).hexdigest();f=cache/(key+'.mp3')
        if f.exists() and f.stat().st_size>1000:hits+=1
        else:
            for attempt in range(3):
                calls+=1
                try:
                    await edge_tts.Communicate(b['say'],'en-US-AndrewNeural',rate='+30%',pitch='+8Hz').save(str(f));break
                except edge_tts.exceptions.NoAudioReceived:
                    if attempt==2:raise
                    await asyncio.sleep(2)
        dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(f)]))
        d=max(b['seconds'],dur+.35);beats.append(dict(b,start=t,end=t+d,voice=str(f),voice_duration=dur));t+=d
    if t>65.1:raise ValueError('measured narration exceeds 65 seconds; shorten sentences or simplify the story')
    tl={'beats':beats,'duration':t,'narration_requests':calls,'cached_lines':hits}
    (out/'timeline.json').write_text(json.dumps(tl,indent=2));return tl
def assemble(spec,timeline,out):
    out=Path(out);T=timeline['duration'];n=int(T*SR);voice=np.zeros(n)
    for b in timeline['beats']:
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',b['voice'],'-ar',str(SR),'-ac','1','-f','f32le','-']);x=np.frombuffer(raw,np.float32).astype(float)
        pos=int((b['start']+.08)*SR);x=x[:n-pos];voice[pos:pos+len(x)]+=x
    voice*=.78/(abs(voice).max()+1e-9);t=np.arange(n)/SR
    bed=np.zeros(n)
    for k in range(int(T*1.8)):
        pos=int(k/1.8*SR);d=min(int(.45*SR),n-pos);tt=np.arange(d)/SR;freq=[110,130.81,164.81,146.83][(k//4)%4]
        bed[pos:pos+d]+=.025*(np.sin(2*np.pi*freq*tt)+.25*np.sin(2*np.pi*freq*2*tt))*np.exp(-tt*8)*np.minimum(1,tt*80)
    win=1200;env=np.array([abs(voice[i:i+win]).mean() for i in range(0,n,win)]);env=np.interp(np.arange(n),np.arange(len(env))*win,env)
    mixed=voice+bed*(1-.7*np.clip(env*10,0,1));mixed*=np.minimum(1,t*4)*np.minimum(1,(T-t)*3)
    with wave.open(str(out/'mix.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(mixed,-.98,.98)*32700).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'silent.mp4'),'-i',str(out/'mix.wav'),'-c:v','copy','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-t',str(T),'-movflags','+faststart',str(out/'video.mp4')],check=True)
