"""Sectioned desk stapler: driver, magazine, anvil and length-preserving clinch."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import cylinder,background as gradient
FLOOR=.30;GROUND=(193,206,211);DARK=False
LEG=.8;R=.06;STRAIGHT=.23;ANVIL=.83;CONTACT=ANVIL+LEG;FINAL=ANVIL+STRAIGHT+R

def bend_angle(crown):
 if crown>=CONTACT:return 0.
 lo,hi=0.,math.pi/2;drop=crown-STRAIGHT-ANVIL
 for _ in range(42):
  a=(lo+hi)/2;vertical=R*math.sin(a)+(LEG-STRAIGHT-R*a)*math.cos(a)
  if vertical>drop:lo=a
  else:hi=a
 return (lo+hi)/2

def leg_points(crown,side,x=2.2):
 if crown>=CONTACT:return [(x,side*.60,crown),(x,side*.60,crown-LEG)]
 a=bend_angle(crown);points=[(x,side*.60,crown),(x,side*.60,crown-STRAIGHT)]
 points += [(x,side*(.60-R*(1-math.cos(q))),crown-STRAIGHT-R*math.sin(q)) for q in np.linspace(0,a,12)[1:]]
 tail=LEG-STRAIGHT-R*a;last=np.array(points[-1]);points.append(tuple(last+[0,-side*tail*math.sin(a),-tail*math.cos(a)]))
 return points

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 feed=0. if i<2 else ease(progress(t,b[2])) if i==2 else 1.
 crown=2.2 if i<3 else 2.2+(CONTACT-2.2)*ease(progress(t,b[3])) if i==3 else CONTACT+(FINAL-CONTACT)*ease(progress(t,b[4])) if i==4 else FINAL
 driver=crown if i<6 else FINAL+(2.2-FINAL)*ease(progress(t,b[6])) if i==6 else 2.2
 return dict(beat=i,feed=feed,crown_z=crown,driver_z=driver,bend=bend_angle(crown),handle_angle=math.atan((driver+.30-1.8)/5.2),next_feed=ease(progress(t,b[6])) if i==6 else 1. if i==7 else 0.,cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7]))))
@functools.lru_cache(maxsize=1)
def background():return gradient((236,244,248),(192,211,218))
def wire(s,crown,x,color):
 s.beam((x,-.60,crown),(x,.60,crown),.018,color)
 for side in (-1,1):
  pts=leg_points(crown,side,x)
  for a,b in zip(pts,pts[1:]):
   if np.linalg.norm(np.subtract(a,b))>1e-8:s.beam(a,b,.018,color)
def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut'];driver=p['driver_z']
 s.box((-.2,0,.50),(7.0,2.25,.35),(42,73,94))
 s.box((-3,0,1.15),(.48,1.4,1.2),(102,125,133));cylinder(s,(-3,0,1.8),.15,1.8,(176,190,191),'y',n=18)
 # The forward paper section is displaced only as an explicitly labelled cutaway.
 for j in range(3):
  z=.93+j*.05
  s.box((2.05,.58,z),(2.55,1.16,.045),(230+j*5,234+j*4,225+j*6))
  s.box((2.05,-.58-6*cut,z),(2.55,1.16,.045),(230+j*5,234+j*4,225+j*6))
 if 'anvil' not in hidden:
  s.box((2.2,0,.72),(.70,1.65,.18),(124,151,162))
  for side in (-1,1):
   pts=[(2.2,side*y,ANVIL) for y in np.linspace(.12,.60,10)]
   for a,b in zip(pts,pts[1:]):s.beam(a,b,.035,(77,102,117))
 # A rigid handle drives a vertical follower through sliding contact.
 end=(-3+5.8*math.cos(p['handle_angle']),0,1.8+5.8*math.sin(p['handle_angle']))
 s.beam((-3,0,1.8),end,.10,(135,157,164))
 s.beam((-3,0,2.04+5.5*cut),(end[0],0,end[2]+.24+5.5*cut),.37,(178,72,58))
 s.box((-.35,.78,1.74),(5.35,.10,1.0),(154,174,177))
 s.box((-.35,-.78,1.74+5.5*cut),(5.35,.10,1.0),(144,164,174))
 if 'driver' not in hidden:s.box((2.2,0,driver+.10),(.12,1.30,.20),(221,192,111))
 if 'magazine' not in hidden:
  x=1.4+.8*p['feed'];wire(s,p['crown_z'],x,(215,189,124))
  for j in range(1,8):wire(s,2.2,1.4+.8*p['feed']-j*.18+.18*p['next_feed'],(166,184,190))
 if 'spring' not in hidden:
  front=.90+.8*p['feed']+.18*p['next_feed'];points=[(-2.65+(front+2.65)*j/70,.15*math.sin(q),1.8+.15*math.cos(q)) for j,q in enumerate(np.linspace(0,18*math.pi,71))]
  for a,b in zip(points,points[1:]):s.beam(a,b,.013,(172,184,176))
  s.box((front,0,1.82),(.12,.60,.46),(106,137,150))
 if p['beat'] in (3,4) and 'input' not in hidden:
  z=end[2]+.8;s.beam((2.0,-.3,z),(2.0,-.3,z-.45),.035,(83,142,160))
  s.beam((2.0,-.3,z-.45),(1.87,-.3,z-.30),.025,(83,142,160));s.beam((2.0,-.3,z-.45),(2.13,-.3,z-.30),.025,(83,142,160))
 return p
SHOTS=[((0,0,1.35),1.05,.45),((0,0,1.70),1.4,.6),((1.25,0,1.80),2.1,.55),((2.1,0,1.65),2.35,.65),((2.2,0,1.05),2.65,.45),((2.2,0,1.05),2.55,.45),((1.5,0,1.60),1.8,.55),((0,0,1.35),1.05,.45)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 4.2
