"""Lever: a beam rests on a fulcrum one third along its length; a push down on the long arm lifts a heavy weight hanging from the short arm.
Exact: long arm 4, short arm 2, so the weight rises exactly half as far as the hand end falls (rise = 2 sin a, fall = 4 sin a). Teaching model."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
FZ=3.1;SA=2.0;LA=4.0;ROPE=1.5

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 ang=.16*e[2]+.12*e[3]+.14*e[5]-.14*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),ang=ang)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);a=p['ang'];cut=p['cut'];beat=p['beat']
 L=(-SA*math.cos(a),FZ+SA*math.sin(a));R=(LA*math.cos(a),FZ-LA*math.sin(a));F=(0,FZ)
 if 'base' not in hidden:
  hb.block(s,(0,.2,.45),(8.4,.95,.5),hb.DARK,.07)
  P.plate(s,(0,.7,3.0),(8.0,.14,5.2),hb.PLATE,tiles=(10,8))
  P.rivets(s,[(x,.45) for x in (-3.6,-1.8,0,1.8,3.6)],.06,hb.BRASS,y=-.4)
  P.rivets(s,[(x,.92) for x in (-3.6,-1.8,0,1.8,3.6)],.06,hb.STEEL,y=.5)
 if 'fulcrum' not in hidden:
  for sx in (-.75,.75):hb.bar(s,(sx,.7),(0,FZ-.25),.38,.18,.12,hb.sh(hb.MID,1.0),eyes=False)
  hb.block(s,(0,.12,.75),(1.8,.8,.28),hb.sh(hb.DARK,1.15),.05)
  hb.pin(s,0,FZ,0,.2,hb.BRASS,.8)
 if 'beam' not in hidden:
  hb.bar(s,L,R,.42,.26,-.06,hb.STEEL)
  for k in range(1,6):
   q=(L[0]+(R[0]-L[0])*k/6,L[1]+(R[1]-L[1])*k/6);hb.pin(s,q[0],q[1],-.2,.04,hb.sh(hb.MID,.7),.12)
  hb.block(s,(R[0]+.1,-.08,R[1]),(.55,.4,.5),hb.RED,.06)
 if 'load' not in hidden:
  lz=L[1]-ROPE
  P.tube(s,(L[0],-.04,L[1]),(L[0],-.04,lz+.5),.04,hb.sh(hb.STEEL,.8),n=8)
  hb.block(s,(L[0],-.04,lz),(1.2,.9,.85),hb.BRASS,.07)
  hb.block(s,(L[0],-.04,lz-.62),(1.5,1.0,.4),hb.sh(hb.BRASS,.85),.06)
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(R[0]+.1,-.5,R[1]+1.9-(1.2 if sg<0 else 0)),(R[0]+.1,-.5,R[1]+(.9 if sg>0 else 1.9)),hb.ARROW,.05) if sg>0 else hb.arrow(s,(R[0]+.1,-.5,R[1]+.9),(R[0]+.1,-.5,R[1]+1.9),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=1.2+7.0*cut;hb.block(s,(0,-.6,zc),(3.6,.14,1.0),hb.COVER,.06)
  P.rivets(s,[(-1.5,zc),(1.5,zc)],.06,hb.sh(hb.STEEL,.8),y=-.7)
 return p
SHOTS=[((0.5, 0, 3.2), 1.65, 0.3), ((0, 0, 2.6), 1.5, 0.3), ((0.5, 0, 3.2), 1.2, 0.3), ((0.8, 0, 3.0), 1.3, 0.3), ((0.5, 0, 3.2), 1.2, 0.3), ((0.5, 0, 3.2), 1.2, 0.3), ((0.5, 0, 3.2), 1.2, 0.3), ((0.5, 0, 3.2), 1.65, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
