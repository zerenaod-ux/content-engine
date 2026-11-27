"""Movable pulley: one rope is tied to the beam, runs down round a pulley that carries the weight, then up over a fixed pulley to a handle.
Two strands share the load, so the handle moves exactly twice as far as the weight. Exact rope geometry: strands are tangent to both wheels. Teaching model."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
RM=.6;RF=.9;XM=RM;XF=2*RM-RF;ZF=6.0;ZM0=3.5;ROPE=(214,190,140)

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 h=.22*e[2]+.18*e[3]+.22*e[5]-.17*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),h=h)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def rope(s,a,b,y=-.1):P.tube(s,(a[0],y,a[1]),(b[0],y,b[1]),.045,ROPE,n=8)
def arc(s,c,r,a0,a1,y=-.1,n=14):
 pts=[(c[0]+r*math.cos(a0+(a1-a0)*k/n),c[1]+r*math.sin(a0+(a1-a0)*k/n)) for k in range(n+1)]
 for u,v in zip(pts,pts[1:]):rope(s,u,v,y)
def draw(s,t,tl,hidden=()):
 p=state(t,tl);h=p['h'];cut=p['cut'];beat=p['beat'];zm=ZM0+h;zh=ZM0+.1-2*h
 if 'frame' not in hidden:
  hb.block(s,(0,.25,.45),(5.6,.95,.5),hb.DARK,.07)
  P.plate(s,(0,.75,3.6),(5.2,.14,6.4),hb.PLATE,tiles=(8,10))
  hb.block(s,(0,.3,7.0),(5.2,.8,.5),hb.sh(hb.DARK,1.1),.06)
  hb.block(s,(XF,.1,ZF+.5),(.3,.4,1.3),hb.MID,.04)
  hb.block(s,(0,.1,6.55),(.5,.5,.4),hb.BRASS,.05)
  P.rivets(s,[(x,.45) for x in (-2.3,-1.1,1.1,2.3)],.06,hb.BRASS,y=-.4)
  P.rivets(s,[(x,7.0) for x in (-2.3,-1.1,1.1,2.3)],.06,hb.STEEL,y=-.45)
 if 'pulleys' not in hidden:
  hb.wheel_spokes(s,(XF,ZF),RF,.2,-.05,2*h/RF,6,hb.sh(hb.STEEL,.95),thick=.2,spoke_w=.12)
  hb.wheel_spokes(s,(XM,zm),RM,.15,-.05,h/RM,5,hb.sh(hb.WARM,.95),thick=.2,spoke_w=.1)
  hb.pin(s,XF,ZF,-.05,.13,hb.BRASS,.5);hb.pin(s,XM,zm,-.05,.1,hb.BRASS,.5)
 if 'rope' not in hidden:
  rope(s,(0,6.35),(0,zm))                       # tied end down to the moving pulley
  arc(s,(XM,zm),RM,math.pi,2*math.pi)             # under the moving pulley
  rope(s,(2*RM,zm),(2*RM,ZF))                   # up to the fixed pulley
  arc(s,(XF,ZF),RF,0,math.pi)                   # over the fixed pulley
  rope(s,(XF-RF,ZF),(XF-RF,zh+.35))             # down to the handle
 if 'weight' not in hidden:
  P.tube(s,(XM,-.05,zm-RM-.0),(XM,-.05,zm-1.0),.05,hb.sh(hb.STEEL,.8),n=8)
  hb.block(s,(XM,-.05,zm-1.55),(1.3,.9,1.1),hb.BRASS,.07)
  hb.block(s,(XM,-.05,zm-2.25),(1.6,1.0,.4),hb.sh(hb.BRASS,.85),.06)
  hb.block(s,(XF-RF,-.1,zh),(.3,.3,.7),hb.RED,.05)
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(XF-RF-.55,-.6,zh+.9-(.5*sg if sg>0 else -.5)),(XF-RF-.55,-.6,zh+.9+(-.5 if sg>0 else .5)),hb.ARROW,.05) if False else hb.arrow(s,(XF-RF-.6,-.6,zh+(1.4 if sg>0 else .6)),(XF-RF-.6,-.6,zh+(.6 if sg>0 else 1.4)),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=5.2+7.0*cut;hb.block(s,(0,-.5,zc),(3.2,.14,1.8),hb.COVER,.06)
  P.rivets(s,[(-1.3,zc+.6),(1.3,zc+.6),(-1.3,zc-.6),(1.3,zc-.6)],.06,hb.sh(hb.STEEL,.8),y=-.6)
 return p
SHOTS=[((0, 0, 3.7), 2.15, 0.3), ((0, 0, 5.0), 1.6, 0.3), ((0, 0, 3.7), 1.15, 0.3), ((0, 0, 4.4), 1.4, 0.3), ((0, 0, 3.7), 1.15, 0.3), ((0, 0, 3.7), 1.15, 0.3), ((0, 0, 3.7), 1.15, 0.3), ((0, 0, 3.7), 2.15, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
