"""Simplified three-wheel gate/fence padlock, not a commercial lock replica."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import cylinder,background as gradient
XS=(-1.18,0,1.18)
ANGLES=(1.2,-1.1,1.8)
RADIUS=.74
GATE_RADIUS=.50
WHEEL_Z=2.18
BAR_HIGH=WHEEL_Z+RADIUS+.065
BAR_LOW=WHEEL_Z+GATE_RADIUS+.065
FLOOR=.38
GROUND=(30,49,64)
DARK=True

def aligned(angles):return all(abs((a+math.pi)%(2*math.pi)-math.pi)<.07 for a in angles)

def state(t,tl):
 beats=tl['beats'];i=min(7,next((j for j,b in enumerate(beats) if t<b['end']),7));angles=list(ANGLES)
 for j,index in enumerate((2,3,4)):
  if i>index:angles[j]=0.
  elif i==index:angles[j]=ANGLES[j]*(1-ease(progress(t,beats[index])))
 # The fence can descend only when all three physical gate clearances align.
 clearance=min(1.,max(0.,(max(abs(a) for a in angles)-.025)/.045))
 free=1-ease(clearance) if aligned(angles) else 0.
 lift=ease(progress(t,beats[6]))*.9 if i==6 else .9 if i==7 else 0.
 if free<.999:lift=0.
 return dict(beat=i,angles=angles,bar_z=BAR_HIGH-(BAR_HIGH-BAR_LOW)*free,free=free,shackle=lift,
             cut=ease(progress(t,beats[1]))*(1-ease(progress(t,beats[7]))))

@functools.lru_cache(maxsize=1)
def background():return gradient((19,36,54),(40,66,82))

def wheel(s,x,angle,color,notches=True):
 # Axle is along x. The true notch removes outer material; it is not paint.
 n=72
 for k in range(n):
  a=k*2*math.pi/n;b=(k+1)*2*math.pi/n
  mid=(a+b)/2
  radial=GATE_RADIUS if notches and abs((mid+math.pi)%(2*math.pi)-math.pi)<.22 else RADIUS
  def pt(xx,r,beta):return (xx,-r*math.sin(beta+angle),WHEEL_Z+r*math.cos(beta+angle))
  for xx in (x-.39,x+.39):s.face([pt(xx,.20,a),pt(xx,radial,a),pt(xx,radial,b),pt(xx,.20,b)],color)
  s.face([pt(x-.39,radial,a),pt(x+.39,radial,a),pt(x+.39,radial,b),pt(x-.39,radial,b)],tuple(int(c*(.76+.18*math.cos(mid+angle))) for c in color))
  # Ribs and asymmetric index follow the wheel's own rigid rotation.
  if k%6==0:s.beam(pt(x-.34,radial+.012,a),pt(x+.34,radial+.012,a),.012,(226,217,178))
  if k==0:s.beam(pt(x-.34,radial+.02,a),pt(x+.34,radial+.02,a),.038,(234,104,73))
 # Solid boss and its mark show that the wheel moves around the fixed axle.
 cylinder(s,(x,0,WHEEL_Z),.18,.85,(162,177,181),'x',n=16)

def draw(s,t,tl,hidden=()):
 p=state(t,tl);cut=p['cut'];z=p['bar_z'];lift=p['shackle']
 # Original complete padlock body and shackle; its front has a normal wheel window.
 s.box((0,1.03,2.0),(4.45,.18,3.25),(151,113,51))
 s.box((0,.03,.55),(4.45,2.1,.26),(190,147,64))
 for x in (-2.12,2.12):s.box((x,.03,2.0),(.20,2.1,3.25),(204,160,70))
 s.box((0,-.94,1.10+7.5*cut),(4.45,.18,1.0),(211,168,74))
 s.box((0,-.94,3.28+7.5*cut),(4.45,.18,.72),(211,168,74))
 # Top cover has real openings for both shackle legs.
 s.box((0,.03,3.82+6*cut),(3.38,2.1,.18),(226,187,91))
 for x in (-2.17,2.17):s.box((x,.03,3.82+6*cut),(.12,2.1,.18),(226,187,91))
 for y in (-.86,.86):s.box((0,y,3.82+6*cut),(4.45,.30,.18),(226,187,91))
 for x in (-1.8,1.8):s.cylinder((x,-1.06,1.05+7.5*cut),.065,.04,(72,91,95),n=8)
 if 'wheels' not in hidden:
  for x,a,color in zip(XS,p['angles'],((193,202,194),(158,187,188),(194,173,129))):wheel(s,x,a,color,notches='gates' not in hidden)
 cylinder(s,(0,0,WHEEL_Z),.095,4.08,(55,77,89),'x',n=16)
 # Fence spans all three wheel gates. A single misaligned rim blocks it.
 if 'bar' not in hidden:
  s.box((.14,0,z),(3.52,.15,.13),(222,99,63))
  s.box((1.91,.0,z+.06),(.25,.29,.12),(237,141,78))
 # A guide and return spring press the fence toward the physical gate floors.
 for x in (-1.50,1.50):
  s.box((x,.86,2.1),(.12,.12,2.8),(76,108,119))
  s.beam((x,.86,3.50),(x,-.04,3.50),.05,(93,123,131))
  if 'spring' not in hidden:
   points=[(x+.09*math.cos(a),-.04+.09*math.sin(a),z+.13+(3.48-z-.13)*j/42) for j,a in enumerate(np.linspace(0,9*math.pi,43))]
   for a,b in zip(points,points[1:]):s.beam(a,b,.018,(177,192,188))
 # Right shackle leg has an actual notch corresponding to the sliding dog.
 if 'shackle' not in hidden:
  s.beam((-1.89,.09,1.12+lift),(-1.89,.09,4.72+lift),.13,(188,211,215))
  s.beam((1.89,.09,3.16+lift),(1.89,.09,4.72+lift),.13,(188,211,215))
  s.beam((1.89,.09,2.90+lift),(1.89,.09,2.98+lift),.13,(188,211,215))
  # A rear web retains structural continuity behind the visible front notch.
  s.beam((1.89,.18,2.95+lift),(1.89,.18,3.20+lift),.045,(142,170,178))
  arch=[(1.89*math.cos(a),.09,4.72+lift+1.89*math.sin(a)) for a in np.linspace(0,math.pi,33)]
  for a,b in zip(arch,arch[1:]):s.beam(a,b,.13,(197,217,216))
 return p

SHOTS=[((0,0,3.75),1.18,.42),((0,0,2.85),1.6,.66),((-1.10,0,2.80),2.25,.72),((0,0,2.80),2.25,.72),((.85,0,2.80),2.25,.72),((.75,0,2.90),2.05,.58),((.7,0,4.25),1.50,.38),((0,0,3.75),1.18,.42)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 5.0
