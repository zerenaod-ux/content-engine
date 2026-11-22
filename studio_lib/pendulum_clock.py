"""Weight-driven pendulum clock with an anchor escapement. Engine-owned geometry; simplified, not a horological drawing.
The pendulum swings once every 2 s (one tick each second); the anchor lets the escape wheel advance one tooth per swing;
a falling weight supplies the energy; the seconds hand rides on the escape wheel arbor and turns once a minute."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient,cylinder
FLOOR=.30;GROUND=(226,215,196);DARK=False
PERIOD=2.0;AMP=math.radians(9);TEETH=30
P=np.array([0,-.30,4.45]);W=np.array([0,-.30,3.60]);R=.55;G=np.array([-1.0,-.30,3.60])

def ramp(x,a,b):return max(0.,min(1.,(x-a)/(b-a)))
def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 th=AMP*math.sin(2*math.pi*t/PERIOD);f=2*t/PERIOD;k=math.floor(f);step=k+ramp(f-k,0,.12)
 turn=step*math.pi/TEETH
 cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7])))
 return dict(beat=i,theta=th,turn=turn,weight_z=2.45-.012*t,cut=cut,tick=1-ramp(f-k,0,.2))
@functools.lru_cache(maxsize=1)
def background():return gradient((246,238,224),(214,198,172))
def rot(pt,c,a):
 d=np.array(pt)-c;ca,sa=math.cos(a),math.sin(a)
 return c+np.array([d[0]*ca-d[2]*sa,d[1],d[0]*sa+d[2]*ca])
def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut']
 wood,dark,brass,steel,cream,orange=(122,86,62),(84,60,46),(214,172,88),(110,128,138),(238,231,212),(221,102,57)
 s.box((0,.45,3.1),(3.6,.12,6.0),wood)
 s.box((0,0,.15),(3.8,1.2,.3),dark);s.box((0,0,6.2),(3.8,1.2,.3),dark)
 for x in (-1.8,1.8):s.box((x,0,3.15),(.2,1.1,5.9),dark)
 s.box((-.45,.25,3.85),(2.6,.06,1.7),(196,160,92))
 if 'weight' not in hidden:
  wz=p['weight_z'];s.beam((G[0]-.3,-.25,3.6),(G[0]-.3,-.25,wz+.45),.02,(60,60,60))
  cylinder(s,(G[0]-.3,-.25,wz),.26,.7,(70,84,92),'z',n=20)
  cylinder(s,(G[0],-.18,3.6),.3,.25,(150,120,70),'y',n=16)
 s.gear(tuple(G+[0,.05,0]),.45,24,-p['turn']*R/.45,brass)
 if 'escape' not in hidden:s.gear(tuple(W),R,TEETH,-p['turn'],(230,190,100))
 for k in range(60):
  a=k/60*2*math.pi;r1=.66 if k%5 else .62
  s.beam((W[0]+r1*math.sin(a),-.52,W[2]+r1*math.cos(a)),(W[0]+.74*math.sin(a),-.52,W[2]+.74*math.cos(a)),.01 if k%5 else .018,(60,72,80))
 ha=-p['turn']   # same arbor as the escape wheel: 60 ticks per turn
 s.beam((W[0],-.56,W[2]),(W[0]+.6*math.sin(ha),-.56,W[2]+.6*math.cos(ha)),.025,orange)
 cylinder(s,(W[0],-.57,W[2]),.05,.04,orange,'y',n=12)
 if 'anchor' not in hidden:
  for side in (-1,1):
   tip=np.array([side*R*math.sin(math.radians(38)),-.42,W[2]+R*math.cos(math.radians(38))+.02]);tip=rot(tip,P,p['theta']*.9)
   s.beam(tuple(P+[0,-.12,0]),tuple(tip),.045,steel)
   s.box(tuple(tip+[0,0,-.03]),(.12,.1,.1),(240,120,70) if p['tick']>.5 and side==(1 if p['theta']>0 else -1) else (200,90,60))
  cylinder(s,tuple(P+[0,-.12,0]),.08,.12,steel,'y',n=12)
 if 'pendulum' not in hidden:
  bot=rot(P+[0,-.1,-3.0],P+[0,-.1,0],p['theta'])
  s.beam(tuple(P+[0,-.1,0]),tuple(bot),.03,(90,100,108));cylinder(s,tuple(bot),.36,.16,brass,'y',n=28)
 if 'door' not in hidden and cut<.99:
  dz=3.85+cut*3.0
  for a,b in (((-1.5,-.62,dz-.95),(1.5,-.62,dz-.95)),((-1.5,-.62,dz+.95),(1.5,-.62,dz+.95)),((-1.5,-.62,dz-.95),(-1.5,-.62,dz+.95)),((1.5,-.62,dz-.95),(1.5,-.62,dz+.95))):s.beam(a,b,.06,dark)
  s.box((0,-.6,dz),(2.9,.02,1.85),cream)
 return p
SHOTS=[((0,0,3.2),1.05,.30),((0,-.1,2.0),1.9,.40),((0,-.35,3.95),3.6,.30),((.3,-.4,4.1),6.5,.28),((-.5,-.35,3.6),3.4,.35),((-1.2,-.25,2.9),2.6,.45),((0,-.5,3.6),4.6,.22),((0,0,3.2),1.05,.30)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
