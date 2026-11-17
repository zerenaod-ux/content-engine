"""Mix cached measured narration with generated, synchronized sound and music."""
import argparse, json, subprocess, sys, time, wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent.parent))
from scene_lib import audio as A
OUT=ROOT/'output'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--name',default='drawbridge-review.mp4');args=ap.parse_args()
    if Path(args.name).name!=args.name:raise ValueError('output name must be a file name')
    t0=time.monotonic();tl=json.loads((OUT/'timeline.json').read_text());T=tl['duration'];n=int(T*A.SR)
    voice=np.zeros(n);fx=np.zeros(n);rng=np.random.RandomState(42)
    def put(track,x,start,gain=1):
        i=int(start*A.SR);x=x[:max(0,len(track)-i)];track[i:i+len(x)]+=x*gain
    for b in tl['beats']:
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',b['voice'],'-f','f32le','-ac','1','-ar',str(A.SR),'-'])
        x=np.frombuffer(raw,dtype=np.float32).astype(float)
        if len(x)/A.SR>b['end']-b['start']-.1:raise RuntimeError('narration exceeds measured window')
        put(voice,x,b['start']+.1)
    voice=A.norm(voice,.78)
    # Motor sound follows only actual leaf motion; no whoosh on every edit.
    for a,b in [(tl['beats'][3]['start'],tl['beats'][4]['end']),(tl['beats'][6]['start'],tl['beats'][6]['end'])]:
        d=b-a;t=np.arange(int(d*A.SR))/A.SR;env=np.minimum(1,t*2)*np.minimum(1,(d-t)*2)
        motor=(np.sin(2*np.pi*95*t)+.3*np.sin(2*np.pi*190*t)+.10*np.sin(2*np.pi*720*t))*env
        put(fx,motor,a,.024)
    put(fx,A.click(),tl['beats'][1]['start']+.3,.13)
    put(fx,A.thunk(),tl['beats'][6]['end']-.05,.10)
    put(fx,A.click(),tl['beats'][7]['start']+.2,.16)
    d=tl['beats'][5]['end']-tl['beats'][5]['start'];put(fx,A.flow(d),tl['beats'][5]['start'],.025)
    bed=A.music(T,bpm=108,energy=.22)
    # Short-time envelope for ducking, linear-time rather than wide convolution.
    win=2205;env=np.array([np.abs(voice[i:i+win]).mean() for i in range(0,n,win)])
    e=np.interp(np.arange(n),np.arange(len(env))*win,env);duck=1-.65*np.clip(e*12,0,1)
    out=voice+fx+bed*.10*duck
    t=np.arange(n)/A.SR;out*=np.minimum(1,t*4)*np.minimum(1,(T-t)*3)
    A.write_wav(str(OUT/'mix.wav'),out)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'mix.wav'),'-c:v','copy','-c:a','aac','-b:a','192k','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-t',str(T),'-movflags','+faststart',str(OUT/args.name)],check=True)
    report={'assembly_seconds':time.monotonic()-t0,'voice_peak':float(abs(voice).max()),'mix_peak_before_normalization':float(abs(out).max()),'narration_sped_up':False,'generated_sound':True}
    (OUT/'audio-metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
