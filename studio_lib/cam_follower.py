"""Cam and follower: an egg-shaped cam turns on a shaft, a flat-footed follower rides on it and a spring keeps it pressed down.
The cam contour is built from its support function h(a)=R0+L/2*(1+cos a), so the follower height equals h exactly (no gap, no overlap). Teaching model, no engine shown."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
CZ=1.55;R0=.62;LF=1.05;GZ=4.75

def h(a):return R0+LF/2*(1+math.cos(a))
def dh(a):return -LF/2*math.sin(a)
def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 turn=2*math.pi*e[2]+math.pi*e[3]+2*math.pi*e[5]-math.pi*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),turn=turn,lift=h(math.pi/2-turn))
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def contour(turn,n=72):
 pts=[]
 for k in range(n):
  a=2*math.pi*k/n;x=h(a)*math.cos(a)-dh(a)*math.sin(a);z=h(a)*math.sin(a)+dh(a)*math.cos(a)
  r=math.hypot(x,z);q=math.atan2(z,x)+turn;pts.append((r*math.cos(q),CZ+r*math.sin(q)))
 return pts
def draw(s,t,tl,hidden=()):
 p=state(t,tl);turn=p['turn'];cut=p['cut'];beat=p['beat'];tap=CZ+p['lift']
 if 'frame' not in hidden:
  P.plate(s,(0,.6,3.4),(3.8,.2,6.4),hb.PLATE,tiles=(6,10))
  hb.block(s,(0,.1,.45),(4.6,.95,.5),hb.DARK,.07)
  hb.block(s,(0,.15,GZ),(1.5,.8,.6),hb.sh(hb.DARK,1.1),.06)
  P.rivets(s,[(x,.45) for x in (-1.9,-.9,.9,1.9)],.06,hb.BRASS,y=-.4)
 if 'cam' not in hidden:
  pts=contour(turn);front=[(x,-.12,z) for x,z in pts];rear=[(x,.12,z) for x,z in pts]
  s.face(rear,hb.MID)
  for k in range(len(pts)):
   j=(k+1)%len(pts);m=math.atan2(pts[k][1]-CZ,pts[k][0])
   s.face([front[k],front[j],rear[j],rear[k]],tuple(int(c*(.72+.26*math.cos(m-.9))) for c in hb.WARM))
  s.face(front,hb.sh(hb.WARM,.95))
  P.tube(s,(0,-.1,CZ),(0,-.5,CZ),.2,hb.STEEL,n=14,chamfer=.03)
  px=.3*math.cos(turn+1.1);pz=CZ+.3*math.sin(turn+1.1);P.tube(s,(px,-.12,pz),(px,-.26,pz),.07,hb.RED,n=10)
 if 'follower' not in hidden:
  hb.block(s,(0,0,tap+.1),(1.1,.7,.2),hb.STEEL,.04)
  hb.block(s,(0,0,tap+1.9),(.26,.26,3.5),hb.sh(hb.STEEL,.92),.03)
  hb.block(s,(0,-.02,tap+1.0),(.8,.5,.2),hb.BRASS,.04)
  hb.block(s,(0,0,tap+3.7),(.9,.6,.3),hb.RED,.05)
 if 'spring' not in hidden:
  P.spring(s,(0,-.42,tap+1.12),(0,-.42,GZ-.3),6,.28,.04,hb.sh(hb.STEEL,.85))
 if beat in (2,3,5):hb.arrow(s,(.0,-.65,CZ+1.95),(.0,-.65,CZ+1.95),hb.WARM,.06) if False else None
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(-1.35*sg,-.7,CZ-1.15),(1.35*sg,-.7,CZ-1.15),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=3.55+7.0*cut;hb.block(s,(0,-.58,zc),(3.2,.14,2.3),hb.COVER,.06)
  P.rivets(s,[(-1.4,zc+.85),(1.4,zc+.85),(-1.4,zc-.85),(1.4,zc-.85)],.06,hb.sh(hb.STEEL,.8),y=-.68)
 return p
SHOTS=[((0, 0, 3.6), 2.65, 0.3), ((0, 0, 3.6), 1.4, 0.3), ((0, 0, 3.6), 1.49, -0.45), ((0, 0, 2.6), 2.28, 0.8), ((0, 0, 3.6), 1.56, 0.2), ((0, 0, 3.6), 1.49, -0.7), ((0, 0, 3.6), 1.43, 0.5), ((0, 0, 3.6), 2.65, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
