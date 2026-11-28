"""Hand egg beater: a crank turns a big 24-tooth gear, and that gear turns two 8-tooth pinions, each carrying a beater blade that dips into the batter.
Chain of linked parts: crank -> big gear -> two pinions -> blades -> batter. Exact: gear ratio 24/8 (each blade turns three times per crank turn, opposite way to the crank). Teaching model."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
NA=24;NB=8;RA=1.6;RB=RA*NB/NA;C=(0.,5.0);D=RA+RB
PH=(-math.pi/4,-3*math.pi/4)
PC=[(C[0]+D*math.cos(f),C[1]+D*math.sin(f)) for f in PH]
BL=.9;BATTER=(244,206,96)

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 k=2*math.pi*(.8*e[2]+.5*e[3]+.6*e[5]-.45*e[6])
 return dict(beat=i,cut=e[1]*(1-e[7]),crank=k,blades=-k*NA/NB)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);k=p['crank'];bl=p['blades'];cut=p['cut'];beat=p['beat']
 if 'frame' not in hidden:
  hb.block(s,(0,.25,.8),(7.8,.95,.5),hb.DARK,.07)
  P.plate(s,(0,.8,3.7),(7.0,.14,6.2),hb.PLATE,tiles=(10,10))
  for sx in (-3.6,3.6):hb.block(s,(sx,.3,3.8),(.4,.8,5.8),hb.sh(hb.DARK,1.1),.05)
  hb.block(s,(0,.3,6.85),(7.6,.8,.44),hb.sh(hb.DARK,1.15),.06)
  P.rivets(s,[(x,.9) for x in (-3.2,-1.6,0,1.6,3.2)],.06,hb.BRASS,y=-.2)
 if 'bowl' not in hidden:
  hb.block(s,(0,.1,1.8),(5.4,.9,1.5),hb.sh(hb.MID,.9),.08)
  hb.block(s,(0,-.36,2.2),(4.9,.04,.8),BATTER,.02)
  hb.block(s,(0,-.36,1.45),(5.3,.05,.18),hb.sh(hb.STEEL,.8),.02)
 if 'gears' not in hidden:
  P.gear(s,(C[0],0,C[1]),RA,NA,math.pi/NA+k,.28,hb.BRASS,y=-.22,tip=.1,root=.12,hub=.22,holes=5,hole_r=.2,mark=True)
  for q in PC:P.gear(s,(q[0],0,q[1]),RB,NB,bl,.28,hb.sh(hb.STEEL,1.0),y=-.22,tip=.12,root=.14,hub=.3,holes=0,hole_r=.1,mark=True)
 if 'beaters' not in hidden:
  for q in PC:
   P.tube(s,(q[0],-.4,q[1]),(q[0],-.7,q[1]),.12,hb.STEEL,n=12,chamfer=.03)
   for j,(ln,yy,col) in enumerate(((BL,-.56,hb.STEEL),(BL*.55,-.7,hb.sh(hb.STEEL,.85)))):
    a=bl+j*math.pi/2;dx=ln*math.cos(a);dz=ln*math.sin(a)
    hb.bar(s,(q[0]-dx,q[1]-dz),(q[0]+dx,q[1]+dz),.2,.08,yy,col,eyes=False)
   P.tube(s,(q[0]+BL*math.cos(bl),-.6,q[1]+BL*math.sin(bl)),(q[0]+BL*math.cos(bl),-.7,q[1]+BL*math.sin(bl)),.12,hb.BRASS,n=10)
 if 'crank' not in hidden:
  ang=k+.7;tx=C[0]+1.15*math.cos(ang);tz=C[1]+1.15*math.sin(ang)
  hb.bar(s,C,(tx,tz),.3,.14,-.5,hb.RED)
  P.tube(s,(tx,-.45,tz),(tx,-.95,tz),.17,hb.BRASS,n=12,chamfer=.03)
  P.tube(s,(C[0],-.4,C[1]),(C[0],-.7,C[1]),.15,hb.STEEL,n=12,chamfer=.03)
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(-.9*sg,-1.1,.9),(.9*sg,-1.1,.9),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=3.5+7.0*cut;hb.block(s,(0,-1.0,zc),(6.2,.14,1.4),hb.COVER,.06)
  P.rivets(s,[(-2.7,zc),(2.7,zc)],.06,hb.sh(hb.STEEL,.8),y=-1.1)
 return p
SHOTS=[((0, 0, 3.6), 1.55, 0.3), ((0, 0, 4.2), 1.5, 0.3), ((0, 0, 3.6), 1.3, -0.45), ((0, 0, 3.6), 1.45, 0.8), ((0, 0, 3.6), 1.4, 0.2), ((0, 0, 3.6), 1.3, -0.7), ((0, 0, 3.6), 1.25, 0.5), ((0, 0, 3.6), 1.55, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
