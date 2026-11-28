"""Hand winch: a crank turns a small 10-tooth pinion, the pinion drives a 26-tooth gear that shares an axle with a rope drum, and the rope lifts a crate.
Chain of four linked parts: crank -> pinion -> big gear + drum -> rope -> crate. Exact: gear ratio 26/10 (drum turns 0.385 of a crank turn), crate rise = drum radius * drum angle. Teaching model."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
NP=10;NB=26;RB=1.3;RP=RB*NP/NB;AX=(-.4,4.55);PX=(AX[0]-(RB+RP),4.55);RD=.58;Z0=1.05;CRATE=1.25;RX=2.45;YR=-.62

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 k=2*math.pi*(.7*e[2]+.45*e[3]+.5*e[5]-.4*e[6])
 return dict(beat=i,cut=e[1]*(1-e[7]),crank=k,rise=RD*k*NP/NB)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);k=p['crank'];rise=p['rise'];cut=p['cut'];beat=p['beat'];cz=Z0+rise
 if 'frame' not in hidden:
  hb.block(s,(0,.25,.45),(7.4,.95,.5),hb.DARK,.07)
  P.plate(s,(0,.8,3.5),(6.6,.14,6.0),hb.PLATE,tiles=(10,10))
  for sx in (-3.4,3.4):hb.block(s,(sx,.3,3.3),(.4,.8,5.6),hb.sh(hb.DARK,1.1),.05)
  hb.block(s,(0,.3,6.2),(7.2,.8,.44),hb.sh(hb.DARK,1.15),.06)
  P.rivets(s,[(x,.45) for x in (-3.0,-1.5,0,1.5,3.0)],.06,hb.BRASS,y=-.4)
 if 'drum' not in hidden:
  P.tube(s,(AX[0],-.34,AX[1]),(AX[0],-.82,AX[1]),RD,hb.sh(hb.WARM,.95),n=28,chamfer=.04)
  for q in (-.42,-.54,-.66):P.tube(s,(AX[0],q,AX[1]),(AX[0],q-.04,AX[1]),RD+.045,(150,118,70),n=28)
  P.tube(s,(AX[0],.5,AX[1]),(AX[0],-.9,AX[1]),.13,hb.STEEL,n=12,chamfer=.03)
 if 'gears' not in hidden:
  ab=math.pi-math.pi/NB+k*NP/NB
  P.gear(s,(AX[0],0,AX[1]),RB,NB,ab,.28,hb.BRASS,y=-.22,tip=.1,root=.12,hub=.22,holes=5,hole_r=.16,mark=True)
  P.gear(s,(PX[0],0,PX[1]),RP,NP,-k,.28,hb.sh(hb.STEEL,1.0),y=-.22,tip=.12,root=.14,hub=.3,holes=0,hole_r=.1,mark=True)
 if 'crank' not in hidden:
  ang=-k+.8;tx=PX[0]+1.0*math.cos(ang);tz=PX[1]+1.0*math.sin(ang)
  hb.bar(s,PX,(tx,tz),.28,.14,-.5,hb.RED)
  P.tube(s,(tx,-.45,tz),(tx,-.9,tz),.16,hb.BRASS,n=12,chamfer=.03)
  P.tube(s,(PX[0],-.4,PX[1]),(PX[0],-.7,PX[1]),.14,hb.STEEL,n=12,chamfer=.03)
 if 'rope' not in hidden:
  zt=AX[1]+RD+.03;P.tube(s,(AX[0],YR,zt),(RX,YR,zt),.05,(214,190,140),n=8);P.tube(s,(RX,YR,zt-.32),(RX,YR,cz+CRATE+.35),.05,(214,190,140),n=8)
  P.tube(s,(RX,YR-.1,zt-.32),(RX,YR+.2,zt-.32),.32,hb.sh(hb.STEEL,.9),n=20,chamfer=.04)
 if 'crate' not in hidden:
  x=RX
  hb.block(s,(x,YR,cz+CRATE/2-.05),(1.3,1.0,CRATE),(176,128,72),.07)
  hb.block(s,(x,YR-.51,cz+CRATE/2-.05),(1.35,.06,.18),hb.sh(hb.BRASS,.9),.02);hb.block(s,(x,YR-.51,cz+CRATE*.2),(1.35,.06,.18),hb.sh(hb.BRASS,.9),.02)
  hb.block(s,(x,YR,cz+CRATE+.2),(.34,.34,.3),hb.STEEL,.04)
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(PX[0]-.6*sg,-1.1,3.0),(PX[0]+.9*sg,-1.1,3.0),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=2.6+7.0*cut;hb.block(s,(-.4,-1.0,zc),(4.6,.14,1.3),hb.COVER,.06)
  P.rivets(s,[(-2.4,zc),(1.6,zc)],.06,hb.sh(hb.STEEL,.8),y=-1.1)
 return p
SHOTS=[((0, 0, 3.4), 1.6, 0.3), ((-0.4, 0, 4.0), 1.4, 0.3), ((0, 0, 3.4), 1.21, -0.45), ((0, 0, 3.4), 1.26, 0.8), ((0, 0, 3.4), 1.26, 0.2), ((0, 0, 3.4), 1.21, -0.7), ((0, 0, 3.4), 1.16, 0.5), ((0, 0, 3.4), 1.6, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
