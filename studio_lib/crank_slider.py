"""Crank-slider (piston engine core): gas pressure pushes a piston down a cylinder, the connecting rod turns the crank, the crank spins the flywheel.
Exact kinematics: piston height = crank_z + r*sin(a) + sqrt(L^2-(r*cos(a))^2). Teaching model, no valves or fuel shown."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
FLOOR=.30;GROUND=(34,47,59);DARK=True
CZ=2.35;RC=.78;LR=2.45;FW=1.32

def pose(a):
 pin=(RC*math.cos(a),CZ+RC*math.sin(a));pz=CZ+RC*math.sin(a)+math.sqrt(LR*LR-(RC*math.cos(a))**2);return pin,pz
def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 turn=-math.pi*e[2]-math.pi*e[3]-2*math.pi*e[5]+math.pi*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),turn=turn)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);a=math.pi/2+p['turn'];cut=p['cut'];beat=p['beat'];pin,pz=pose(a)
 if 'block' not in hidden:
  for sg in (-1,1):hb.block(s,(sg*.98,.1,5.2),(.52,.9,3.6),hb.DARK,.06)
  hb.block(s,(0,.1,7.15),(2.5,.9,.45),hb.sh(hb.DARK,1.12),.06)
  P.plate(s,(0,.6,3.4),(3.6,.2,6.2),hb.PLATE,tiles=(6,10))
  hb.block(s,(0,.1,.62),(4.6,.95,.5),hb.DARK,.07)
  P.rivets(s,[(x,.62) for x in (-2.0,-1.0,1.0,2.0)],.06,hb.BRASS,y=-.4)
 if 'piston' not in hidden:
  hb.block(s,(0,0,pz+.22),(1.38,.8,.62),hb.STEEL,.06)
  for dz in (.35,.2):P.tube(s,(-.69,-.42,pz+dz),(.69,-.42,pz+dz),.025,hb.sh(hb.MID,.6),n=6)
  P.tube(s,(0,-.46,pz),(0,-.55,pz),.17,hb.BRASS,n=14,chamfer=.03)
 if 'rod' not in hidden:
  hb.bar(s,(pin[0],pin[1]),(0,pz),.34,.16,-.30,hb.sh(hb.STEEL,.95))
 if 'flywheel' not in hidden:
  hb.wheel_spokes(s,(0,CZ),FW,.38,.06,p['turn']*1.0,6,hb.sh(hb.WARM,.95),thick=.22,spoke_w=.2)
  P.annulus(s,(0,0,CZ),FW-.12,FW-.6,.12,hb.sh(hb.MID,.9))
 if 'crank' not in hidden:
  hb.bar(s,(0,CZ),(pin[0],pin[1]),.34,.16,-.14,hb.RED)
  P.tube(s,(pin[0],-.12,pin[1]),(pin[0],-.46,pin[1]),.14,hb.BRASS,n=14,chamfer=.03)
  P.tube(s,(0,-.1,CZ),(0,-.62,CZ),.2,hb.STEEL,n=14,chamfer=.03)
 if beat in (2,3):hb.arrow(s,(0,-.8,pz+1.9) if False else (0,-.7,7.95),(0,-.7,7.25),hb.WARM,.06)
 if 'cover' not in hidden and cut<.99:
  zc=5.0+7.0*cut;hb.block(s,(0,-.58,zc),(3.5,.14,1.55),hb.COVER,.06)
  P.rivets(s,[(-1.5,zc+.5),(1.5,zc+.5),(-1.5,zc-.5),(1.5,zc-.5)],.06,hb.sh(hb.STEEL,.8),y=-.68)
 return p
SHOTS=[((0, 0, 4.1), 2.45, 0.3), ((0, 0, 4.8), 1.5, 0.3), ((0, 0, 4.4), 1.35, 0.3), ((0, 0, 3.2), 2.0, 0.3), ((0, 0, 4.4), 1.35, 0.3), ((0, 0, 4.4), 1.35, 0.3), ((0, 0, 4.4), 1.35, 0.3), ((0, 0, 4.1), 2.45, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
