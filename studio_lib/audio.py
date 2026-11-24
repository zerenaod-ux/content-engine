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
def duration_speed_scale(duration,bounds,current=1.0):
    if bounds[0]<=duration<=bounds[1]:return None
    target=bounds[0]+2 if duration<bounds[0] else bounds[1]-2
    scale=current*duration/target
    if not .85<=scale<=1.15:raise ValueError('Measured narration cannot fit the duration without an unnatural delivery change')
    return scale

async def _cpu_narrate(spec,out,cache,duration_range=(40,70)):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    request=out/'cpu-voice-request.json';report=out/'cpu-voice-report.json'
    scale=1.0
    for attempt in range(3):
        adjusted=dict(spec,delivery_speed_scale=scale)
        request.write_text(json.dumps(adjusted,indent=2))
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
        next_scale=duration_speed_scale(t,duration_range,scale)
        if next_scale is None:
            timeline={'beats':beats,'duration':t,'narration_requests':0,'cached_lines':data['cached_lines'],'voice_provider':PROVIDER,'voice':VOICE,'voice_policy':VERSION,'pacing_policy':'measured-pace-v1','voice_speed_scale':scale,'duration_fit_attempts':attempt+1,'primary_audio_cache_retained':True}
            (out/'timeline.json').write_text(json.dumps(timeline,indent=2));return timeline
        scale=next_scale
    raise ValueError('Measured narration outside required duration after bounded same-voice adjustment')

async def narrate(spec,out,cache,duration_range=(40,70)):
    # A single identity replaces provider-dependent voice switching. Cached
    # older routes are intentionally ignored; an outage remains retryable.
    return await _cpu_narrate(spec,out,cache,duration_range=duration_range)

def assemble(spec,timeline,out,foley_track=None):
    out=Path(out);T=timeline['duration'];n=int(T*SR);voice=np.zeros(n)
    for b in timeline['beats']:
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',b['voice'],'-ar',str(SR),'-ac','1','-f','f32le','-']);x=np.frombuffer(raw,np.float32).astype(float)
        pos=int((b['start']+.08)*SR);x=x[:n-pos];voice[pos:pos+len(x)]+=x
    # Speech master (no music or generated tone). Machine sounds from the real motion are mixed in below, ducked under speech (foley.py, owner request 2026-11-24).
    mixed=voice*.78/(abs(voice).max()+1e-9)
    if foley_track is not None:   # owner request 2026-11-24: the machine's own sounds, ducked under speech (studio_lib/foley.py)
        from studio_lib import foley as _f;mixed=_f.mix(mixed,foley_track);mixed=mixed/max(1.,abs(mixed).max()/.97)
    if foley_track is not None:   # wordless variant: machine sounds only (reference Short, owner 2026-11-24)
        wl=np.zeros(n);wl[:min(n,len(foley_track))]=foley_track[:n];wl=wl*.8/(abs(wl).max()+1e-9)
        with wave.open(str(out/'foley.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(wl,-.98,.98)*32700).astype(np.int16).tobytes())
    with wave.open(str(out/'mix.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(mixed,-.98,.98)*32700).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'silent.mp4'),'-i',str(out/'mix.wav'),'-c:v','copy','-c:a','aac','-b:a','160k',*mastering_args(),'-t',str(T),'-movflags','+faststart',str(out/'video.mp4')],check=True)
