"""Representative direct-acting tank inlet valve with a buoyant rigid lever.

Time and flow markers are schematic. No CFD, pump or electronic controller.
"""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import cylinder,sphere,background as gradient,path_point
LOW,MID,HIGH=1.25,2.25,3.25
PIVOT=np.array([-2.1,0,3.35]);ARM=2.45;FLOAT_RADIUS=.48
SEAT=4.02
HIGH_ANGLE=math.asin((HIGH+.18-PIVOT[2])/ARM)
STEM=SEAT-.04-(PIVOT[2]+.42*math.sin(HIGH_ANGLE)+.1325)
FLOOR=.38
GROUND=(229,217,194)
DARK=False

def physical(level):
 theta=math.asin((level+.18-PIVOT[2])/ARM)
 center=PIVOT+np.array([ARM*math.cos(theta),0,ARM*math.sin(theta)])
 high_angle=math.asin((HIGH+.18-PIVOT[2])/ARM)
 gap=.42*(math.sin(high_angle)-math.sin(theta))
 return dict(level=level,float_z=float(center[2]),float_center=center.tolist(),angle=theta,
             gap=gap,plug_z=SEAT-.04-gap,flow=gap/(.42*(math.sin(high_angle)-math.sin(math.asin((LOW+.18-PIVOT[2])/ARM)))))

def state(t,tl):
 beats=tl['beats'];i=min(7,next((j for j,b in enumerate(beats) if t<b['end']),7));u=ease(progress(t,beats[i]));drain=0.
 if i<2:level=LOW
 elif i==2:level=LOW+(MID-LOW)*u
 elif i==3:level=MID+(HIGH-MID)*u
 elif i==4:level=HIGH
 elif i==5:
  drain=ease(min(1,progress(t,beats[i])/.15));level=HIGH-(HIGH-LOW)*ease(max(0,(progress(t,beats[i])-.15)/.85))
 elif i==6:
  drain=1-ease(min(1,progress(t,beats[i])/.12));level=LOW+(HIGH-LOW)*ease(max(0,(progress(t,beats[i])-.12)/.88))
 else:level=HIGH
 p=physical(level);p.update(beat=i,drain=drain,cut=ease(progress(t,beats[1]))*(1-ease(progress(t,beats[7]))))
 return p

