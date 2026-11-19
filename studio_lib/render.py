"""Render data-only AI-authored scenes with persistent objects and auto framing."""
import json, math, subprocess, time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from studio_lib.mesh import Scene,ease
W,H=720,1280
FONTPATH=next((p for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf','/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf','/System/Library/Fonts/Supplemental/Arial.ttf'] if Path(p).exists()),'DejaVuSans.ttf')
FONT=ImageFont.truetype(FONTPATH,22);TITLE=ImageFont.truetype(FONTPATH,43)
BG=Image.fromarray(np.broadcast_to(np.linspace([245,246,233],[201,225,225],H,dtype=np.uint8)[:,None,:],(H,W,3)).copy())
def sample(keys,phase,default):
    if not keys:return default
    if phase<=keys[0][0]:return keys[0][1]
    for a,b in zip(keys,keys[1:]):
        if phase<=b[0]:return a[1]+(b[1]-a[1])*ease((phase-a[0])/(b[0]-a[0]))
    return keys[-1][1]
def phase_at(t,beats):
    for i,b in enumerate(beats):
        if t<b['end']:return i+max(0,(t-b['start'])/(b['end']-b['start']))
    return len(beats)-1e-8
def transforms(spec,phase):
    by={o['id']:o for o in spec['objects']};done={};vis={}
    def one(oid):
        if oid in done:return done[oid]
        o=by[oid];m=o.get('motion',{});ang=math.radians(sample(m.get('angle'),phase,0));c,s=math.cos(ang),math.sin(ang)
        axis=o.get('axis','y')
        r={'y':[[c,0,-s],[0,1,0],[s,0,c]],'x':[[1,0,0],[0,c,-s],[0,s,c]],'z':[[c,-s,0],[s,c,0],[0,0,1]]}[axis]
        a=np.eye(4);a[:3,:3]=np.array(r)*sample(m.get('scale'),phase,1)
        a[:3,3]=np.array(o['position'])+np.array([sample(m.get(k),phase,0) for k in ('x','y','z')])
        visible=sample(m.get('visible'),phase,1)>.5
        if o.get('parent'):a=one(o['parent'])@a;visible=visible and vis[o['parent']]
        done[oid]=a;vis[oid]=visible;return a
    for oid in by:one(oid)
    return done,vis
class ObjectMesh(Scene):
    def __init__(self,owner,matrix):self.owner=owner;self.matrix=matrix;self.gear_marks=[]
    def face(self,points,color):
        p=np.asarray(points,float);p=np.column_stack([p,np.ones(len(p))])@self.matrix.T
        self.owner.face(p[:,:3],tuple(int(c) for c in color))
def add_object(scene,o,matrix):
    local=ObjectMesh(scene,matrix)
    for m in o['meshes']:
        kind=m['type'];col=m['color']
        if kind=='box':local.box(m['at'],m['size'],col)
        elif kind=='beam':local.beam(m['a'],m['b'],m['radius'],col)
        elif kind=='cylinder':local.cylinder(m['at'],m['radius'],m['length'],col,n=16)
        elif kind=='gear':local.gear(m['at'],m['radius'],m['teeth'],0,col)
        elif kind=='face':local.face(m['points'],col)
    # Marker strokes are part of the data's actual rigid transform.
    if not hasattr(scene,'reference_marks'):scene.reference_marks=[]
    for (x,y,z),r,a in local.gear_marks:
        points=np.array([[x+r*.38*math.cos(a),y,z+r*.38*math.sin(a),1],[x+r*.79*math.cos(a),y,z+r*.79*math.sin(a),1]])@matrix.T
        scene.reference_marks.append(points[:,:3])
class BoundsCollector:
    def __init__(self):self.points=[]
    def face(self,p,c):self.points.extend(p)
def geometry(spec,phase,hidden=()):
    mats,visible=transforms(spec,phase);by={o['id']:o for o in spec['objects']};parts={}
    for o in spec['objects']:
        parent=o.get('parent');blocked=o['id'] in hidden
        while parent in by:
            blocked=blocked or parent in hidden;parent=by[parent].get('parent')
        if visible[o['id']] and not blocked:
            collect=BoundsCollector();add_object(collect,o,mats[o['id']]);parts[o['id']]=np.array(collect.points)
    return parts,mats,visible
def camera(spec,phase,parts,focus_override=None):
    i=min(len(spec['beats'])-1,int(phase));focus=focus_override or spec['beats'][i]['focus'];by={o['id']:o for o in spec['objects']}
    def belongs(oid):
        while oid:
            if oid in focus:return True
            oid=by[oid].get('parent')
        return False
    pts=[p for oid,p in parts.items() if belongs(oid)] or list(parts.values())
    cloud=np.concatenate(pts);lo,hi=cloud.min(axis=0),cloud.max(axis=0);target=(lo+hi)/2
    # Fit a real projected geometry envelope, not a guessed box.
    az=.36+.06*math.sin(phase*.35)
    zoom=.40;upper=2.8
    for _ in range(12):
        z=(zoom+upper)/2
        c=Scene(0,z,target,az);xy,depth=c.project(cloud)
        if min(depth)<.5 or xy[:,0].min()<38 or xy[:,0].max()>682 or xy[:,1].min()<340 or xy[:,1].max()>1130:upper=z
        else:zoom=z
    return target,zoom,az
def frame(spec,t,timeline,hidden=(),camera_override=None):
    phase=phase_at(t,timeline['beats']);parts,mats,visible=geometry(spec,phase,hidden)
    # Camera always uses complete scene even for part-removal evidence checks.
    fullparts=geometry(spec,phase)[0] if hidden else parts
    target,zoom,az=camera_override or camera(spec,phase,fullparts)
    i=int(phase);fraction=phase-i
    if camera_override is None and i>0 and fraction<.3:
        previous=camera(spec,phase,fullparts,spec['beats'][i-1]['focus']);blend=ease(fraction/.3)
        target=previous[0]*(1-blend)+target*blend;zoom=previous[1]*(1-blend)+zoom*blend
    im=BG.copy();scene=Scene(t,zoom,target,az);scene.reference_marks=[]
    ground=Scene(t,zoom,target,az)
    water=spec['setting']=='ocean';space=spec['setting']=='space'
    if not space:
        ground.face([[-1000,-1000,-.08],[1000,-1000,-.08],[1000,1000,-.08],[-1000,1000,-.08]],(66,160,175) if water else (211,222,216));ground.paint(im)
    for o in spec['objects']:
        if o['id'] in parts:add_object(scene,o,mats[o['id']])
    scene.paint(im);d=ImageDraw.Draw(im)
    for pts in scene.reference_marks:
        q,dep=scene.project(pts)
        if min(dep)>.2:d.line([tuple(p) for p in q],fill=(255,247,207),width=4)
    mask=Image.new('L',(W,H));md=ImageDraw.Draw(mask)
    for y in range(300):md.line((0,y,W,y),fill=255 if y<245 else int(255*(300-y)/55))
    im.paste(BG,(0,0),mask);d=ImageDraw.Draw(im)
    d.text((42,65),'HOW IT TICKS',font=FONT,fill=(31,77,89))
    import textwrap
    for j,line in enumerate(textwrap.wrap(spec.get('hook',spec['title']),25)[:3]):d.text((42,125+j*55),line,font=TITLE,fill=(30,65,78))
    d.line((42,1195,678,1195),fill=(170,200,200),width=3)
    d.line((42,1195,42+636*t/timeline['duration'],1195),fill=(221,102,57),width=3)
    return im
def render(spec,timeline,out,fps=30):
    started=time.monotonic();n=math.ceil(timeline['duration']*fps);out=Path(out)
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x1280','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(frame(spec,k/fps,timeline).tobytes())
        if k%150==0:print(f'render {k}/{n}',flush=True)
    p.stdin.close()
    if p.wait():raise RuntimeError('render failed')
    return {'render_seconds':time.monotonic()-started,'frames':n,'fps':fps}
