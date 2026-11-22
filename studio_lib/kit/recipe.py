"""Recipe schema, validator and generic machine built only from tested kit parts.
Coordinates are in the x-z plane (x right, z up from the floor); every recipe is shifted up by ZC so it sits where hand-built machines sit."""
import math,functools
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient

ZC=2.8
KINDS={'frame':('x','z','w','h'),'lever':('pivot','length'),'gear':('center','r','teeth'),'slider':('origin','size','axis','travel'),'spring':('a','b'),'pin':('center','r'),'cam':('center','r','e'),'pulley':('center','r')}
PARAM={'lever':'angle','gear':'angle','slider':'pos','cam':'angle','pulley':'angle'}
THEMES={'warm':((250,241,213),(226,218,181),(222,210,179)),'cool':((226,238,246),(190,211,226),(205,222,232)),'dark':((24,31,45),(12,16,26),(30,36,48))}
PALETTE={'frame':(110,84,60),'lever':(197,146,83),'gear':(213,170,76),'slider':(150,160,168),'spring':(164,178,179),'pin':(70,84,96),'cam':(205,112,84),'pulley':(96,150,176)}
LIM={'x':(-7.5,7.5),'z':(-.5,7.5)}

class RecipeError(ValueError):pass
def _num(v,name,lo=-50,hi=50):
 if not isinstance(v,(int,float)) or isinstance(v,bool) or not (lo<=v<=hi) or v!=v:raise RecipeError(f'{name} must be a number in [{lo},{hi}]')
 return float(v)
def _pt(v,name):
 if not (isinstance(v,(list,tuple)) and len(v)==2):raise RecipeError(f'{name} must be [x,z]')
 return (_num(v[0],name+'.x',*LIM['x']),_num(v[1],name+'.z',*LIM['z']))

