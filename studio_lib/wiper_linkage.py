"""Wiper linkage (crank-rocker four-bar): a small motor crank turns round and round, a coupler rod pushes and pulls the wiper arm, and the arm swings back and forth over the glass.
Exact four-bar geometry: ground 2.7, crank .7, coupler 2.4, rocker 1.3 (crank is shortest, so it can turn fully); rocker angle solved from the circle intersection. Teaching model, no car shown."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
G=2.7;CR=.7;CP=2.4;RK=1.3;ZP=1.45;O2=(-1.35,ZP);O4=(1.35,ZP);ARM=3.7

def solve(th):
 A=(O2[0]+CR*math.cos(th),O2[1]+CR*math.sin(th));dx,dy=O4[0]-A[0],O4[1]-A[1];D=math.hypot(dx,dy)
 l=(CP*CP-RK*RK+D*D)/(2*D);h=math.sqrt(max(0.,CP*CP-l*l));ex,ey=dx/D,dy/D
 B=(A[0]+l*ex-h*ey,A[1]+l*ey+h*ex);return A,B,math.atan2(B[1]-O4[1],B[0]-O4[0])
def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 turn=2*math.pi*e[2]+math.pi*e[3]+2*math.pi*e[5]-math.pi*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),turn=turn)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut'];beat=p['beat'];A,B,phi=solve(p['turn']+.6);ux,uz=math.cos(phi),math.sin(phi)
 if 'glass' not in hidden:
  P.plate(s,(-.5,.6,3.7),(6.2,.14,4.5),(54,84,104),tiles=(12,9))
  hb.block(s,(-.5,.42,1.62),(6.0,.3,.1),hb.sh(hb.WARM,.85),.03);hb.block(s,(-.5,.42,5.8),(6.0,.3,.1),hb.sh(hb.BRASS,.9),.03)
  for sx in (-3.55,2.55):hb.block(s,(sx,.5,3.7),(.3,.5,4.6),hb.DARK,.05)
  hb.block(s,(-.5,.5,1.35),(6.6,.5,.26),hb.DARK,.05)
  hb.block(s,(-.5,.5,6.1),(6.6,.5,.26),hb.DARK,.05)
 if 'frame' not in hidden:
  hb.block(s,(0,.2,.5),(6.2,.95,.5),hb.DARK,.07)
  hb.block(s,(O2[0],.1,ZP-.25),(1.1,.7,.5),hb.sh(hb.DARK,1.15),.06)
  P.rivets(s,[(x,.5) for x in (-2.7,-1.4,0,1.4,2.7)],.06,hb.BRASS,y=-.4)
  P.rivets(s,[(x,6.1) for x in (-3.4,-2.0,-.6,.8,2.2)],.07,hb.STEEL,y=.2)
  P.rivets(s,[(x,1.35) for x in (-3.4,-2.0,-.6,.8,2.2)],.07,hb.STEEL,y=.2)
 if 'crank' not in hidden:
  P.gear(s,(O2[0],0,O2[1]),.62,12,p['turn']+.6,.24,hb.BRASS,y=.02,tip=.12,root=.14,hub=.28,holes=0,hole_r=.1,mark=True)
  hb.bar(s,O2,A,.34,.14,-.30,hb.RED)
  P.tube(s,(O2[0],-.28,O2[1]),(O2[0],-.52,O2[1]),.18,hb.STEEL,n=14,chamfer=.03)
 if 'coupler' not in hidden:
  hb.bar(s,A,B,.26,.12,-.14,hb.sh(hb.STEEL,.95));hb.pin(s,A[0],A[1],-.3,.12,hb.BRASS,.32);hb.pin(s,B[0],B[1],-.14,.12,hb.BRASS,.5)
 if 'arm' not in hidden:
  tip=(O4[0]+ARM*ux,O4[1]+ARM*uz);bs=(O4[0]+1.7*ux,O4[1]+1.7*uz)
  hb.bar(s,O4,tip,.3,.14,0.,hb.STEEL,eyes=False)
  hb.bar(s,bs,tip,.15,.14,-.22,hb.sh(hb.DARK,.7),eyes=False)
  for q in (.3,.45,.6,.75,.9):hb.pin(s,O4[0]+(ARM*q+.3)*ux,O4[1]+(ARM*q+.3)*uz,-.05,.045,hb.BRASS,.3)
  P.tube(s,(O4[0],-.12,O4[1]),(O4[0],-.5,O4[1]),.2,hb.BRASS,n=14,chamfer=.04)
 if beat in (2,3,5,6):
  sg=-1 if beat==6 else 1;hb.arrow(s,(O2[0]-.9*sg,-.8,.95),(O2[0]+.9*sg,-.8,.95),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=1.45+7.0*cut;hb.block(s,(0,-.6,zc),(4.4,.14,.9),hb.COVER,.06)
  P.rivets(s,[(-2.2,zc+.25),(2.2,zc+.25),(-2.2,zc-.25),(2.2,zc-.25)],.06,hb.sh(hb.STEEL,.8),y=-.7)
 return p
SHOTS=[((-0.5, 0, 3.5), 1.8, 0.3), ((-0.5, 0, 3.0), 1.3, 0.3), ((-0.5, 0, 3.6), 1.2, 0.3), ((-0.5, 0, 3.0), 1.5, 0.3), ((-0.5, 0, 3.6), 1.2, 0.3), ((-0.5, 0, 3.6), 1.2, 0.3), ((-0.5, 0, 3.6), 1.2, 0.3), ((-0.5, 0, 3.5), 1.8, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
