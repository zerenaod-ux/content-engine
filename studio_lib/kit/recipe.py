"""Recipe schema, validator and generic machine built only from tested kit parts.
Coordinates are in the x-z plane (x right, z up from the floor); every recipe is shifted up by ZC so it sits where hand-built machines sit."""
import math,functools
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient

ZC=2.8
KINDS={'frame':('x','z','w','h'),'lever':('pivot','length'),'gear':('center','r','teeth'),'slider':('origin','size','axis','travel'),'spring':('a','b'),'pin':('center','r')}
PARAM={'lever':'angle','gear':'angle','slider':'pos'}
THEMES={'warm':((250,241,213),(226,218,181),(222,210,179)),'cool':((226,238,246),(190,211,226),(205,222,232)),'dark':((24,31,45),(12,16,26),(30,36,48))}
PALETTE={'frame':(110,84,60),'lever':(197,146,83),'gear':(213,170,76),'slider':(150,160,168),'spring':(164,178,179),'pin':(70,84,96)}
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
   _num(p['travel'],'travel',.1,4)
  elif k=='spring':
   _pt(p['a'],pid+'.a')
   b=p['b']
   if isinstance(b,dict):
    if b.get('part') not in ids and b.get('part') not in [q.get('id') for q in parts]:raise RecipeError(pid+' spring end references an unknown part')
   else:_pt(b,pid+'.b')
  elif k=='pin':_pt(p['center'],pid+'.center');_num(p['r'],'r',.08,.6)
 if not any(p['kind']!='frame' and p['kind']!='spring' and p['kind']!='pin' for p in parts):raise RecipeError('needs at least one moving part')
 if sum(p['kind']=='frame' for p in parts)!=1:raise RecipeError('exactly one frame required')
 if not isinstance(labels,dict) or not 3<=len(labels)<=8 or any(k not in ids or not isinstance(v,str) or not 2<=len(v)<=28 for k,v in labels.items()):raise RecipeError('3-8 labels on existing parts required')
 driven=set()
 mesh=[]
 for l in links:
  if not isinstance(l,dict) or l.get('type') not in ('mesh','couple'):raise RecipeError('link type must be mesh or couple')
  if l['type']=='mesh':
   a,b=ids.get(l.get('a')),ids.get(l.get('b'))
   if not a or not b or a['kind']!='gear' or b['kind']!='gear':raise RecipeError('mesh links join two gears')
   d=math.dist(a['center'],b['center']);gap=d-a['r']-b['r']
   if abs(gap)>.12:raise RecipeError('gears %s/%s do not mesh: centre gap off by %.2f'%(a['id'],b['id'],gap))
   driven.add(b['id']);mesh.append((a['id'],b['id']))
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
  if p['kind']=='gear':lim=(-40,40)
  _num(d.get('to'),'to',*lim);keyed.setdefault(p['id'],set()).add(d['beat'])
 beats=set(b for s in keyed.values() for b in s)
 if len(beats&{1,2,3,4,5,6})<3:raise RecipeError('motion must happen in at least 3 of beats 1-6')
 # Every driven part must have a driver chain that starts at a keyed part (no orphan motion).
 for l in links:
  if l['type']=='couple' and l['driver'] not in keyed and l['driver'] not in driven:raise RecipeError('link driver never moves')
  if l['type']=='mesh' and l['a'] not in keyed and l['a'] not in driven:raise RecipeError('mesh driver never moves')
 m=Machine(recipe);bad=m.bounds_violation()
 if bad:raise RecipeError(bad)
 return recipe

def _rot(points,pivot,angle):
 p=np.asarray(points,float).copy();c,s=math.cos(angle),math.sin(angle);x=p[:,0]-pivot[0];z=p[:,2]-pivot[1]
 p[:,0]=pivot[0]+x*c-z*s;p[:,2]=pivot[1]+x*s+z*c;return p

