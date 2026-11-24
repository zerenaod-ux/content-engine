"""Manual ratchet wrench head: sawtooth wheel, spring-loaded pawl and a hex bolt. Engine-owned geometry; simplified teaching model.
Forward stroke: the pawl sits against the steep face of a tooth, so the wheel and bolt turn with the handle.
Back stroke: the pawl rides up the sloped back of each tooth and clicks into the next gap; the wheel and bolt hold still.
Stroke size is a whole number of teeth, so the pawl always ends a back stroke resting in a gap."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient,cylinder
FLOOR=.30;GROUND=(34,47,59);DARK=True
C=np.array([0.,0.,2.7]);N=24;PITCH=2*math.pi/N;STROKE=3*PITCH
R0,R1=.78,.96;RH=1.5;STEEP=.15;ALPHA0=6*PITCH;LENGTH=6.4;GRIP=4.1

def profile(v):
 """Tooth radius at wheel phase v in [0,1): valley at 0, steep face up to the tip, then the long slope back down."""
 v%=1.
 return R0+(R1-R0)*(v/STEEP) if v<STEEP else R1-(R1-R0)*((v-STEEP)/(1-STEEP))

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 handle=STROKE*(e[2]-e[3]+e[4]-e[5])          # housing angle
 wheel=STROKE*(e[2]+e[4])                      # the wheel only ever advances
 slip=wheel-handle                             # how far the pawl has travelled over teeth
 v=(-slip/PITCH)%1.
 cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7])))
 return dict(beat=i,handle=handle,wheel=wheel,slip=slip,phase=v,pawl_r=profile(v),click=1. if v<STEEP and slip>1e-6 else 0.,cut=cut)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def at(angle,r,y):return (C[0]+r*math.cos(angle),y,C[2]+r*math.sin(angle))
def draw(s,t,tl,hidden=()):
 p=state(t,tl);H=p['handle'];Wa=p['wheel'];cut=p['cut'];beat=p['beat']
 steel,dark,brass,grip,warm=(186,198,206),(66,79,91),(222,176,84),(202,72,50),(236,152,72)
 # Fixed work plate and bolt shank behind the head.
 s.box((0,.95,2.45),(5.2,.30,5.4),(46,60,74))
 cylinder(s,(C[0],.55,C[2]),.20,.9,(176,138,66),'y',n=14)
 # Housing: back disc and rim band turn with the handle.
 back=[at(k*2*math.pi/48,RH,.34) for k in range(48)];s.face(back,(52,64,75))
 for k in range(48):
  a=k*2*math.pi/48+H;b=(k+1)*2*math.pi/48+H
  s.face([at(a,RH,.34),at(b,RH,.34),at(b,RH,-.30),at(a,RH,-.30)],tuple(int(c*(.78+.20*math.cos(a-.9))) for c in dark))
 # Handle: steel neck and a ridged red grip.
 d=(math.cos(H),math.sin(H))
 def along(r,y=0.):return (C[0]+r*d[0],y,C[2]+r*d[1])
 s.beam(along(RH-.1),along(GRIP),.17,(158,170,178));s.beam(along(GRIP),along(LENGTH),.27,grip)
 for k in range(9):
  r=GRIP+.25+k*.23;s.beam(along(r,-.27),along(r,.27),.035,(120,44,32))
 s.box(along(LENGTH+.08),(.22,.3,.3),(150,52,38))
 # Ratchet wheel (sawtooth), turning with Wa.
 if 'wheel' not in hidden:
  pts=[]
  for k in range(N):
   pts.append((k*PITCH+Wa,R0));pts.append((k*PITCH+STEEP*PITCH+Wa,R1))
  front=[at(a,r,-.10) for a,r in pts];rear=[at(a,r,.12) for a,r in pts]
  s.face(rear,(96,108,116))
  for j in range(len(pts)):
   k=(j+1)%len(pts);mid=(pts[j][0]+pts[k][0])/2
   s.face([front[j],front[k],rear[k],rear[j]],tuple(int(c*(.68+.30*math.cos(mid-1.1))) for c in steel))
  s.face(front,steel)
  cylinder(s,(C[0],-.02,C[2]),.46,.26,(120,134,142),'y',n=22)
 if 'bolt' not in hidden:
  hexa=[at(Wa+k*math.pi/3,.38,-.26) for k in range(6)];hexb=[at(Wa+k*math.pi/3,.38,-.12) for k in range(6)]
  for k in range(6):s.face([hexa[k],hexa[(k+1)%6],hexb[(k+1)%6],hexb[k]],tuple(int(c*(.74+.2*math.cos(k))) for c in brass))
  s.face(hexa,brass)
  s.beam(at(Wa,.04,-.30),at(Wa,.33,-.30),.032,(255,247,207))
 # Pawl: pivots on the housing, tip rides the tooth profile, spring presses it inward.
 tip=np.array(at(ALPHA0+H,p['pawl_r']+.03,-.10));pivot=np.array(at(ALPHA0+H+.50,1.30,-.10))
 if 'pawl' not in hidden:
  s.beam(tuple(pivot),tuple(tip),.11,warm if p['click'] else (214,128,62))
  s.box(tuple(tip),(.22,.22,.22),(255,196,110) if p['click'] else (232,150,70))
  cylinder(s,tuple(pivot),.11,.24,(150,162,170),'y',n=14)
 if 'spring' not in hidden:
  m=pivot+.62*(tip-pivot);ang=math.atan2(m[2]-C[2],m[0]-C[0]);start=np.array(at(ang,math.hypot(m[0]-C[0],m[2]-C[2]),-.10));wall=np.array(at(ang,1.43,-.10))
  side=np.array((-math.sin(ang),0,math.cos(ang)))*.075;pts=[start+(wall-start)*q/10+(side if q%2 else -side if q else 0) for q in range(11)]
  for a,b in zip(pts,pts[1:]):s.beam(tuple(a),tuple(b),.022,(190,200,190))
 # Input arrow at the grip (forward on drive strokes, backward on return strokes).
 if 'input' not in hidden and beat in (2,3,4,5):
  sign=1 if beat in (2,4) else -1;perp=np.array((-d[1],0,d[0]))*sign;base=np.array(along(5.3,-.40))+perp*.55;head=base+perp*1.3
  s.beam(tuple(base),tuple(head),.04,(120,205,230))
  for off in (-.28,.28):s.beam(tuple(head),tuple(head-perp*.34+np.array((d[0],0,d[1]))*off),.035,(120,205,230))
 # Cover plate lifts away for the cutaway.
 if 'door' not in hidden and cut<.99:
  lift=7.0*cut;cover=[(C[0]+RH*math.cos(k*2*math.pi/48+H),-.36,C[2]+lift+RH*math.sin(k*2*math.pi/48+H)) for k in range(48)]
  s.face(cover,(94,110,122))
  for k in range(6):
   a=k*math.pi/3+H+.3;s.box((C[0]+1.18*math.cos(a),-.40,C[2]+lift+1.18*math.sin(a)),(.16,.06,.16),(40,50,58))
 return p
SHOTS=[((2.7,0,3.5),1.4,.30),((0,0,2.7),1.9,.34),((1.9,0,3.5),1.25,.30),((-.1,0,2.95),2.6,.34),((-.2,0,3.15),3.4,.38),((0,0,2.8),2.4,.30),((0,0,2.7),2.9,.32),((2.7,0,3.5),1.4,.30)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
