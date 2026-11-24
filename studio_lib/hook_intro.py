"""Owner rule (2026-11-24): every How It Ticks video opens with a very zoomed-in 2-3 second hook taken from the MIDDLE of the video,
then restarts from the first second and plays to the end. The verified/sealed video.mp4 is never changed; only the delivered copy gets the hook."""
import json,os,shutil,subprocess
from pathlib import Path
HOOK_SECONDS=2.5      # length of the teaser
HOOK_FROM=0.50        # where in the video the teaser is taken (fraction of the duration = the middle)
ZOOM=1.9              # how far the teaser is zoomed in on the centre

def _duration(path):
    return float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(path)]))['format']['duration'])

def _size(path):
    v=next(x for x in json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)]))['streams'] if x['codec_type']=='video')
    return int(v['width']),int(v['height'])

def command(src,dst,duration,start=None,length=HOOK_SECONDS,zoom=ZOOM,width=1080,height=1920):
    start=duration*HOOK_FROM-length/2 if start is None else start
    start=max(0.,min(start,duration-length-0.1))
    cw,ch=f'iw/{zoom}',f'ih/{zoom}'
    f=(f"[0:v]trim=start={start:.3f}:duration={length},setpts=PTS-STARTPTS,crop={cw}:{ch}:(iw-{cw})/2:(ih-{ch})/2,scale={width}:{height}:flags=lanczos,setsar=1,fps=30[hv];"
       f"[0:a]atrim=start={start:.3f}:duration={length},asetpts=PTS-STARTPTS,afade=t=out:st={length-0.12:.2f}:d=0.12,aresample=48000[ha];"
       f"[0:v]setpts=PTS-STARTPTS,setsar=1,fps=30[fv];[0:a]asetpts=PTS-STARTPTS,aresample=48000[fa];"
       f"[hv][ha][fv][fa]concat=n=2:v=1:a=1[v][a]")
    return ['ffmpeg','-v','error','-y','-i',str(src),'-filter_complex',f,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dst)]

def deliver(src,dst):
    """Write the hook version to dst; on any problem deliver the untouched video instead (never block a video)."""
    src=Path(src);dst=Path(dst)
    if os.environ.get('CE_HOOK_INTRO','on')=='off':shutil.copyfile(src,dst);return False
    tmp=dst.with_suffix('.hook.mp4')
    try:
        d=_duration(src);w,h=_size(src);subprocess.run(command(src,tmp,d,width=w,height=h),check=True,timeout=300)
        if _duration(tmp)<d+HOOK_SECONDS-0.5:raise ValueError('hook version shorter than expected')
        shutil.move(str(tmp),str(dst));return True
    except Exception as e:
        print('hook intro skipped:',str(e)[:200],flush=True)
        try:tmp.unlink()
        except OSError:pass
        shutil.copyfile(src,dst);return False