class Machine:
 """Generic machine with the same interface as the hand-built modules."""
 DARK=False
 def __init__(self,recipe):
  self.r=recipe;self.parts={p['id']:p for p in recipe['parts']};self.theme=recipe.get('theme','warm')
  self.DARK=self.theme=='dark';self.GROUND=THEMES[self.theme][2]
  self.drive=sorted(recipe['drive'],key=lambda d:d['beat']);self.links=recipe.get('links',[])
  self.order=self._order()
 def _order(self):
  keyed={d['part'] for d in self.drive};done=set(keyed);out=[];pend=list(self.links)
  for _ in range(len(pend)+1):
   for l in list(pend):
    src=l['a'] if l['type']=='mesh' else l['driver']
    if src in done:out.append(l);done.add(l['b'] if l['type']=='mesh' else l['driven']);pend.remove(l)
  return out
 def params(self,t,tl):
  b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7));val={}
  for pid,p in self.parts.items():
   if p['kind'] in PARAM:val[pid]=p.get('angle0',0.) if p['kind']=='lever' else p.get('pos0',0.) if p['kind']=='slider' else p.get('angle0',0.)
  keys={}
  for d in self.drive:keys.setdefault(d['part'],[]).append(d)
  for pid,ks in keys.items():
   cur=val[pid]
   for d in ks:
    if d['beat']<i:cur=d['to']
    elif d['beat']==i:cur=cur+(d['to']-cur)*ease(progress(t,b[i]))
   val[pid]=cur
  for l in self.order:
   if l['type']=='mesh':
    a,bb=self.parts[l['a']],self.parts[l['b']];val[bb['id']]=-val[a['id']]*a['teeth']/bb['teeth']+math.pi/bb['teeth']
   else:val[l['driven']]=l.get('offset',0)+l.get('ratio',1)*val[l['driver']]
  return i,val
 def slider_end(self,p,v):
  x,z=p['origin'];L,H=p['size'];return (x+v+L/2,z) if p.get('axis','x')=='x' else (x+L/2,z+v)
 def point_of(self,ref,val):
  p=self.parts[ref]
  if p['kind']=='slider':return self.slider_end(p,val[ref])
  if p['kind']=='lever':
   a=val[ref];return (p['pivot'][0]+p['length']*math.cos(a),p['pivot'][1]+p['length']*math.sin(a))
  return tuple(p.get('center',p.get('origin',(0,0))))
 def state(self,t,tl):
  i,val=self.params(t,tl);return dict(beat=i,values=val)
 def bounds_violation(self):
  fr=next(p for p in self.r['parts'] if p['kind']=='frame');x0,x1=fr['x']-fr['w']/2,fr['x']+fr['w']/2;z0,z1=fr['z'],fr['z']+fr['h']
  tl={'beats':[{'start':k*6,'end':(k+1)*6} for k in range(8)]}
  for t in np.linspace(0,47.9,97):
   i,val=self.params(float(t),tl)
   for pid,p in self.parts.items():
    pts=[]
    if p['kind']=='lever':pts=[tuple(p['pivot']),self.point_of(pid,val)]
    elif p['kind']=='slider':
     if abs(val[pid])>p['travel']+1e-6:return f'{pid} moves {abs(val[pid]):.2f}, beyond its travel {p["travel"]}'
     x,z=p['origin'];L,H=p['size'];e=self.slider_end(p,val[pid]);cx=e[0]-L/2 if p.get('axis','x')=='x' else x;cz=z if p.get('axis','x')=='x' else z+val[pid]
     pts=[(cx-L/2,cz-H/2),(cx+L/2,cz+H/2)]
    elif p['kind']=='gear':pts=[(p['center'][0]-p['r'],p['center'][1]-p['r']),(p['center'][0]+p['r'],p['center'][1]+p['r'])]
    for x,z in pts:
     if not (x0-.15<=x<=x1+.15 and z0-.15<=z<=z1+.15):return f'{pid} leaves the frame ({x:.1f},{z:.1f})'
  return None
 @functools.lru_cache(maxsize=1)
 def background(self):top,bot,_=THEMES[self.theme];return gradient(top,bot)
 def elevation(self,t,tl):return 5.5
 def focus(self,i):
  for d in self.drive:
   if d['beat']==i:
    p=self.parts[d['part']];c=p.get('pivot') or p.get('center') or p.get('origin');return (c[0],0,c[1]+ZC)
  fr=next(p for p in self.r['parts'] if p['kind']=='frame');return (fr['x'],0,fr['z']+fr['h']/2+ZC)
 def shot(self,i):
  i=min(i,7);fr=next(p for p in self.r['parts'] if p['kind']=='frame');mid=(fr['x'],0,fr['z']+fr['h']/2+ZC)
  wide=2.0*6/max(fr['w'],fr['h']*1.6)
  if i in (0,7):return (mid,wide,.32)
  f=self.focus(i);tg=(f[0]*.45+mid[0]*.55,0,f[2]*.5+mid[2]*.5)
  return (tg,wide*1.08,.28 if i%2 else -.22)
 def draw(self,s,t,tl,hidden=()):
  p=self.state(t,tl);val=p['values']
  for part in self.r['parts']:
   k=part['kind'];c=PALETTE[k]
   if k=='frame':
    x,z,w,h=part['x'],part['z']+ZC,part['w'],part['h']
    s.box((x,.55,z+h/2),(w,.12,h),tuple(int(v*.78) for v in c))
    for sx in (-1,1):s.box((x+sx*(w/2-.1),0,z+h/2),(.2,1.0,h),c)
    for sz in (0,h):s.box((x,0,z+sz),(w,1.0,.2),c)
   elif k=='lever':
    px,pz=part['pivot'];a=val[part['id']];L=part['length']
    s.box((px+L/2,-.05,pz+ZC),(L,.3,.26),c,transform=lambda q,px=px,pz=pz+ZC,a=a:_rot(q,(px,pz),a))
    s.cylinder((px,-.05,pz+ZC),.22,.5,PALETTE['pin'])
   elif k=='gear':
    cx,cz=part['center'];s.gear((cx,0,cz+ZC),part['r'],part['teeth'],val[part['id']],c)
   elif k=='slider':
    e=self.slider_end(part,val[part['id']]);L,H=part['size']
    if part.get('axis','x')=='x':s.box((e[0]-L/2,-.05,e[1]+ZC),(L,.34,H),c)
    else:s.box((part['origin'][0]+L/2-L/2,-.05,part['origin'][1]+ZC+val[part['id']]),(L,.34,H),c)
   elif k=='pin':s.cylinder((part['center'][0],-.1,part['center'][1]+ZC),part['r'],.5,c)
  for part in self.r['parts']:
   if part['kind']!='spring':continue
   a=part['a'];b=part['b']
   if isinstance(b,dict):b=self.point_of(b['part'],val)
   n=14;ax,az=a;bx,bz=b;dx,dz=bx-ax,bz-az;d=math.hypot(dx,dz) or 1e-6;nx,nz=-dz/d,dx/d;amp=min(.3,.18+.0*d);pts=[]
   for j in range(n+1):
    u=j/n;off=0 if j in (0,n) else amp*(1 if j%2 else -1);pts.append((ax+dx*u+nx*off,-.1,az+dz*u+nz*off+ZC))
   for q,r_ in zip(pts,pts[1:]):s.beam(q,r_,.035,PALETTE['spring'])
  return p
 @property
 def SHOTS(self):return [self.shot(i) for i in range(8)]
