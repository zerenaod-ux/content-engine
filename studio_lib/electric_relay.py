"""Representative electromagnetic relay with isolated control/load circuits."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import cylinder,sphere,background as gradient,path_point
PIVOT=np.array([-1.4,0,2.8]);LENGTH=2.7;CLOSED=-.16
FLOOR=.30
GROUND=(43,55,68)
DARK=True

def point(x,z,angle):return PIVOT+np.array([x*math.cos(angle)-z*math.sin(angle),0,x*math.sin(angle)+z*math.cos(angle)])
FIXED=point(LENGTH,-.11,CLOSED)+np.array([math.sin(CLOSED)*.20,0,-math.cos(CLOSED)*.20])

def physical(angle,current):
 moving=point(LENGTH,-.11,angle);gap=float(np.linalg.norm(moving-FIXED)-.20)
 return dict(angle=angle,current=current,gap=max(0.,gap),powered=float(gap<.003),moving=moving.tolist())

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,beat in enumerate(b) if t<beat['end']),7))
 if i<2:current=0.;angle=0.;switch=0.
 elif i==2:current=.60*ease(progress(t,b[2]));angle=0.;switch=ease(min(1,progress(t,b[2])/.2))
 elif i==3:current=.6+.4*ease(progress(t,b[3]));angle=CLOSED*ease(progress(t,b[3]));switch=1.
 elif i==4:current=1.;angle=CLOSED;switch=1.
 elif i==5:
  u=ease(progress(t,b[5]));current=1-u;angle=CLOSED*(1-u);switch=1-ease(min(1,progress(t,b[5])/.2))
 else:current=0.;angle=0.;switch=0.
 p=physical(angle,current);p.update(beat=i,switch=switch,cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7]))))
 return p
@functools.lru_cache(maxsize=1)
def background():return gradient((25,33,46),(50,66,81))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut'];angle=p['angle']
 s.box((0,0,.55),(8.0,3.0,.28),(66,84,93))
 s.box((-.1,.68,.95),(3.8,1.8,.45),(53,63,67))
 # A complete removable relay cover; control and load wires stay connected.
 s.box((-.1,.25,3.52+6.5*cut),(3.8,1.8,.16),(64,76,80))
 for x in (-1.92,1.72):s.box((x,.25,2.18+6.5*cut),(.16,1.8,2.6),(58,70,75))
 for y in (-.59,1.09):s.box((-.1,y,2.18+6.5*cut),(3.8,.13,2.6),(62,77,83))
 # Fixed iron core has a beveled pole face that meets the armature underside.
 if 'core' not in hidden:
  ring=[(.2+.28*math.cos(a),.28*math.sin(a)) for a in np.linspace(0,2*math.pi,24,endpoint=False)]
  top=[(x,y,PIVOT[2]+(x-PIVOT[0])*math.tan(CLOSED)-.065/math.cos(CLOSED)) for x,y in ring]
  s.face(top,(157,178,181))
  for j,(x,y) in enumerate(ring):s.face([(x,y,.78),(ring[(j+1)%24][0],ring[(j+1)%24][1],.78),top[(j+1)%24],top[j]],(103,128,139))
 if 'coil' not in hidden:
  points=[(.2+.45*math.cos(a),.45*math.sin(a),.88+1.12*j/144) for j,a in enumerate(np.linspace(0,24*math.pi,145))]
  for a,b in zip(points,points[1:]):s.beam(a,b,.045,(194,112,67))
 if 'armature' not in hidden:
  s.beam(PIVOT,point(LENGTH,0,angle),.065,(174,194,198));s.cylinder(tuple(PIVOT),.14,.48,(207,177,108),n=20)
  sphere(s,p['moving'],.10,(225,202,142),n=14,bands=7)
 sphere(s,FIXED,.10,(224,199,130),n=14,bands=7)
 s.beam(tuple(FIXED-np.array([0,0,.1])),(FIXED[0],0,.8),.055,(187,154,90))
 # Return spring is stretched by attraction and releases stored energy on switch-off.
 anchor=np.array([-1.50,.60,3.32]);end=point(1.3,0,angle)+[0,.20,0]
 s.beam((anchor[0],anchor[1],.8),anchor,.05,(97,121,133))
 if 'spring' not in hidden:
  direction=end-anchor;u=np.cross(direction,[0,1,0]);u/=np.linalg.norm(u);v=np.cross(direction/np.linalg.norm(direction),u)
  points=[anchor+direction*j/48+.075*(u*math.cos(a)+v*math.sin(a)) for j,a in enumerate(np.linspace(0,12*math.pi,49))]
  for a,b in zip(points,points[1:]):s.beam(a,b,.018,(204,209,199))
 # Two separately powered circuits. No control wire carries the load power.
 for x,color in ((-3.1,(95,125,135)),(3.1,(167,135,85))):
  s.box((x,.0,.95),(.54,.75,.65),color);s.box((x,0,1.32),(.32,.5,.08),(218,195,140))
 cylinder(s,(3.12,-.65,1.85),.28,.35,(243,214,117) if p['powered'] else (113,142,157),'z',n=24)
 s.box((-2.65,-.85,.81),(.75,.40,.12),(119,144,145))
 a=np.array([-2.95,-.85,.91]);b=np.array([-2.40,-.85,.91])
 s.beam(a,b+np.array([0,0,.38*(1-p['switch'])]),.035,(225,193,119))
 control=[(-3.1,0,1.35),(-3.1,-1.05,.83),(-2.95,-.85,.91),(-2.40,-.85,.91),(.2,-.55,.9),(.2,-.55,2.0),(-3.45,1.0,.83),(-3.1,0,.8)]
 load=[(3.1,0,1.35),(3.5,-.65,1.85),(3.12,-.65,1.85),(FIXED[0],0,.8),tuple(FIXED),tuple(point(LENGTH,-.11,angle)),tuple(PIVOT),(2.6,1.2,.83),(3.1,0,.8)]
 for points,color,skip in ((control,(97,151,172),2),(load,(188,151,76),4)):
  for n,(a,b) in enumerate(zip(points,points[1:])):
   if n!=skip:s.beam(a,b,.025,color)
 if p['current']>.01 and 'field' not in hidden:
  for j in range(4):
   points=[(.2+(.65+j*.10)*math.cos(a),.55*math.sin(a),1.4+.60*math.sin(a)) for a in np.linspace(0,2*math.pi,25)]
   for k,(a,b) in enumerate(zip(points,points[1:])):
    if (k+int(t*5))%5<3:s.beam(a,b,.012,(112,180,203))
 if p['powered'] and 'load' not in hidden:
  for k in range(15):sphere(s,path_point(load,(t*.22+k/15)%1),.033,(240,214,127),n=8,bands=4)
 return p
SHOTS=[((0,0,2.0),1.22,.65),((-.1,0,2.1),1.8,.30),((-.3,0,1.8),1.9,.28),((.4,0,2.5),2.2,.25),((1.5,0,2.1),1.9,.32),((.1,0,2.3),2.0,.30),((.3,0,2.1),1.9,.28),((0,0,2.0),1.22,.65)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 8.
