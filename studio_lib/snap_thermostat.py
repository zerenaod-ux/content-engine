"""Representative automatic-reset snap-disc switch, deliberately slow and enlarged."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import cylinder,background as gradient,path_point
FLOOR=.30
GROUND=(190,205,209)
DARK=False
RIM_Z=2.13
PIN=.405

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,beat in enumerate(b) if t<beat['end']),7))
 hot=0. if i<3 else ease(progress(t,b[3])) if i==3 else 1. if i<6 else 1-ease(progress(t,b[6])) if i==6 else 0.
 temperature=ease(progress(t,b[2])) if i==2 else 1. if i in (3,4) else 1-ease(progress(t,b[5])) if i==5 else 0.
 dome=-.10+.20*hot;pin_top=RIM_Z+dome+PIN;offset=pin_top-2.5;angle=math.atan(offset/1.1)+math.asin(.065/math.hypot(1.1,offset))
 tip=np.array([-1.1+2.2*math.cos(angle),0,2.5+2.2*math.sin(angle)])
 return dict(beat=i,hot=hot,temperature=temperature,dome=dome,pin_top=pin_top,angle=angle,tip=tip.tolist(),gap=float(tip[2]-2.5),powered=float(hot<.001),cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7]))))
@functools.lru_cache(maxsize=1)
def background():return gradient((235,244,247),(190,209,218))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut'];tip=p['tip']
 s.box((0,.0,.55),(5.6,2.5,.28),(68,101,119))
 cylinder(s,(0,0,1.16),1.5,.95,(180,191,190),'z',n=36)
 # Exposed ceramic support and rim; cap lifts as a simplified cutaway.
 cylinder(s,(0,0,1.78),1.35,.20,(217,226,215),'z',n=36)
 cylinder(s,(0,0,3.24+6.5*cut),1.55,.18,(166,187,195),'z',n=36)
 for k in range(36):
  a=k*2*math.pi/36;b=(k+1)*2*math.pi/36
  s.face([(1.5*math.cos(beta),1.5*math.sin(beta),z+6.5*cut) for beta,z in ((a,1.63),(b,1.63),(b,3.15),(a,3.15))],(151,177,189))
 for x in (-1.25,1.25):cylinder(s,(x,-.6,.87),.09,.4,(212,174,100),'z',n=12)
 if 'disc' not in hidden:
  for j in range(8):
   r0=.94*j/8;r1=.94*(j+1)/8
   for k in range(28):
    a=k*2*math.pi/28;c=a+2*math.pi/28
    s.face([(r*math.cos(beta),r*math.sin(beta),RIM_Z+p['dome']*(1-(r/.94)**2)) for r,beta in ((r0,a),(r1,a),(r1,c),(r0,c))],(175,124,79) if j%2 else (193,148,100))
 if 'pin' not in hidden:cylinder(s,(0,0,(RIM_Z+p['dome']+p['pin_top'])/2),.065,PIN,(226,215,175),'z',n=16)
 s.box((-1.1,.0,2.38),(.22,.32,.24),(93,112,117))
 if 'contacts' not in hidden:
  s.beam((-1.1,0,2.5),tip,.065,(193,163,98));cylinder(s,(tip[0],0,tip[2]-.035),.115,.07,(222,207,166),'z',n=18)
  cylinder(s,(1.1,0,2.36),.115,.14,(222,207,166),'z',n=18)
  s.beam((1.1,.0,.75),(1.1,0,2.32),.045,(178,145,88))
 # Separate supply and test lamp demonstrate contact state, not a mains appliance.
 s.box((-2.15,-.25,1.0),(.50,.70,.65),(84,106,118));s.box((-2.15,-.25,1.37),(.32,.45,.08),(220,187,120))
 cylinder(s,(2.10,-.25,.92),.33,.35,(101,126,130),'z',n=24)
 cylinder(s,(2.10,-.25,1.30),.28,.40,(239,203,98) if p['powered'] else (143,167,175),'z',n=24)
 circuit=[(-2.15,-.3,1.4),(-2.15,-1.0,.80),(-1.1,-1,.80),(-1.1,0,2.50),(1.1,0,2.50),(1.1,-1.,.80),(2.1,-1.,.80),(2.1,-.25,1.45),(2.50,-.25,.80),(2.50,.90,.80),(-2.15,.90,.80),(-2.15,-.3,1.4)]
 for n,(a,b) in enumerate(zip(circuit,circuit[1:])):
  if n==3:continue
  s.beam(a,b,.025,(151,102,66))
 if p['powered'] and 'current' not in hidden:
  for k in range(18):
   point=path_point(circuit,(t*.30+k/18)%1);cylinder(s,point,.035,.07,(235,210,117),'y',n=8)
 if p['beat'] in (2,3,4,5,6) and 'heat' not in hidden:
  # Color markers explicitly illustrate heat transfer; no fake glowing metal.
  warm=p['beat'] in (2,3,4)
  for k in range(9):
   u=(t*.48+k/9)%1;x=-.7+(k%3)*.7;y=.5
   route=[(x,-1.8,1.0),(x,-1.8,2.0),(x,-.4,2.12)] if warm else [(x,-.4,2.12),(x,-1.8,2.6),(x,-1.8,3.4)]
   point=path_point(route,u)
   s.beam(point,point+np.array([0,0,.15]),.025,(220,124,80) if warm else (103,160,187))
 return p
SHOTS=[((0,0,1.9),1.45,.44),((0,0,2.3),2.0,.36),((0,0,2.2),2.05,.36),((.25,0,2.45),2.55,.28),((.7,0,2.55),2.6,.25),((0,0,2.2),2.05,.36),((.25,0,2.45),2.55,.28),((0,0,1.9),1.45,.44)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 9.