def validate(recipe):
 """Raise RecipeError for anything the kit cannot build safely; return the normalised recipe."""
 if not isinstance(recipe,dict):raise RecipeError('recipe must be an object')
 parts=recipe.get('parts');drive=recipe.get('drive',[]);links=recipe.get('links',[]);labels=recipe.get('labels',{})
 if recipe.get('theme','warm') not in THEMES:raise RecipeError('unknown theme')
 if not isinstance(parts,list) or not 3<=len(parts)<=14:raise RecipeError('3-14 parts required')
 ids={}
 for p in parts:
  if not isinstance(p,dict) or p.get('kind') not in KINDS:raise RecipeError('unknown part kind: %s'%(p.get('kind') if isinstance(p,dict) else p))
  pid=p.get('id')
  if not isinstance(pid,str) or not pid.isidentifier() or pid in ids:raise RecipeError('part ids must be unique identifiers')
  ids[pid]=p
  for key in KINDS[p['kind']]:
   if key not in p and not (p['kind']=='slider' and key=='axis'):raise RecipeError(f'{pid} missing {key}')
  k=p['kind']
  if k=='frame':
   _num(p['x'],'x',*LIM['x']);_num(p['z'],'z',*LIM['z']);_num(p['w'],'w',1,15);_num(p['h'],'h',1,8)
  elif k=='lever':_pt(p['pivot'],pid+'.pivot');_num(p['length'],'length',.5,5);_num(p.get('angle0',0),'angle0',-3.2,3.2)
  elif k=='gear':
   _pt(p['center'],pid+'.center');_num(p['r'],'r',.3,2.2)
   if not isinstance(p['teeth'],int) or not 8<=p['teeth']<=40:raise RecipeError(f'{pid} teeth must be an int 8-40')
  elif k=='slider':
   _pt(p['origin'],pid+'.origin');s=p['size'];_num(s[0],'size',.2,5);_num(s[1],'size',.1,3)
   if p.get('axis','x') not in ('x','z'):raise RecipeError('slider axis must be x or z')
   if p.get('dir',1) not in (1,-1):raise RecipeError('slider dir must be 1 or -1')
   _num(p['travel'],'travel',.1,4)
  elif k=='spring':
   _pt(p['a'],pid+'.a')
   b=p['b']
   if isinstance(b,dict):
    if b.get('part') not in ids and b.get('part') not in [q.get('id') for q in parts]:raise RecipeError(pid+' spring end references an unknown part')
   else:_pt(b,pid+'.b')
  elif k=='pin':_pt(p['center'],pid+'.center');_num(p['r'],'r',.08,.6)
  elif k=='cam':_pt(p['center'],pid+'.center');_num(p['r'],'r',.5,1.5);_num(p['e'],'e',.15,.6)
  elif k=='pulley':_pt(p['center'],pid+'.center');_num(p['r'],'r',.4,1.2)
 if not any(p['kind']!='frame' and p['kind']!='spring' and p['kind']!='pin' for p in parts):raise RecipeError('needs at least one moving part')
 if sum(p['kind']=='frame' for p in parts)!=1:raise RecipeError('exactly one frame required')
 if not isinstance(labels,dict) or not 3<=len(labels)<=8 or any(k not in ids or not isinstance(v,str) or not 2<=len(v)<=28 for k,v in labels.items()):raise RecipeError('3-8 labels on existing parts required')
 driven=set()
 mesh=[]
 for l in links:
  if not isinstance(l,dict) or l.get('type') not in ('mesh','couple','yoke','cam','rope'):raise RecipeError('link type must be mesh, couple, yoke, cam or rope')
  if l['type']=='mesh':
   a,b=ids.get(l.get('a')),ids.get(l.get('b'))
   if not a or not b or a['kind']!='gear' or b['kind']!='gear':raise RecipeError('mesh links join two gears')
   d=math.dist(a['center'],b['center']);gap=d-a['r']-b['r']
   if abs(gap)>.12:raise RecipeError('gears %s/%s do not mesh: centre gap off by %.2f'%(a['id'],b['id'],gap))
   driven.add(b['id']);mesh.append((a['id'],b['id']))
  elif l['type'] in ('yoke','cam','rope'):
   a=ids.get(l.get({'yoke':'lever','cam':'cam','rope':'pulley'}[l['type']]));b=ids.get(l.get({'yoke':'slider','cam':'follower','rope':'slider'}[l['type']]))
   want={'yoke':('lever','slider'),'cam':('cam','slider'),'rope':('pulley','slider')}[l['type']]
   if not a or not b or a['kind']!=want[0] or b['kind']!=want[1]:raise RecipeError(l['type']+' link joins a '+want[0]+' and a '+want[1])
   if l['type']=='cam':
    if b.get('axis','x')!='z' or abs(b['origin'][0]-a['center'][0])>.3:raise RecipeError('cam follower must be a z-axis slider directly above the cam centre')
    if abs((b['origin'][1]-b['size'][1]/2)-(a['center'][1]+a['r']-a['e']))>.2:raise RecipeError('cam follower bottom must rest on the cam at its lowest point: z = cam z + r - e = %.2f'%(a['center'][1]+a['r']-a['e']))
    if b['travel']<2*a['e']-.01:raise RecipeError('cam follower travel must be at least 2*e')
   if l['type']=='rope':
    if b.get('axis','x')!='z' or abs((b['origin'][0])-(a['center'][0]+a['r']))>.25:raise RecipeError('rope slider must be a z-axis slider hanging at x = pulley x + r')
   driven.add(b['id'])
   continue
  else:
   dv,dr=ids.get(l.get('driver')),ids.get(l.get('driven'))
   if not dv or not dr or dv['kind'] not in PARAM or dr['kind'] not in PARAM:raise RecipeError('couple links join moving parts')
   _num(l.get('ratio',1),'ratio',-6,6);_num(l.get('offset',0),'offset',-6,6)
   driven.add(dr['id'])
 for pid in driven:
  if any(d.get('part')==pid for d in drive):raise RecipeError(pid+' is driven by a link and cannot also be keyframed')
 keyed={}
 if not isinstance(drive,list) or not drive:raise RecipeError('drive keyframes required')
 for d in drive:
  p=ids.get(d.get('part'))
  if not p or p['kind'] not in PARAM:raise RecipeError('drive targets a moving part')
  if not isinstance(d.get('beat'),int) or not 0<=d['beat']<=7:raise RecipeError('beat must be 0-7')
  lim=(-1.7,1.7) if PARAM[p['kind']]=='angle' else (0,p.get('travel',1))
  if p['kind'] in ('gear','cam','pulley'):lim=(-40,40)
  _num(d.get('to'),'to',*lim);keyed.setdefault(p['id'],set()).add(d['beat'])
 beats=set(b for s in keyed.values() for b in s)
 if len(beats&{1,2,3,4,5,6})<3:raise RecipeError('motion must happen in at least 3 of beats 1-6')
 # Every driven part must have a driver chain that starts at a keyed part (no orphan motion).
 for l in links:
  if l['type']=='couple' and l['driver'] not in keyed and l['driver'] not in driven:raise RecipeError('link driver never moves')
  if l['type']=='mesh' and l['a'] not in keyed and l['a'] not in driven:raise RecipeError('mesh driver never moves')
  if l['type'] in ('yoke','cam','rope'):
   src=l.get({'yoke':'lever','cam':'cam','rope':'pulley'}[l['type']])
   if src not in keyed and src not in driven:raise RecipeError(l['type']+' driver never moves')
 m=Machine(recipe);bad=m.bounds_violation()
 if bad:raise RecipeError(bad)
 return recipe

