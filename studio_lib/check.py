"""Rendered evidence gates; never equate technical passes with owner approval."""
import json
from pathlib import Path
import numpy as np
from studio_lib.render import frame,geometry,camera,phase_at
def provisional(spec):
    t=0;beats=[]
    for b in spec['beats']:
        beats.append(dict(b,start=t,end=t+b['seconds']));t+=b['seconds']
    return {'beats':beats,'duration':t}
def inspect(spec,timeline,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);errors=[];rows=[];frames=[]
    for i,b in enumerate(timeline['beats']):
        t=(b['start']+b['end'])/2;phase=phase_at(t,timeline['beats']);parts,_,_=geometry(spec,phase);cam=camera(spec,phase,parts)
        actual=np.asarray(frame(spec,t,timeline,camera_override=cam)).astype(int)
        frame(spec,t,timeline,camera_override=cam).save(out/f'beat-{i:02d}.jpg');frames.append(actual)
        for oid in b['evidence']:
            removed=np.asarray(frame(spec,t,timeline,hidden=(oid,),camera_override=cam)).astype(int)
            delta=np.max(abs(actual-removed),axis=2);count=int(np.count_nonzero(delta>22))
            rows.append({'beat':i,'object':oid,'visible_pixels':count})
            if count<120:errors.append(f'beat {i}: evidence object {oid} only contributes {count} visible pixels; expose/enlarge/frame the actual part')
        # Check changes at a FIXED camera; camera panning cannot pass this gate.
        a=np.asarray(frame(spec,b['start']+.15,timeline,camera_override=cam)).astype(int)
        z=np.asarray(frame(spec,b['end']-.15,timeline,camera_override=cam)).astype(int)
        motion=int(np.count_nonzero(np.max(abs(a-z),axis=2)[310:1160]>25))
        rows.append({'beat':i,'fixed_camera_changed_pixels':motion})
        if i not in (0,len(timeline['beats'])-1) and motion<100:errors.append(f'beat {i}: no visible object motion at fixed camera; animate the mechanism, not the camera')
    from PIL import Image
    sheet=Image.new('RGB',(360*4,640*((len(frames)+3)//4)))
    for i,fr in enumerate(frames):sheet.paste(Image.fromarray(fr.astype('uint8')).resize((360,640)),((i%4)*360,(i//4)*640))
    sheet.save(out/'contact.jpg')
    report={'errors':errors,'measurements':rows,'automatic_checks_passed':not errors,'semantic_verification':False,'owner_approved':False}
    (out/'evidence-report.json').write_text(json.dumps(report,indent=2));return errors
