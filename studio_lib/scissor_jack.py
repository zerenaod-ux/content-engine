"""Scissor jack: a screw with opposite threads pulls two side nuts together, so four hinged arms fold upright and the platform rises.
Teaching model, no car shown. Beat 2/3/5 raise it, beat 4 holds, beat 6 lowers a little. Geometry is exact: arms keep one length, so height = 2*sqrt(L^2-a^2)."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
L=2.25;A0=2.05;A1=.55;ZB=1.15;PITCH=.30;REVS=(A0-A1)/PITCH;TURN=REVS*2*math.pi

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 lift=.34*e[2]+.26*e[3]+.34*e[5]-.52*e[6]
 cut=e[1]*(1-e[7])
 return dict(beat=i,cut=cut,lift=lift,turn=lift*TURN)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def geometry(lift):
 a=A0-lift*(A0-A1);h=2*math.sqrt(L*L-a*a);return a,h
def draw(s,t,tl,hidden=()):
 p=state(t,tl);lift=p['lift'];a,h=geometry(lift);zm=ZB+h/2;zt=ZB+h;beat=p['beat']
 bot=(0,ZB);top=(0,zt);lm=(-a,zm);rm=(a,zm)
 if 'base' not in hidden:
  hb.block(s,(0,.05,ZB-.32),(6.8,.9,.46),hb.DARK,.07)
  hb.block(s,(0,-.42,ZB-.32),(6.2,.08,.30),hb.MID,.03)
  P.rivets(s,[(x,ZB-.32) for x in (-3.0,-1.5,1.5,3.0)],.06,hb.BRASS,y=-.49)
 if 'arms' not in hidden:
  for y in (.30,-.30):
   hb.bar(s,bot,lm,.46,.14,y,hb.STEEL);hb.bar(s,bot,rm,.46,.14,y,hb.sh(hb.STEEL,.92))
   hb.bar(s,top,lm,.46,.14,y,hb.sh(hb.STEEL,.96));hb.bar(s,top,rm,.46,.14,y,hb.STEEL)
  for q in (bot,top,lm,rm):hb.pin(s,q[0],q[1],0,.13,hb.BRASS,.92)
 if 'screw' not in hidden:
  ph=p['turn']*PITCH/(2*math.pi)
  hb.thread(s,-a-.2,0,zm,0,.17,-ph,PITCH,hb.STEEL);hb.thread(s,0,a+1.25,zm,0,.17,ph,PITCH,hb.sh(hb.STEEL,1.05))
  P.tube(s,(0,-.12,zm),(0,.12,zm),.23,hb.WARM,n=18,chamfer=.04)
 if 'nuts' not in hidden:
  for q in (lm,rm):hb.block(s,(q[0],0,q[1]),(.62,.50,.62),hb.BRASS,.06)
 if 'platform' not in hidden:
  hb.block(s,(0,0,zt+.22),(4.0,.9,.40),hb.MID,.07)
  hb.block(s,(0,-.46,zt+.46),(3.6,.10,.10),hb.sh(hb.RED,1.05),.03)
  P.rivets(s,[(x,zt+.22) for x in (-1.6,-.8,.8,1.6)],.06,hb.BRASS,y=-.47)
 if 'crank' not in hidden:
  cx=a+1.25;ang=p['turn']
  hx=cx+.62*math.cos(ang);hz=zm+.62*math.sin(ang)
  P.tube(s,(cx,-.1,zm),(cx,-.42,zm),.19,hb.sh(hb.STEEL,.9),n=14,chamfer=.03)
  hb.bar(s,(cx,zm),(hx,hz),.20,.12,-.42,hb.RED,eyes=False)
  P.tube(s,(hx,-.42,hz),(hx,-.80,hz),.10,hb.sh(hb.RED,1.15),n=12,chamfer=.025)
 if beat in (2,3,5):
  sign=1;cx=a+1.25
  hb.arrow(s,(cx+.1,-.95,zm+1.55),(cx+.1,-.95,zm+.95))
 if beat in (3,4):
  hb.arrow(s,(0,-.62,zt+1.55),(0,-.62,zt+.95),(236,152,72))
 if 'cover' not in hidden and p['cut']<.99:
  hb.block(s,(0,-.56,zm+7.0*p['cut']),(2*a+1.6,.14,1.05),hb.COVER,.05)
  P.rivets(s,[(-a-.55,zm+7.0*p['cut']),(a+.55,zm+7.0*p['cut'])],.06,hb.sh(hb.STEEL,.8),y=-.66)
 return p
SHOTS=[((0,0,2.5),1.65,.30),((0,0,2.7),1.75,.30),((.5,0,3.3),1.7,.30),((0,0,3.9),2.4,.30),((0,0,3.7),1.7,.30),((.5,0,4.0),1.65,.30),((0,0,3.5),1.7,.30),((0,0,2.6),1.65,.30)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