def _rot(points,pivot,angle):
 p=np.asarray(points,float).copy();c,s=math.cos(angle),math.sin(angle);x=p[:,0]-pivot[0];z=p[:,2]-pivot[1]
 p[:,0]=pivot[0]+x*c-z*s;p[:,2]=pivot[1]+x*s+z*c;return p
LINKSRC={'mesh':('a','b'),'couple':('driver','driven'),'yoke':('lever','slider'),'cam':('cam','follower'),'rope':('pulley','slider')}
TL8={'beats':[{'start':k*6.,'end':(k+1)*6.} for k in range(8)]}

class Machine:
 """Generic machine with the same interface as the hand-built modules."""
 DARK=False
 def __init__(self,recipe):
  self.r=recipe;self.parts={p['id']:p for p in recipe['parts']};self.theme=recipe.get('theme','warm')
  self.DARK=self.theme=='dark';self.GROUND=THEMES[self.theme][2]
  self.drive=sorted(recipe['drive'],key=lambda d:d['beat']);self.links=recipe.get('links',[])
  self.order=self._order();self._shots=None
 def _order(self):
  keyed={d['part'] for d in self.drive};done=set(keyed);out=[];pend=list(self.links)
  for _ in range(len(pend)+1):
   for l in list(pend):
    a,b=LINKSRC[l['type']]
    if l[a] in done:out.append(l);done.add(l[b]);pend.remove(l)
  return out
 def tip(self,p,a):return (p['pivot'][0]+p['length']*math.cos(a),p['pivot'][1]+p['length']*math.sin(a))
 def params(self,t,tl):
  b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7));val={}
  for pid,p in self.parts.items():
   if p['kind'] in PARAM:val[pid]=p.get('angle0',0.) if p['kind']!='slider' else p.get('pos0',0.)
  keys={}
  for d in self.drive:keys.setdefault(d['part'],[]).append(d)
  for pid,ks in keys.items():
   cur=val[pid]
   for d in ks:
    if d['beat']<i:cur=d['to']
    elif d['beat']==i:cur=cur+(d['to']-cur)*ease(progress(t,b[i]))
   val[pid]=cur
  for l in self.order:
   ty=l['type']
   if ty=='mesh':
    a,bb=self.parts[l['a']],self.parts[l['b']];val[bb['id']]=-val[a['id']]*a['teeth']/bb['teeth']+math.pi/bb['teeth']
   elif ty=='couple':val[l['driven']]=l.get('offset',0)+l.get('ratio',1)*val[l['driver']]
   elif ty=='yoke':
    lv,sl=self.parts[l['lever']],self.parts[l['slider']];ax=0 if sl.get('axis','x')=='x' else 1
    val[sl['id']]=l.get('sign',1)*(self.tip(lv,val[lv['id']])[ax]-self.tip(lv,lv.get('angle0',0.))[ax])
   elif ty=='cam':
    cm=self.parts[l['cam']];val[l['follower']]=cm['e']*(1+math.sin(val[cm['id']]))
   elif ty=='rope':
    pu=self.parts[l['pulley']];val[l['slider']]=max(0.,l.get('ratio',1)*pu['r']*val[pu['id']]+l.get('offset',0))
  return i,val
 def slider_geom(self,p,v):
  """Centre (x,z) and size (w,h) of a slider at position v."""
  x,z=p['origin'];L,H=p['size'];d=p.get('dir',1)
  return ((x+L/2+d*v,z) if p.get('axis','x')=='x' else (x,z+d*v)),(L,H)
 def slider_end(self,p,v):
  c,(L,H)=self.slider_geom(p,v);return (c[0]+L/2,c[1]) if p.get('axis','x')=='x' else (c[0],c[1]+H/2)
 def point_of(self,ref,val):
  p=self.parts[ref]
  if p['kind']=='slider':return self.slider_end(p,val[ref])
  if p['kind']=='lever':return self.tip(p,val[ref])
  return tuple(p.get('center',p.get('origin',(0,0))))
 def state(self,t,tl):
  i,val=self.params(t,tl);return dict(beat=i,**{k:float(v) for k,v in val.items()})
 def extents(self,pid,val):
  """Axis-aligned (x0,z0,x1,z1) of a moving part."""
  p=self.parts[pid];k=p['kind']
  if k=='lever':
   tx,tz=self.tip(p,val[pid]);px,pz=p['pivot'];return (min(px,tx)-.2,min(pz,tz)-.2,max(px,tx)+.2,max(pz,tz)+.2)
  if k=='slider':
   (cx,cz),(L,H)=self.slider_geom(p,val[pid]);return (cx-L/2,cz-H/2,cx+L/2,cz+H/2)
  if k in ('gear','pulley'):x,z=p['center'];r=p['r']*1.06;return (x-r,z-r,x+r,z+r)
  if k=='cam':x,z=p['center'];r=p['r']+p['e'];return (x-r,z-r,x+r,z+r)
  return None
 def moving_ids(self):
  ids=[p['id'] for p in self.r['parts'] if p['kind'] in PARAM]
  moving=set()
  for i in range(8):
   a=self.params(i*6+1e-5,TL8)[1];b=self.params((i+1)*6-1e-5,TL8)[1]
   for pid in ids:
    if abs(a[pid]-b[pid])>.02:moving.add(pid)
  return [x for x in ids if x in moving]
 def bounds_violation(self):
  fr=next(p for p in self.r['parts'] if p['kind']=='frame');x0,x1=fr['x']-fr['w']/2,fr['x']+fr['w']/2;z0,z1=fr['z'],fr['z']+fr['h']
  for t in np.linspace(0,47.9,97):
   i,val=self.params(float(t),TL8)
   for pid,p in self.parts.items():
    if p['kind']=='slider' and (val[pid]<-1e-6 or val[pid]>p['travel']+1e-6):return f'{pid} moves {val[pid]:.2f}, outside its travel 0..{p["travel"]}'
    e=self.extents(pid,val)
    if e and not (x0-.15<=e[0] and e[2]<=x1+.15 and z0-.15<=e[1] and e[3]<=z1+.15):return f'{pid} leaves the frame: it reaches x {e[0]:.1f}..{e[2]:.1f}, z {e[1]:.1f}..{e[3]:.1f} but the frame allows x {x0:.1f}..{x1:.1f}, z {z0:.1f}..{z1:.1f}. Shorten its len, move its pivot inward, or use smaller drive angles (levers: angle within about +-0.6 rad with len under half the frame height)'
   for l in self.links:
    if l['type']=='yoke':
     lv,sl=self.parts[l['lever']],self.parts[l['slider']];tx,tz=self.tip(lv,val[lv['id']]);(cx,cz),(L,H)=self.slider_geom(sl,val[sl['id']])
     inside=(cz-H/2+.05<=tz<=cz+H/2-.05 and abs(tx-cx)<=L/2) if sl.get('axis','x')=='x' else (cx-L/2+.05<=tx<=cx+L/2-.05 and abs(tz-cz)<=H/2)
     if not inside:return f"{lv['id']} tip leaves the slot of {sl['id']}: lever and slider do not stay joined"
  return None
 @functools.lru_cache(maxsize=1)
 def background(self):top,bot,_=THEMES[self.theme];return gradient(top,bot)
 def elevation(self,t,tl):return 5.5
 def _fit(self,box,pad,cap=2.7):
  w=box[2]-box[0]+2*pad;h=box[3]-box[1]+2*pad;zx=640/(48.75*w);zz=860*.95/(48.75*h)
  return max(1.0,min(cap,min(zx,zz)*.80))
 def _compute_shots(self):
  fr=next(p for p in self.r['parts'] if p['kind']=='frame');mid=(fr['x'],0,fr['z']+fr['h']/2+ZC)
  moving=self.moving_ids();per=[]
  for i in range(8):
   boxes=[]
   for u in np.linspace(0,1,9):
    val=self.params(i*6+u*6-(1e-5 if u==1 else 0),TL8)[1]
    for pid in moving:boxes.append(self.extents(pid,val))
   per.append(boxes)
  wide=self._fit((fr['x']-fr['w']/2,fr['z'],fr['x']+fr['w']/2,fr['z']+fr['h']),.35,cap=2.2)
  out=[]
  for i in range(8):
   if i in (0,7):out.append((mid,wide,.32));continue
   boxes=[b for b in per[i]+per[i-1] if b];arr=np.array(boxes)
   box=(arr[:,0].min(),arr[:,1].min(),arr[:,2].max(),arr[:,3].max())
   cx,cz=(box[0]+box[2])/2,(box[1]+box[3])/2;z=self._fit(box,.55)
   if 1<i<7:z/=1.25          # camera_direction multiplies these beats by 1.25
   out.append(((cx,0,cz+ZC),z,(.28 if i%2 else -.22)))
  return out
 def shot(self,i):
  if self._shots is None:self._shots=self._compute_shots()
  return self._shots[min(i,7)]
 @property
 def SHOTS(self):return [self.shot(i) for i in range(8)]
 def callouts(self,s,t,tl):
  """Screen-space name tags for the parts the narration is about right now."""
  i,val=self.params(t,tl);b=tl['beats'][i];u=progress(t,b);lab=self.r['labels'];out=[]
  nxt=self.params(b['end']-1e-4,tl)[1] if i<7 else val;prv=self.params(b['start']+1e-4,tl)[1]
  for pid,text in lab.items():
   p=self.parts[pid];k=p['kind'];moving=abs(nxt.get(pid,0)-prv.get(pid,0))>.02 if pid in val else False
   if not (i==1 or moving):continue
   if k=='lever':x,z=self.tip(p,val[pid])
   elif k=='slider':
    (cx,cz),(L,H)=self.slider_geom(p,val[pid]);x,z=cx,cz+H/2
   elif k in ('gear','pulley','cam'):x,z=p['center'][0]-p['r']*1.05-.2,p['center'][1]
   elif k=='spring':a=p['a'];e=self.point_of(p['b']['part'],val) if isinstance(p['b'],dict) else p['b'];x,z=(a[0]+e[0])/2,(a[1]+e[1])/2+.25
   else:x,z=p.get('center',p.get('pivot',(0,0)))[:2] if k!='frame' else (p['x'],p['z']+p['h'])
   px,py=s.point((x,0,z+ZC+.25));out.append((text,(px,py)))
  return out
 def draw(self,s,t,tl,hidden=()):
  i,val=self.params(t,tl);p=dict(beat=i,**{k:float(v) for k,v in val.items()})
  rivet=(168,150,120) if self.theme!='dark' else (110,130,150)
  for part in self.r['parts']:
   if part['id'] in hidden:continue
   k=part['kind'];c=PALETTE[k]
   if k=='frame':
    x,z,w,h=part['x'],part['z']+ZC,part['w'],part['h']
    s.box((x,.55,z+h/2),(w,.12,h),tuple(int(v*.78) for v in c))
    for sx in (-1,1):s.box((x+sx*(w/2-.1),0,z+h/2),(.2,1.0,h),c)
    for sz in (0,h):s.box((x,0,z+sz),(w,1.0,.2),c)
    for sx in (-1,1):
     for sz in (.12,h-.12):s.cylinder((x+sx*(w/2-.1),-.52,z+sz),.07,.06,rivet)
   elif k=='lever':
    px,pz=part['pivot'];a=val[part['id']];L=part['length']
    s.box((px+L/2,-.05,pz+ZC),(L,.3,.26),c,transform=lambda q,px=px,pz=pz+ZC,a=a:_rot(q,(px,pz),a))
    s.cylinder((px,-.05,pz+ZC),.22,.5,PALETTE['pin'])
    tx,tz=self.tip(part,a);s.cylinder((tx,-.12,tz+ZC),.13,.5,(236,224,190))
   elif k=='gear':
    cx,cz=part['center'];s.gear((cx,0,cz+ZC),part['r'],part['teeth'],val[part['id']],c)
   elif k=='cam':
    cx,cz=part['center'];a=val[part['id']];e=part['e'];r=part['r']
    s.cylinder((cx+e*math.cos(a),-.05,cz+e*math.sin(a)+ZC),r,.32,c);s.cylinder((cx,-.2,cz+ZC),.14,.5,PALETTE['pin'])
    s.beam((cx,-.24,cz+ZC),(cx+e*math.cos(a)*1.0+r*.7*math.cos(a),-.24,cz+ZC+e*math.sin(a)+r*.7*math.sin(a)),.04,(255,240,214))
   elif k=='pulley':
    cx,cz=part['center'];a=val[part['id']];r=part['r']
    s.cylinder((cx,-.05,cz+ZC),r,.3,c);s.cylinder((cx,-.2,cz+ZC),r*.78,.12,tuple(int(v*.7) for v in c));s.cylinder((cx,-.26,cz+ZC),.12,.2,PALETTE['pin'])
    s.beam((cx,-.3,cz+ZC),(cx+r*.7*math.cos(a),-.3,cz+ZC+r*.7*math.sin(a)),.04,(255,240,214))
   elif k=='slider':
    (cx,cz),(L,H)=self.slider_geom(part,val[part['id']])
    s.box((cx,-.05,cz+ZC),(L,.34,H),c)
    for l in self.links:
     if l['type']=='yoke' and l['slider']==part['id']:
      lv=self.parts[l['lever']];tx,tz=self.tip(lv,val[lv['id']])
      if part.get('axis','x')=='x':s.box((tx,-.23,cz+ZC),(.2,.06,H*.86),(34,40,48))
      else:s.box((cx,-.23,tz+ZC),(L*.86,.06,.2),(34,40,48))
   elif k=='pin':s.cylinder((part['center'][0],-.1,part['center'][1]+ZC),part['r'],.5,c)
  for l in self.links:   # rope: pulley rim to the hanging slider
   if l['type']=='rope' and self.parts[l['pulley']]['id'] not in hidden:
    pu=self.parts[l['pulley']];sl=self.parts[l['slider']];(cx,cz),(L,H)=self.slider_geom(sl,val[sl['id']])
    s.beam((pu['center'][0]+pu['r'],-.28,pu['center'][1]+ZC),(cx,-.28,cz+H/2+ZC),.03,(228,214,170))
  for part in self.r['parts']:
   if part['kind']!='spring' or part['id'] in hidden:continue
   a=part['a'];b=part['b']
   if isinstance(b,dict):b=self.point_of(b['part'],val)
   n=14;ax,az=a;bx,bz=b;dx,dz=bx-ax,bz-az;d=math.hypot(dx,dz) or 1e-6;nx,nz=-dz/d,dx/d;amp=.2;pts=[]
   for j in range(n+1):
    u=j/n;off=0 if j in (0,n) else amp*(1 if j%2 else -1);pts.append((ax+dx*u+nx*off,-.1,az+dz*u+nz*off+ZC))
   for q,r_ in zip(pts,pts[1:]):s.beam(q,r_,.035,PALETTE['spring'])
  return p

def framing_errors(machine,tl,samples=160):
 """Real-camera check: every moving part stays on screen (with the same flourish camera the video uses) for the whole video."""
 from studio_lib.mesh import Scene
 from studio_lib.camera_direction import tracked_shot,flourish
 moving=machine.moving_ids();hidden=tuple(p['id'] for p in machine.r['parts'] if p['id'] not in moving);errors=[];beats=tl['beats']
 for t in np.linspace(.2,tl['duration']-.2,samples):
  i=min(7,next((j for j,b in enumerate(beats) if t<b['end']),7));zoom,target,az=tracked_shot(t,beats,i,machine);zoom,target,az=flourish(t,beats[i],i,len(beats),zoom,target,az)
  s=Scene(t,zoom,target,az,elevation=machine.elevation(t,tl));machine.draw(s,t,tl,hidden)
  pts=np.array([q for _,poly,_ in s.faces for q in poly])
  if len(pts) and not (pts[:,0].min()>=15 and pts[:,0].max()<=705 and pts[:,1].min()>=290 and pts[:,1].max()<=1175):errors.append(f'moving part leaves the screen at {t:.1f}s')
  if len(errors)>=3:break
 return errors
