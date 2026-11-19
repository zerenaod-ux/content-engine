"""Measured cached narration and a quiet generated soundtrack, free services only."""
import asyncio,hashlib,json,subprocess,time,wave,sys,os
from pathlib import Path
import numpy as np
import edge_tts
from studio_lib.service_queue import lease
from studio_lib.duration import require_duration
from studio_lib.audio_mastering import mastering_args
from studio_lib.cinema.speech import delivery,VOICE
from studio_lib.voice_policy import PROVIDER,VERSION
SR=24000
async def _cpu_narrate(spec,out,cache,duration_range=(40,70)):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    request=out/'cpu-voice-request.json';report=out/'cpu-voice-report.json'
    request.write_text(json.dumps(spec,indent=2))
    await asyncio.to_thread(subprocess.run,[sys.executable,'-m','studio_lib.cpu_voice','--spec',str(request),'--report',str(report)],check=True,timeout=600)
    data=json.loads(report.read_text())
    if data.get('provider')!=PROVIDER or data.get('voice')!=VOICE or data.get('voice_policy')!=VERSION or len(data.get('lines',[]))!=len(spec['beats']):raise ValueError('CPU voice result is incomplete')
    t=0;beats=[]
    for b,line in zip(spec['beats'],data['lines']):
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',line['voice']]))
        if not .2<duration<90:raise ValueError('CPU narration duration is invalid')
        if line.get('speaker')!=VOICE:raise ValueError('Narrator identity mismatch; do not switch speakers')
        length=max(b['seconds'],duration+.08+line['delivery']['pause_after'])
        beats.append(dict(b,start=t,end=t+length,voice=line['voice'],voice_duration=duration,delivery=line['delivery']));t+=length
    if not duration_range[0]<=t<=duration_range[1]:raise ValueError('Measured narration outside required duration range: '+str(t))
    timeline={'beats':beats,'duration':t,'narration_requests':0,'cached_lines':data['cached_lines'],'voice_provider':'kokoro-onnx-cpu','voice':data['voice'],'voice_policy':VERSION,'primary_audio_cache_retained':True}
    (out/'timeline.json').write_text(json.dumps(timeline,indent=2));return timeline

async def narrate(spec,out,cache,duration_range=(40,70)):
    # A single identity replaces provider-dependent voice switching. Cached
    # older routes are intentionally ignored; an outage remains retryable.
    return await _cpu_narrate(spec,out,cache,duration_range=duration_range)

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
