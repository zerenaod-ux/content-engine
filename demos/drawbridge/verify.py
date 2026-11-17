"""Physical sequencing and render checks, separate from aesthetic acceptance."""
import json, math
from pathlib import Path
import numpy as np
from render import state,leaf_transform,frame,APPROACHES,Scene
OUT=Path(__file__).resolve().parent/'output'
tl=json.loads((OUT/'timeline.json').read_text());beats=tl['beats'];checks=[]
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
times=np.linspace(beats[3]['start'],beats[4]['end'],100)
angles=[state(t,beats)['angle'] for t in times]
check('leaf opens monotonically to 72 degrees',all(b>=a for a,b in zip(angles,angles[1:])) and abs(angles[-1]-math.radians(72))<1e-6)
weights=[leaf_transform(a)(np.array([[-1.6,0,-.5]]))[0,2] for a in angles]
check('rigid counterweight descends during opening',all(b<=a for a,b in zip(weights,weights[1:])))
check('pivot stays fixed',all(np.allclose(leaf_transform(a)(np.array([[0,0,0]]))[0],[-2.8,0,2.5]) for a in angles))
check('barriers closed whenever bridge raised',all(state(t,beats)['gate']>.99 for t in np.linspace(0,tl['duration'],500) if state(t,beats)['angle']>.02))
check('ship crosses only with bridge fully raised',all(abs(state(t,beats)['angle']-math.radians(72))<1e-6 for t in np.linspace(beats[5]['start'],beats[5]['end']-.01,100)))
check('road returns before traffic resumes',all(state(t,beats)['angle']<1e-6 for t in np.linspace(beats[7]['start'],beats[7]['end'],50)))
check('narration fits without time stretching',all(b['voice_duration']+.1<b['end']-b['start'] for b in beats))
check('all sampled frames bright enough',all(np.asarray(frame(b['start']+.5,tl)).mean()>85 for b in beats))
roads=sorted([(x-length/2,x+length/2) for x,length in APPROACHES]+[(-5.2,2.8)])
check('closed road joins have no gaps',all(abs(a[1]-b[0])<1e-8 for a,b in zip(roads,roads[1:])))
check('every wheel location has road support throughout crossing',all(any(a<=x+dx<=b for a,b in roads) for x in np.linspace(-6.7,7,300) for dx in [-.25,.25]))
visible=[]
for t in np.linspace(beats[5]['end']-.1,tl['duration']-.1,8):
    actual=np.asarray(frame(t,tl)).astype(int);removed=np.asarray(frame(t,tl,hidden=('ship',))).astype(int)
    visible.append(int(np.count_nonzero(np.max(abs(actual-removed),axis=2)>20)))
check('ship contributes visible pixels after passage through final shot',min(visible)>50)
from PIL import Image
gearframes=[]
for angle in [0,.5]:
    scene=Scene(0,2.8,[-3.1,-.55,2.3],.18)
    scene.gear((-3.8,-1.16,2.5),.30,12,-angle*28/12+math.pi/12,(113,150,168))
    im=Image.new('RGB',(720,1280));scene.paint(im);gearframes.append(np.asarray(im).astype(int))
check('pinion rotation visibly changes rendered pixels with fixed camera',np.count_nonzero(np.max(abs(gearframes[0]-gearframes[1]),axis=2)>30)>100)
samples=[state(t,beats) for t in np.arange(0,tl['duration'],1/30)]
check('camera zoom changes continuously at output frame rate',max(abs(a['zoom']-b['zoom']) for a,b in zip(samples,samples[1:]))<.05)
report={'checks':checks,'editorial_approval':False,'limits':'Stylized authored mechanism, no structural engineering simulation; visual checks cannot establish audience appeal.'}
report['ship_visible_pixels_after_passage']=visible
(OUT/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
