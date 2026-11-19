"""A closed-end, non-locking metal zipper with rigid interleaving elements."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
FLOOR=.30;GROUND=(194,207,213);DARK=False
START=-4.4;END=4.55;PITCH=.5
LEFT=np.arange(-3.75,3.76,PITCH)
RIGHT=LEFT+.25

def separation(x,slider):return .6*ease((x-slider+.55)/1.1)
def tooth(side,x,slider):
 # Heads cross the centreline; staggered opposing stems occupy the gaps.
 profile=[(-.07,-.2),(.07,-.2),(.07,.05),(.13,.05),(.13,.22),(-.13,.22),(-.13,.05),(-.07,.05)]
 return tooth_pose(side,x,slider,profile)
def tooth_pose(side,x,slider,points):
 # A rigid element follows its fabric tape's tangent. Keeping heads parallel
 # while the tapes curve would make them interpenetrate inside the slider.
 u=(x-slider+.55)/1.1;slope=.6*(6*u-6*u*u)/1.1 if 0<u<1 else 0.
 angle=math.atan(slope);c=math.cos(angle);s=math.sin(angle);sep=separation(x,slider)
 return [(x+xx*c+(yy+.2)*s,side*(.2+sep+xx*s-(yy+.2)*c)) for xx,yy in points]

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 if i<2:x=START
 elif i==2:x=START+2.8*ease(progress(t,b[2]))
 elif i==3:x=-1.6+3.2*ease(progress(t,b[3]))
 elif i==4:x=1.6+(END-1.6)*ease(progress(t,b[4]))
 elif i==5:x=END
 elif i==6:x=END+(START-END)*ease(progress(t,b[6]))
 else:x=START
 joined=sum(separation(a,x)<.02 for a in list(LEFT)+list(RIGHT))
 return dict(beat=i,slider=x,joined=float(joined),cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7]))))
@functools.lru_cache(maxsize=1)
def background():return gradient((238,245,248),(192,211,219))
def prism(s,points,z,height,color):
 for h in (z,z+height):s.face([(x,y,h) for x,y in points],color)
 for j,a in enumerate(points):
  b=points[(j+1)%len(points)];s.face([(a[0],a[1],z),(b[0],b[1],z),(b[0],b[1],z+height),(a[0],a[1],z+height)],tuple(int(c*.82) for c in color))
def draw(s,t,tl,hidden=()):
 p=state(t,tl);x=p['slider'];cut=p['cut']
 if 'tapes' not in hidden:
  for side in (-1,1):
   xs=np.linspace(-5.2,5.25,60)
   for a,b in zip(xs,xs[1:]):
    ya=side*(.2+separation(a,x));yb=side*(.2+separation(b,x))
    s.face([(a,ya,1.35),(b,yb,1.35),(b,yb+side*.72,1.35),(a,ya+side*.72,1.35)],(46,112,142))
    s.beam((a,ya+side*.48,1.365),(b,yb+side*.48,1.365),.009,(157,184,184))
 if 'teeth' not in hidden:
  for side,positions in ((-1,LEFT),(1,RIGHT)):
   for a in positions:prism(s,tooth(side,a,x),1.37,.18,(204,174,104))
 # Narrow joined throat grows into two guide channels ahead of the slider.
 outline=[(x-.68,-.45),(x+.68,-1.05),(x+.68,1.05),(x-.68,.45)]
 if 'slider' not in hidden:
  prism(s,outline,1.26,.08,(144,166,179));prism(s,outline,1.78+5.7*cut,.09,(167,184,188))
  s.box((x-.22,0,2.01+5.7*cut),(.24,.35,.26),(132,154,168))
  for y in (-.20,.20):s.beam((x-.22,y,2.1+5.7*cut),(x-1.1,y,2.18+5.7*cut),.035,(194,209,207))
  for xx in (x-.22,x-1.1):s.beam((xx,-.20,2.13+5.7*cut),(xx,.20,2.13+5.7*cut),.035,(194,209,207))
 if 'divider' not in hidden:prism(s,[(x-.12,0),(x+.64,-.27),(x+.64,.27)],1.35,.35,(111,140,155))
 if 'guides' not in hidden:
  for side in (-1,1):
   points=[(a,side*(.285+separation(a,x)),1.47) for a in np.linspace(x-.55,x+.55,18)]
   for a,b in zip(points,points[1:]):s.beam(a,b,.025,(139,167,180))
 # Closed-end stop joins both tapes; separate top stops bound slider travel.
 s.box((-5.12,0,1.44),(.16,1.80,.24),(131,152,166))
 for side in (-1,1):s.box((5.2,side*(.2+separation(5.2,x)),1.50),(.14,.18,.25),(130,151,163))
 return p
SHOTS=[((0,0,1.35),1.02,.25),((-3.6,0,1.5),1.55,.35),((-2.5,0,1.5),1.9,.35),((0,0,1.5),2.15,.40),((2.8,0,1.5),1.9,.35),((1.0,0,1.5),1.75,.35),((0,0,1.5),1.35,.25),((0,0,1.35),1.02,.25)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 12.
