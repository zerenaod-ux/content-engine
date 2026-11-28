"""Rack-and-pinion steering: a steering wheel turns a small pinion gear whose teeth push a toothed bar (the rack) sideways.
Exact mesh: the rack moves R*angle, tooth phase is locked to the pinion, so teeth never slip. Teaching model, no car shown."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
C=(0.,3.1);R=.95;N=14;PA=2*math.pi/N;ZP=C[1]-R;ANG0=-math.pi/2-.5*PA

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 th=1.0*e[2]+.8*e[3]-1.9*e[5]-.9*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),turn=th,slide=R*th)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);th=p['turn'];cut=p['cut'];beat=p['beat'];off=R*th
 if 'frame' not in hidden:
  hb.block(s,(0,.62,ZP-.7),(9.0,.34,2.9),hb.PLATE,.06)
  for x in (-2.6,2.6):hb.block(s,(x,0,ZP-.32),(1.1,.95,.95),hb.DARK,.07)
  P.rivets(s,[(x,ZP-.32) for x in (-2.9,-2.3,2.3,2.9)],.05,hb.BRASS,y=-.49)
 if 'rack' not in hidden:
  phase=C[0]+R*(-ANG0*0)+off-0.0
  hb.rack(s,-4.0+off,4.0+off,ZP,R*PA,C[0]+off+0*ANG0,0,.62,hb.STEEL)
  for sgn in (-1,1):
   x=sgn*(4.0)+off;hb_end=x+sgn*.9
   P.tube(s,(x,0,ZP-.25),(hb_end,0,ZP-.25),.12,hb.sh(hb.STEEL,.9),n=12,chamfer=.03)
   P.tube(s,(hb_end,-.14,ZP-.25),(hb_end,.14,ZP-.25),.22,hb.BRASS,n=16,chamfer=.04)
 if 'pinion' not in hidden:
  P.gear(s,(C[0],0,C[1]),R,N,ANG0+th,.50,hb.BRASS,y=0.,tip=.12,root=.14,hub=.28,holes=0,hole_r=.1,mark=True)
 if 'wheel' not in hidden:
  hb.wheel_spokes(s,C,1.85,.42,-.78,ANG0+th,3,hb.RED)
  P.tube(s,(C[0],-.78,C[1]),(C[0],-.2,C[1]),.2,hb.STEEL,n=14,chamfer=.03)
 if beat in (2,3,5,6):
  sg=1 if beat in (2,3) else -1
  r=2.35;a0=.9;pts=[(C[0]+r*math.cos(a0+k*.12*sg),-.95,C[1]+r*math.sin(a0+k*.12*sg)) for k in range(5)]
  for a,b in zip(pts,pts[1:]):s.beam(a,b,.04,hb.ARROW)
  hb.arrow(s,pts[-2],pts[-1])
 if 'cover' not in hidden and cut<.99:
  zc=ZP+.15+7.0*cut
  hb.block(s,(0,-.42,zc),(3.0,.14,1.5),hb.COVER,.06)
  P.rivets(s,[(-1.3,zc+.5),(1.3,zc+.5),(-1.3,zc-.5),(1.3,zc-.5)],.06,hb.sh(hb.STEEL,.8),y=-.52)
 return p
SHOTS=[((0, 0, 2.7), 1.3, 0.3), ((0, 0, 3.0), 1.4, 0.3), ((0, 0, 2.9), 1.72, -0.45), ((0, 0, 2.3), 3.0, 0.8), ((0, 0, 2.8), 1.92, 0.2), ((0, 0, 2.9), 1.72, -0.7), ((0, 0, 2.9), 1.65, 0.5), ((0, 0, 2.7), 1.3, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
