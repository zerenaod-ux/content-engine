"""Worm gear: a threaded worm turned by a hand crank pushes the teeth of a wheel one at a time, so twelve turns of the worm make one turn of the wheel.
Exact: thread pitch equals the wheel's circular pitch (2*pi*R/N), ridges advance pitch per worm turn, and the wheel turns by turn/N. Teaching model."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
N=12;R=1.5;PITCH=2*math.pi*R/N;WC=(0.,3.5);WZ=WC[1]-R+.12

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 turn=2*math.pi*(2.5*e[2]+1.5*e[3]+2.5*e[5]-1.5*e[6])
 return dict(beat=i,cut=e[1]*(1-e[7]),turn=turn)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);turn=p['turn'];cut=p['cut'];beat=p['beat']
 if 'frame' not in hidden:
  hb.block(s,(0,.25,.45),(7.0,.95,.5),hb.DARK,.07)
  P.plate(s,(0,.75,3.0),(6.4,.14,5.4),hb.PLATE,tiles=(10,8))
  hb.block(s,(-2.3,.1,WZ-.35),(.5,.8,.9),hb.sh(hb.DARK,1.15),.05)
  hb.block(s,(2.3,.1,WZ-.35),(.5,.8,.9),hb.sh(hb.DARK,1.15),.05)
  P.rivets(s,[(x,.45) for x in (-3.0,-1.5,0,1.5,3.0)],.06,hb.BRASS,y=-.4)
 if 'wheel' not in hidden:
  P.gear(s,(WC[0],0,WC[1]),R,N,turn/N,.34,hb.BRASS,y=.12,tip=.12,root=.14,hub=.3,holes=5,hole_r=.16,mark=True)
 if 'worm' not in hidden:
  hb.thread(s,-2.5,2.5,WZ,-.28,.34,turn/(2*math.pi)*PITCH,PITCH,hb.STEEL)
  for sx in (-2.5,2.5):P.tube(s,(sx,-.28,WZ),(sx+.0,-.28,WZ),.0,hb.MID,n=4) if False else None
 if 'crank' not in hidden:
  ang=turn;cy=-.28+.0
  hb.block(s,(-2.7,cy,WZ),(.3,.4,.4),hb.STEEL,.04)
  q=(.0,.9*math.cos(ang),.9*math.sin(ang))
  s.beam((-2.85,cy,WZ),(-2.85,cy+q[1],WZ+q[2]),.15,hb.RED)
  P.tube(s,(-2.85,cy+q[1],WZ+q[2]),(-3.35,cy+q[1],WZ+q[2]),.2,hb.BRASS,n=12,chamfer=.03)
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(-.9*sg,-.8,.95),(.9*sg,-.8,.95),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=3.9+7.0*cut;hb.block(s,(0,-.5,zc),(3.4,.14,3.2),hb.COVER,.06)
  P.rivets(s,[(-1.4,zc+1.2),(1.4,zc+1.2),(-1.4,zc-1.2),(1.4,zc-1.2)],.06,hb.sh(hb.STEEL,.8),y=-.6)
 return p
SHOTS=[((0, 0, 2.9), 1.85, 0.3), ((0, 0, 2.9), 1.2, 0.3), ((0, 0, 2.9), 1.38, -0.45), ((0, 0, 2.0), 1.92, 0.8), ((0, 0, 2.9), 1.44, 0.2), ((0, 0, 2.9), 1.38, -0.7), ((0, 0, 2.9), 1.32, 0.5), ((0, 0, 2.9), 1.85, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