@functools.lru_cache(maxsize=1)
def background():return gradient((250,243,226),(223,216,198))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);level=p['level'];cut=p['cut'];float_center=np.array(p['float_center']);theta=p['angle']
 # The complete tank, connected supply and draw-off pipes remain one assembly.
 s.box((0,.1,.52),(6.15,2.5,.25),(76,119,123))
 s.box((0,1.22,2.45),(6.15,.16,3.9),(83,133,137))
 for x in (-3.,3.):s.box((x,.05,2.45),(.16,2.4,3.9),(96,148,148))
 s.box((0,-1.17,2.45+7.5*cut),(6.15,.16,3.9),(102,158,155))
 s.box((0,.05,4.44+5*cut),(6.3,2.55,.13),(175,194,178))
 for x in (-2.8,2.8):
  for z in (.8,4.1):s.cylinder((x,-1.29,z+7.5*cut),.065,.06,(229,218,178),n=8)
 # Tank water is translucent in concept, a cutaway surface in this opaque renderer.
 if 'water' not in hidden:
  s.box((0,.05,(.66+level)/2),(5.78,2.15,max(.02,level-.66)),(62,150,178))
  s.face([(-2.89,-1.03,level),(2.89,-1.03,level),(2.89,1.12,level),(-2.89,1.12,level)],(124,207,215))
 # Sight gauge on the outside provides context before the shell lifts.
 s.box((2.65,-1.31,2.5),( .22,.12,3.15),(40,80,88))
 s.box((2.65,-1.39,(.95+level)/2),(.105,.04,max(.02,level-.95)),(121,211,221))
 for z in np.arange(1.,4.01,.5):s.beam((2.83,-1.37,z),(2.98,-1.37,z),.015,(225,228,203))
 # Fixed supply housing and supported shutoff seat.
 inlet=[(-4.0,.0,4.25),(-2.0,.0,4.25),(-1.70,.0,4.25)]
 for a,b in zip(inlet,inlet[1:]):s.beam(a,b,.14,(170,135,75))
 s.box((-1.68,.19,4.02),(.70,.35,.82),(185,151,90))
 # An exposed longitudinal cutaway leaves seat, washer and stem visible.
 if 'seat' not in hidden:
  for x in (-1.92,-1.44):s.box((x,0,SEAT),(.24,.40,.08),(220,211,169))
  for y in (-.155,.155):s.box((-1.68,y,SEAT),(.24,.09,.08),(220,211,169))
 if 'plug' not in hidden:
  cylinder(s,(-1.68,-.05,p['plug_z']-.035),.22,.07,(189,80,65),'z',n=20)
  s.beam((-1.68,-.05,p['plug_z']-.07),(-1.68,-.05,p['plug_z']-STEM),.045,(214,211,175))
  s.box((-1.68,0,p['plug_z']-STEM),(.58,.25,.065),(218,204,153))
 # The rounded lever follower bears on a horizontal sliding platform. All
 # coordinates derive from the same fixed pivot and float angle.
 contact=PIVOT+np.array([.42*math.cos(theta),0,.42*math.sin(theta)])
 if 'rod' not in hidden:
  s.beam(PIVOT,float_center,.065,(224,183,91))
  sphere(s,contact,.10,(236,208,135),n=12,bands=6)
 if 'float' not in hidden:sphere(s,float_center,FLOAT_RADIUS,(231,169,70))
 s.box(tuple(PIVOT+[-.1,.18,-.04]),(.35,.40,.45),(55,83,89));s.cylinder(tuple(PIVOT+[0,-.13,0]),.14,.26,(210,219,201),n=18)
 # Discharge bends into the tank; no particles cross a closed inlet seat.
 spout=[(-1.38,.0,3.96),(-1.0,.0,3.96),(-1.0,.0,3.48)]
 for a,b in zip(spout,spout[1:]):s.beam(a,b,.115,(172,140,80))
 if 'flow' not in hidden and p['flow']>.001 and (p['beat']>2 or (p['beat']==2 and progress(t,tl['beats'][2])>0)):
  for k in range(max(1,round(16*p['flow']))):
   a=path_point([(-4.,-.05,4.25),(-1.68,-.05,4.25),(-1.68,-.05,p['plug_z']+.08),(-1.,-.05,3.96),(-1.,-.05,level+.035)],(t*.45+k*.087)%1)
   sphere(s,a,.047,(186,238,242),n=8,bands=4)
 # A separate draw-off valve explains the new demand, never a magic water loss.
 outlet=[(2.4,-.2,1.20),(3.55,-.2,1.20),(3.55,-.2,.95)]
 for a,b in zip(outlet,outlet[1:]):s.beam(a,b,.14,(174,136,73))
 s.cylinder((3.35,-.23,1.20),.23,.34,(197,164,99),n=18)
 s.beam((3.35,-.45,1.20),(3.35+.32*math.sin(p['drain']*math.pi/2),-.45,1.20+.32*math.cos(p['drain']*math.pi/2)),.045,(177,75,61))
 if p['drain']>.2 and 'drain' not in hidden:
  for k in range(8):sphere(s,path_point([(3.55,-.2,.91),(3.55,-.2,.43)],(t*.8+k/8)%1),.065,(146,220,230),n=8,bands=4)
 return p

SHOTS=[((-.2,0,2.5),1.25,.35),((-.5,0,2.8),1.5,.30),((-.45,0,2.8),1.65,.28),((-.8,0,3.3),2.0,.22),((-.8,0,3.3),2.0,.22),((.1,0,2.6),1.5,.35),((-.5,0,2.8),1.6,.28),((-.2,0,2.5),1.25,.35)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.5
