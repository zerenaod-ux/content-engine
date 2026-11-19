"""Meridional ray model of a straight step-index fibre; not wave optics or a bent cable."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import cylinder,sphere,background as gradient,path_point
FLOOR=.30;GROUND=(37,56,72);DARK=True
Z=2.1;RADIUS=.38;N_CORE=1.49;N_CLAD=1.42;AXIAL=math.radians(12)
CRITICAL=math.asin(N_CLAD/N_CORE)

def ray_path():
 points=[(-5.5,0,Z)];x=-5.5;z=0.;direction=1
 while x<5.5-1e-9:
  boundary=direction*RADIUS;run=(boundary-z)/(direction*math.tan(AXIAL))
  if x+run>=5.5:
   z+=direction*math.tan(AXIAL)*(5.5-x);x=5.5
  else:x+=run;z=boundary;direction*=-1
  points.append((x,0,Z+z))
 return points
PATH=ray_path();LENGTH=sum(np.linalg.norm(np.subtract(b,a)) for a,b in zip(PATH,PATH[1:]));FIRST=np.linalg.norm(np.subtract(PATH[1],PATH[0]))/LENGTH
SECOND=(np.linalg.norm(np.subtract(PATH[2],PATH[1]))/LENGTH)+FIRST

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 front=0. if i<2 else FIRST*ease(progress(t,b[2])) if i==2 else FIRST+(SECOND-FIRST)*ease(progress(t,b[3])) if i==3 else SECOND+(1-SECOND)*ease(progress(t,b[4])) if i==4 else 1.
 return dict(beat=i,front=front,output=float(front>=1.-1e-6),cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7]))))
@functools.lru_cache(maxsize=1)
def background():return gradient((17,32,48),(45,67,81))
def tube_half(s,radius,front,lift,color):
 angles=np.linspace(-math.pi,0,29) if front else np.linspace(0,math.pi,29)
 for a,b in zip(angles,angles[1:]):
  s.face([(x,radius*math.sin(q),Z+radius*math.cos(q)+lift) for x,q in ((-5.5,a),(5.5,a),(5.5,b),(-5.5,b))],color)
def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut'];i=p['beat']
 for name,radius,color in (('jacket',.82,(51,102,139)),('cladding',.56,(100,153,173)),('core',RADIUS,(66,116,143))):
  if name in hidden:continue
  # Rear halves stay; front halves lift for an explicitly enlarged section view.
  tube_half(s,radius,False,0,color);tube_half(s,radius,True,6*cut,color)
 if cut>.05:
  for dz in (-RADIUS,RADIUS):s.beam((-5.5,0,Z+dz),(5.5,0,Z+dz),.012,(165,204,211))
 for x in (-5.8,5.8):cylinder(s,(x,0,Z),.89,.40,(118,143,159),'x',n=24)
 if 'source' not in hidden:
  s.box((-6.40,0,Z),(.80,1.45,1.45),(61,87,108));cylinder(s,(-5.96,0,Z),.29,.10,(224,181,88) if i>=2 else (117,137,142),'x',n=16)
 if 'detector' not in hidden:
  s.box((6.40,0,Z),(.80,1.45,1.45),(68,100,116));cylinder(s,(6.40,-.76,Z),.16,.09,(237,200,106) if p['output'] else (101,129,139),'y',n=16)
 if i>=2 and 'rays' not in hidden:
  remaining=p['front']*LENGTH
  for a,b in zip(PATH,PATH[1:]):
   length=np.linalg.norm(np.subtract(b,a));used=min(remaining,length)
   if used>.001:s.beam(a,np.asarray(a)+(np.subtract(b,a))*used/length,.018,(241,197,98))
   remaining-=used
   if remaining<=0:break
  if 'pulse' not in hidden:
   positions=[p['front']] if i<5 else [(t*.20+k/4)%1 for k in range(4)]
   for q in positions:sphere(s,path_point(PATH,q),.055,(255,229,164),n=8,bands=4)
 return p
SHOTS=[((0,0,Z),.78,.30),((0,0,Z),1.0,.35),((-4.0,0,Z),2.2,.35),((-2.8,0,Z),2.35,.35),((.1,0,Z),1.45,.30),((0,0,Z),1.15,.25),((5.7,0,Z),2.0,.35),((0,0,Z),.78,.30)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
