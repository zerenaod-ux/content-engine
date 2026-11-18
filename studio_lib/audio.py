"""Measured cached narration and a quiet generated soundtrack, free services only."""
import asyncio,hashlib,json,subprocess,time,wave,sys,os
from pathlib import Path
import numpy as np
import edge_tts
from studio_lib.service_queue import lease
from studio_lib.duration import require_duration
from studio_lib.audio_mastering import mastering_args
from studio_lib.cinema.speech import delivery,VOICE
SR=24000
async def _primary_narrate(spec,out,cache):
    out=Path(out);cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);t=0;beats=[];calls=0;hits=0
    for index,b in enumerate(spec['beats']):
        profile=delivery(b.get('action','explain'),index,len(spec['beats']))
        key=hashlib.sha256(json.dumps([b['say'],VOICE,profile],sort_keys=True).encode()).hexdigest();f=cache/(key+'.mp3')
        legacy=cache/(hashlib.sha256(json.dumps([b['say'],VOICE,'+30%','+8Hz']).encode()).hexdigest()+'.mp3')
        if legacy.exists() and legacy.stat().st_size>1000:f=legacy
        if f.exists() and f.stat().st_size>1000:hits+=1
        else:
            for attempt in range(2):
                calls+=1
                try:
                    with lease('voice'):
                        await asyncio.wait_for(edge_tts.Communicate(b['say'],VOICE,rate=profile['rate'],pitch=profile['pitch'],volume=profile['volume']).save(str(f)),timeout=75)
                    if f.stat().st_size<=1000:raise edge_tts.exceptions.NoAudioReceived('Incomplete audio')
                    break
                except (edge_tts.exceptions.NoAudioReceived,asyncio.TimeoutError):
                    f.unlink(missing_ok=True)
                    if attempt==1:raise
                    await asyncio.sleep(10*2**attempt)
        dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(f)]))
        d=max(b['seconds'],dur+.35);beats.append(dict(b,start=t,end=t+d,voice=str(f),voice_duration=dur));t+=d
    require_duration(t)
    tl={'beats':beats,'duration':t,'narration_requests':calls,'cached_lines':hits}
    (out/'timeline.json').write_text(json.dumps(tl,indent=2));return tl

async def _cpu_narrate(spec,out,cache):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    request=out/'cpu-voice-request.json';report=out/'cpu-voice-report.json'
    request.write_text(json.dumps(spec,indent=2))
    await asyncio.to_thread(subprocess.run,[sys.executable,'-m','studio_lib.cpu_voice','--spec',str(request),'--report',str(report)],check=True,timeout=600)
    data=json.loads(report.read_text())
    if data.get('provider')!='kokoro-onnx-cpu' or len(data.get('lines',[]))!=len(spec['beats']):raise ValueError('CPU voice result is incomplete')
    t=0;beats=[]
    for b,line in zip(spec['beats'],data['lines']):
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',line['voice']]))
        if not .2<duration<90:raise ValueError('CPU narration duration is invalid')
        length=max(b['seconds'],duration+line['delivery']['pause_after'])
        beats.append(dict(b,start=t,end=t+length,voice=line['voice'],voice_duration=duration,delivery=line['delivery']));t+=length
    require_duration(t)
    timeline={'beats':beats,'duration':t,'narration_requests':0,'cached_lines':data['cached_lines'],'voice_provider':'kokoro-onnx-cpu','voice':data['voice'],'primary_audio_cache_retained':True}
    (out/'timeline.json').write_text(json.dumps(timeline,indent=2));return timeline

async def narrate(spec,out,cache):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    route=cache/('route-'+hashlib.sha256(json.dumps([b['say'] for b in spec['beats']]).encode()).hexdigest()+'.json')
    if os.environ.get('CE_FORCE_CPU_VOICE')=='1':
        route.write_text(json.dumps({'provider':'kokoro-onnx-cpu','reason':'Owner-authorized failover proof after primary outage'}))
    if route.exists() and json.loads(route.read_text()).get('provider')=='kokoro-onnx-cpu':
        return await _cpu_narrate(spec,out,cache)
    try:return await _primary_narrate(spec,out,cache)
    except (edge_tts.exceptions.NoAudioReceived,asyncio.TimeoutError):
        route.write_text(json.dumps({'provider':'kokoro-onnx-cpu','reason':'Primary voice returned no complete audio after bounded attempts'}))
        print('Primary voice unavailable; resuming one consistent stock voice on the GitHub CPU',flush=True)
        return await _cpu_narrate(spec,out,cache)

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
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'silent.mp4'),'-i',str(out/'mix.wav'),'-c:v','copy','-c:a','aac','-b:a','160k',*mastering_args(),'-t',str(T),'-movflags','+faststart',str(out/'video.mp4')],check=True)
