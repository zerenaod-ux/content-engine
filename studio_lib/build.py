"""Topic -> free-model scene -> bounded automatic repair -> narrated MP4.

No manually edited generated scenes or topic scripts are read by this path.
"""
import argparse,asyncio,hashlib,json,os,subprocess,time
from pathlib import Path
from studio_lib.plan import generate,audit
from studio_lib import novelty
from studio_lib.check import provisional,inspect
from studio_lib.render import render
from studio_lib.audio import narrate,assemble
def run(topic,out):
    novelty.reserve_new(topic)
    out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic();candidate=None;errors=None;resume_audit=False
    provenance={'topic':topic,'manual_scene_edits':False,'scene_source':'fresh free-model response','owner_approved':False,'production_enabled':False}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2))
    for attempt in range(3):
        folder=out/f'attempt-{attempt}';folder.mkdir(exist_ok=True)
        try:
            if not resume_audit:
                candidate,errors=generate(topic,folder,errors,candidate)
            else:
                errors=[]
                (folder/'candidate.json').write_text(json.dumps(candidate,indent=2))
                print('reuse unchanged valid candidate; retry audit only',flush=True)
            if not errors:
                resume_audit=True
                errors=audit(candidate)
                resume_audit=False
                (folder/'editorial-audit.json').write_text(json.dumps({'errors':errors,'external_fact_verification':False},indent=2))
            if not errors:errors=inspect(candidate,provisional(candidate),folder)
        except Exception as e:
            errors=[type(e).__name__+': '+str(e)[:400]]
        (folder/'outcome.json').write_text(json.dumps({'errors':errors,'manual_scene_edits':False},indent=2))
        if not errors:break
        print('automatic candidate rejected:', '; '.join(errors[:6]),flush=True)
    if errors:
        (out/'result.json').write_text(json.dumps(dict(provenance,status='rejected',errors=errors,wall_seconds=time.monotonic()-start),indent=2));raise ValueError('automatic scene failed; evidence retained; no video promoted')
    # The exact unedited accepted candidate becomes the render input.
    (out/'scene.json').write_text(json.dumps(candidate,indent=2));tl=asyncio.run(narrate(candidate,out,Path('.ce-cache/studio-voice')))
    errors=inspect(candidate,tl,out)
    if errors:raise ValueError('measured-timing evidence failed: '+'; '.join(errors[:5]))
    metrics=render(candidate,tl,out/'silent.mp4');assemble(candidate,tl,out)
    novelty.record_created(topic,None,out/'video.mp4')
    subprocess.run(['ffmpeg','-v','error','-i',str(out/'video.mp4'),'-f','null','-'],check=True)
    result=dict(provenance,status='technical_checks_passed_editorial_pending',wall_seconds=time.monotonic()-start,attempts=attempt+1,video_sha256=hashlib.sha256((out/'video.mp4').read_bytes()).hexdigest(),duration=tl['duration'],narration_requests=tl['narration_requests'],cached_voice_lines=tl['cached_lines'],**metrics)
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument('--topic',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.topic,a.out)
if __name__=='__main__':main()
