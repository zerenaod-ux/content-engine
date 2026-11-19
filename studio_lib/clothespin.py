"""Rigid wooden jaws and a preloaded torsion spring; no invented hidden housing."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient,cylinder
Z=2.8
OPEN=.20
CLOTH_X=2.35
THICKNESS=.22
FLOOR=.30
GROUND=(222,210,179)
DARK=False

def inner_gap(angle,x=CLOTH_X):return 2*(x*math.tan(angle)+.08/math.cos(angle))
def stop_angle():
 lo,hi=0.,OPEN
 for _ in range(45):
  mid=(lo+hi)/2
  if inner_gap(mid)<THICKNESS:lo=mid
  else:hi=mid
 return (lo+hi)/2
STOP=stop_angle()

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,beat in enumerate(b) if t<beat['end']),7))
 if i<2:angle=0.
 elif i==2:angle=OPEN*ease(progress(t,b[2]))
 elif i<5:angle=OPEN
 elif i==5:angle=OPEN-(OPEN-STOP)*ease(progress(t,b[5]))
 else:angle=STOP
 inserted=ease(progress(t,b[4])) if i==4 else 1. if i>4 else 0.
 return dict(beat=i,angle=angle,gap=inner_gap(angle),spring_twist=.24+2*angle,cloth_x=CLOTH_X+(1-inserted)*3.4,inserted=inserted)

def transform(points,side,angle):
 p=np.asarray(points,float).copy();p[:,2]*=side;a=side*angle
 x=p[:,0].copy();z=p[:,2].copy();p[:,0]=x*math.cos(a)-z*math.sin(a);p[:,2]=Z+x*math.sin(a)+z*math.cos(a)
 return p
@functools.lru_cache(maxsize=1)
def background():return gradient((250,241,213),(226,218,181))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);a=p['angle'];i=p['beat']
 if 'jaws' not in hidden:
  for side,color in ((1,(197,146,83)),(-1,(172,119,61))):
   fn=lambda points,side=side:transform(points,side,a)
   profile=[(-3,.72),(-2.94,1.03),(-.55,1.03),(-.10,.75),(.30,.44),(2.54,.44),(2.60,.38),(2.60,.08),(.25,.08),(-.15,.33),(-.55,.67),(-2.94,.67)]
   for y in (-.425,.425):s.face(fn([(x,y,z) for x,z in profile]),color)
   for j,(x,z) in enumerate(profile):
    xx,zz=profile[(j+1)%len(profile)];s.face(fn([(x,-.425,z),(xx,-.425,zz),(xx,.425,zz),(x,.425,z)]),tuple(int(c*.86) for c in color))
   # Fine, attached wood grain and gripping ridges move rigidly with each jaw.
   for x in np.linspace(-2.8,-.5,7):s.beam((x,-.435,.80),(x+.19,-.435,.84),.012,(130,86,46),transform=fn)
   for x in np.linspace(1.95,2.55,7):s.beam((x,-.38,.082),(x,.38,.082),.012,(125,84,47),transform=fn)
 cylinder(s,(0,0,Z),.25,1.0,(91,103,108),'y',n=20)
 if 'spring' not in hidden:
  turn=6*math.pi+2*a
  points=[(.35*math.cos(phi),-.55-.38+.76*j/66,Z+.35*math.sin(phi)) for j,phi in enumerate(np.linspace(-a,turn-a,67))]
  for x,y in zip(points,points[1:]):s.beam(x,y,.035,(164,178,179))
  for side,end in ((-1,points[0]),(1,points[-1])):
   target=transform([(-.95,-.55,1.035)],side,a)[0]
   s.beam(end,target,.035,(168,181,178));s.beam(target,target+np.array([0,.16,0]),.035,(168,181,178))
 if i>=4 and 'cloth' not in hidden:
  x=p['cloth_x']
  ribbon=[(x,.11),(x+1.4,.11),(x+1.65,.04),(x+1.78,-.20),(x+1.78,-1.40),(x+1.70,-1.40),(x+1.70,-.20),(x+1.58,-.05),(x+1.35,-.11),(x,-.11)]
  for y in (-.60,.60):s.face([(xx,y,Z+zz) for xx,zz in ribbon],(56,126,159))
  for j,(xx,zz) in enumerate(ribbon):
   nx,nz=ribbon[(j+1)%len(ribbon)];s.face([(xx,-.60,Z+zz),(nx,-.60,Z+nz),(nx,.60,Z+nz),(xx,.60,Z+zz)],(69,145,177))
  for y in np.linspace(-.5,.5,7):s.beam((x+.02,y,Z+.115),(x+1.35,y,Z+.115),.008,(155,196,205))
 if i in (2,3,4) and 'input' not in hidden:
  for side in (-1,1):
   q=transform([(-2.1,-.62,1.2)],side,a)[0];tail=q+np.array([0,0,.6*side]);s.beam(tail,q,.04,(79,132,161))
   s.beam(q,q+np.array([.15,0,.2*side]),.035,(79,132,161));s.beam(q,q+np.array([-.15,0,.2*side]),.035,(79,132,161))
 return p
SHOTS=[((.3,0,2.8),1.2,.32),((-.2,0,2.8),2.0,.26),((-.65,0,2.8),1.65,.26),((1.1,0,2.8),1.9,.28),((2.1,0,2.7),1.8,.30),((.2,0,2.8),1.75,.28),((2.1,0,2.7),1.95,.28),((.3,0,2.8),1.2,.32)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 5.5
