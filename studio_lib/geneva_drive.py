"""Geneva drive: a continuously turning driver pin enters a slot of a four-slot wheel and moves it exactly a quarter turn, then leaves; the wheel waits locked.
Exact kinematics: slot angle follows atan2(a sin(alpha), c - a cos(alpha)). Teaching model."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
CD=2.45;A=CD*math.sin(math.pi/4);RO=1.95;RI=.95;HW=.2;ZC=3.0;DX=-CD/2;GX=CD/2

def beta(al):return math.atan2(A*math.sin(al),CD-A*math.cos(al))
def driven_angle(turn):
 n=math.floor((turn+math.pi)/(2*math.pi));al=turn-2*math.pi*n-math.pi
 al=((turn+math.pi)%(2*math.pi))-math.pi
 if al<-math.pi/4:step=0.
 elif al<=math.pi/4:step=beta(al)+math.pi/4
 else:step=math.pi/2
 return -(math.pi/2)*n-step
def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 turn=2*math.pi*(e[2]+e[3])+2*math.pi*e[5]-2*math.pi*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),turn=turn,wheel=driven_angle(turn))
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def outline(psi):
 pts=[]
 dout=math.asin(HW/RO);din=math.asin(HW/RI)
 for k in range(4):
  c=psi+math.pi/4+k*math.pi/2+math.pi/4*0  # slot centre directions at psi + k*pi/2 (slots point at 0, 90, ...)
 sl=[psi+k*math.pi/2 for k in range(4)]
 for k in range(4):
  a0=sl[k]+dout;a1=sl[(k+1)%4]+(2*math.pi if k==3 else 0)-dout
  a1=sl[k]+math.pi/2-dout
  for q in range(7):
   a=a0+(a1-a0)*q/6;pts.append((a,RO))
  a=sl[k]+math.pi/2
  pts.append((a-din,RI));pts.append((a+din,RI))
 return pts
def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut'];beat=p['beat'];psi=p['wheel']+math.pi  # slot directions at ang psi
 pin=(DX+A*math.cos(p['turn']),ZC+A*math.sin(p['turn']))
 if 'frame' not in hidden:
  P.plate(s,(0,.7,ZC-.1),(7.6,.2,5.6),hb.PLATE,tiles=(8,6))
  hb.block(s,(0,.1,.45),(7.0,.9,.5),hb.DARK,.07)
 if 'wheel' not in hidden:
  pts=[(GX+r*math.cos(a),ZC+r*math.sin(a)) for a,r in outline(psi)]
  front=[(x,-.22,z) for x,z in pts];rear=[(x,.22,z) for x,z in pts]
  s.face(rear,hb.sh(hb.STEEL,.55))
  for j in range(len(pts)):
   k=(j+1)%len(pts);mid=math.atan2((pts[j][1]+pts[k][1])/2-ZC,(pts[j][0]+pts[k][0])/2-GX)
   s.face([front[j],front[k],rear[k],rear[j]],hb.sh(hb.STEEL,.62+.35*math.cos(mid-1.0)))
  s.face(front,hb.STEEL)
  P.tube(s,(GX,-.3,ZC),(GX,.3,ZC),.34,hb.BRASS,n=18,chamfer=.05)
  P.annulus(s,(GX,0,ZC),RI-.05,.42,-.235,hb.sh(hb.STEEL,.82),angle=psi)
 if 'driver' not in hidden:
  th=p['turn']
  P.disc(s,(DX,0,ZC),1.35,-.22,hb.sh(hb.WARM,.9),n=48,angle=th)
  P.annulus(s,(DX,0,ZC),1.3,1.12,-.25,hb.sh(hb.WARM,1.1),angle=th)
  hb.bar(s,(DX,ZC),pin,.42,.2,-.30,hb.WARM)
  P.tube(s,(DX,-.35,ZC),(DX,.3,ZC),.3,hb.BRASS,n=18,chamfer=.05)
 if 'pin' not in hidden:
  P.tube(s,(pin[0],-.28,pin[1]),(pin[0],-.62,pin[1]),.15,hb.RED,n=14,chamfer=.03)
 if beat in (2,3,5):
  r=1.75;a0=math.radians(100);pts=[(DX+r*math.cos(a0+k*.14),-.9,ZC+r*math.sin(a0+k*.14)) for k in range(5)]
  for a,b in zip(pts,pts[1:]):s.beam(a,b,.04,hb.ARROW)
  hb.arrow(s,pts[-2],pts[-1])
 if 'cover' not in hidden and cut<.99:
  zc=ZC+7.0*cut;hb.block(s,(GX,-.5,zc),(3.0,.14,3.0),hb.COVER,.06)
  P.rivets(s,[(GX-1.2,zc+1.2),(GX+1.2,zc+1.2),(GX-1.2,zc-1.2),(GX+1.2,zc-1.2)],.06,hb.sh(hb.STEEL,.8),y=-.6)
 return p
SHOTS=[((0, 0, 3.0), 1.6, 0.3), ((0.8, 0, 3.0), 1.5, 0.3), ((0, 0, 3.0), 1.72, -0.45), ((0.3, 0, 3.0), 2.64, 0.8), ((0, 0, 3.0), 1.8, 0.2), ((0, 0, 3.0), 1.72, -0.7), ((0, 0, 3.0), 1.65, 0.5), ((0, 0, 3.0), 1.6, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
