"""Chain and sprockets: a pedal crank turns a big 16-tooth sprocket, the chain carries the motion to a small 8-tooth sprocket that spins twice as fast.
Exact: both sprockets share the chain pitch (pitch radius = p/(2 sin(pi/N))), chain path is the true outer tangent loop, small angle = big angle * R1/R2. Teaching model, no bicycle shown."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
PITCH=.40;N1=16;N2=8;R1=PITCH/(2*math.sin(math.pi/N1));R2=PITCH/(2*math.sin(math.pi/N2))
C1=(-1.35,2.7);C2=(1.45,2.7);D=C2[0]-C1[0];PHI=math.asin((R1-R2)/D);LT=math.sqrt(D*D-(R1-R2)**2)
A1=R2*(math.pi-2*PHI);A2=R1*(math.pi+2*PHI);TOTAL=2*LT+A1+A2;NL=round(TOTAL/PITCH)

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 turn=-math.pi*e[2]-math.pi*e[3]-2*math.pi*e[5]+math.pi*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),turn=turn)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def pos(s):
 """Point on the chain loop at arc length s, travelling clockwise (top run moves right)."""
 s%=TOTAL;nx,nz=math.sin(PHI),math.cos(PHI)
 if s<LT:
  q=s/LT;a=(C1[0]+R1*nx,C1[1]+R1*nz);b=(C2[0]+R2*nx,C2[1]+R2*nz);return (a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q)
 s-=LT
 if s<A1:
  ang=math.pi/2-PHI-s/R2;return (C2[0]+R2*math.cos(ang),C2[1]+R2*math.sin(ang))
 s-=A1
 if s<LT:
  q=s/LT;a=(C2[0]+R2*nx,C2[1]-R2*nz);b=(C1[0]+R1*nx,C1[1]-R1*nz);return (a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q)
 s-=LT;ang=-(math.pi/2-PHI)-s/R1;return (C1[0]+R1*math.cos(ang),C1[1]+R1*math.sin(ang))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);th=p['turn'];cut=p['cut'];beat=p['beat'];run=-R1*th
 if 'frame' not in hidden:
  P.plate(s,(0,.6,2.9),(6.4,.2,5.4),hb.PLATE,tiles=(10,8))
  hb.block(s,(0,.15,.45),(6.4,.95,.5),hb.DARK,.07)
  P.rivets(s,[(x,.45) for x in (-2.7,-1.4,0,1.4,2.7)],.06,hb.BRASS,y=-.4)
 if 'sprockets' not in hidden:
  P.gear(s,(C1[0],0,C1[1]),R1,N1,th,.26,hb.BRASS,y=0.,tip=.12,root=.14,hub=.28,holes=0,hole_r=.1,mark=True)
  P.gear(s,(C2[0],0,C2[1]),R2,N2,2*th,.26,hb.sh(hb.WARM,.95),y=0.,tip=.12,root=.14,hub=.28,holes=0,hole_r=.1,mark=True)
 if 'chain' not in hidden:
  for k in range(NL):
   sk=k*TOTAL/NL+run;a=pos(sk-.12);b=pos(sk+.12)
   hb.bar(s,a,b,.15,.12,-.17,hb.sh(hb.STEEL,.78+.22*(k%2)),eyes=False)
 if 'crank' not in hidden:
  ang=th+.9;tipx=C1[0]+1.35*math.cos(ang);tipz=C1[1]+1.35*math.sin(ang)
  hb.bar(s,C1,(tipx,tipz),.3,.14,-.34,hb.RED)
  P.tube(s,(tipx,-.3,tipz),(tipx,-.62,tipz),.17,hb.BRASS,n=12,chamfer=.03)
  P.tube(s,(C1[0],-.3,C1[1]),(C1[0],-.55,C1[1]),.16,hb.STEEL,n=12,chamfer=.03)
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(C1[0]-.5*sg+.8,-.75,.95),(C1[0]+.9*sg+.8,-.75,.95),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=2.9+7.0*cut;hb.block(s,(0,-.7,zc),(4.4,.14,1.0),hb.COVER,.06)
  P.rivets(s,[(-1.9,zc),(1.9,zc)],.06,hb.sh(hb.STEEL,.8),y=-.8)
 return p
SHOTS=[((0, 0, 2.9), 1.85, 0.3), ((0, 0, 2.9), 1.5, 0.3), ((0, 0, 2.9), 1.72, -0.45), ((0, 0, 2.9), 1.8, 0.8), ((0, 0, 2.9), 1.8, 0.2), ((0, 0, 2.9), 1.72, -0.7), ((0, 0, 2.9), 1.65, 0.5), ((0, 0, 2.9), 1.85, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
