"""Representative camera iris: rigid pivoted blades and a shared cam ring.

Visible blade portions are clipped by the fixed housing. Optical markers and
sensor brightness are illustrative; this is not a lens ray-tracing simulation.
"""
import functools,math
import numpy as np
from PIL import Image
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress

N=7
PIVOT_RADIUS=2.2
INNER_OFFSET=-1.16
OPEN_ANGLE=math.radians(20)
CLOSED_ANGLE=math.radians(48)
CZ=3.05
IRIS_Y=-1.15

def rotate(point,angle):
 c,s=math.cos(angle),math.sin(angle);x,z=point
 return np.array([c*x-s*z,s*x+c*z])

def pivot(k):return rotate((PIVOT_RADIUS,0),k*2*math.pi/N)

def blade_points(k,angle):
 """Full rigid blade geometry, before the surrounding housing hides excess."""
 a=k*2*math.pi/N+angle;p=pivot(k)
 return np.array([p+rotate(v,a) for v in ((INNER_OFFSET,-3.8),(.35,-3.8),(.35,3.8),(INNER_OFFSET,3.8))])

def control_pin(k,angle):
 return pivot(k)+rotate((-.4,.1),k*2*math.pi/N+angle)

def ring_angle(angle):return .55*(angle-OPEN_ANGLE)

def slot_point(k,blade_angle):
 """A point in ring coordinates; its current rigid transform meets the pin."""
 return rotate(control_pin(k,blade_angle),-ring_angle(blade_angle))

def apothem(angle):return PIVOT_RADIUS*math.cos(angle)+INNER_OFFSET
def opening_area(angle):return N*apothem(angle)**2*math.tan(math.pi/N)

def passes(point,angle):
 p=np.asarray(point);d=apothem(angle)
 return all(np.dot(p,rotate((1,0),k*2*math.pi/N+angle))<d-1e-8 for k in range(N))

def clip_polygon(points,radius=2.30):
 """Only the blade surface exposed inside a fixed circular housing window."""
 polygon=[np.array(p,float) for p in points]
 for i in range(48):
  normal=rotate((1,0),2*math.pi*i/48);limit=radius*math.cos(math.pi/48)
  if not polygon:break
  result=[]
  for j,a in enumerate(polygon):
   b=polygon[(j+1)%len(polygon)];da=np.dot(a,normal)-limit;db=np.dot(b,normal)-limit
   if da<=0:result.append(a)
   if (da<=0)!=(db<=0):result.append(a+(b-a)*(da/(da-db)))
  polygon=result
 return polygon

@functools.lru_cache(maxsize=1024)
def visible_blades(angle):
 return tuple(tuple(tuple(p) for p in clip_polygon(blade_points(k,angle))) for k in range(N))

def state(t,tl):
 beats=tl['beats'];i=min(7,next((i for i,b in enumerate(beats) if t<b['end']),7))
 closed=0. if i<3 else ease(progress(t,beats[3])) if i==3 else 1. if i==4 else 1-ease(progress(t,beats[5])) if i==5 else 0.
 angle=OPEN_ANGLE+(CLOSED_ANGLE-OPEN_ANGLE)*closed
 cut=ease(progress(t,beats[2]))*(1-ease(progress(t,beats[7])))
 return {'beat':i,'angle':angle,'ring_angle':ring_angle(angle),'cut':cut,
         'area':opening_area(angle),'brightness':opening_area(angle)/opening_area(OPEN_ANGLE)}

def annulus(s,center,inner,outer,length,color,angle=0,n=48):
 x,y,z=center
 for k in range(n):
  a=angle+k*2*math.pi/n;b=angle+(k+1)*2*math.pi/n
  for yy,factor in ((y-length/2,1.),(y+length/2,.72)):
   s.face([(x+inner*math.cos(a),yy,z+inner*math.sin(a)),(x+outer*math.cos(a),yy,z+outer*math.sin(a)),(x+outer*math.cos(b),yy,z+outer*math.sin(b)),(x+inner*math.cos(b),yy,z+inner*math.sin(b))],tuple(int(c*factor) for c in color))
  s.face([(x+outer*math.cos(a),y-length/2,z+outer*math.sin(a)),(x+outer*math.cos(b),y-length/2,z+outer*math.sin(b)),(x+outer*math.cos(b),y+length/2,z+outer*math.sin(b)),(x+outer*math.cos(a),y+length/2,z+outer*math.sin(a))],tuple(int(c*(.65+.18*math.cos(a))) for c in color))

@functools.lru_cache(maxsize=1)
def background():
 y,x=np.mgrid[0:1280,0:720]
 glow=np.exp(-((x-360)**2/(430**2)+(y-650)**2/(620**2)))
 return Image.fromarray(np.uint8(np.stack([17+11*glow,22+15*glow,29+20*glow],axis=2)))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);angle=p['angle'];cut=p['cut']
 s.face([(4.1*math.cos(a),.4+1.6*math.sin(a),.37) for a in np.linspace(0,2*math.pi,40,endpoint=False)],(16,20,26))
 # A hollow camera body preserves a real optical path to the sensor.
 s.box((0,.6,.55),(6.2,2.5,.25),(48,58,67))
 s.box((0,1.8,3.0),(6.2,.18,4.9),(39,51,64))
 for x in (-3.,3.):s.box((x,.55,3.0),(.2,2.5,4.9),(51,66,79))
 s.box((3.25,-.2,2.5),(.7,1.8,3.8),(43,56,64))
 for z in np.linspace(1.,3.8,10):s.box((3.62,-.6,z),(.025,.65,.06),(77,87,91))
 # The shell lifts only as a clearly simplified cutaway, never disappears.
 s.box((0,.55,5.55+2.4*cut),(6.2,2.5,.22),(54,68,80))
 s.box((-1.4,.65,5.82+2.4*cut),(1.1,.85,.35),(45,59,71))
 s.cylinder((1.5,-.1,5.75+2.4*cut),.36,.25,(189,159,101),n=24)
 for x in (-2.6,2.6):
  for z in (.9,5.1):s.cylinder((x,-.72,z),.085,.08,(183,192,191),n=8)
 annulus(s,(0,-.55,CZ),1.35,2.42,.8,(50,65,77))
 # Fixed retaining plate, moving ring, and individual overlapping metal blades.
 annulus(s,(0,-.98,CZ),1.24,2.40,.13,(93,112,126))
 if 'blades' not in hidden:
  for k,polygon in enumerate(visible_blades(round(angle,6))):
   y=IRIS_Y-k*.008
   s.face([(x,y,CZ+z) for x,z in polygon],(126+4*k,143+3*k,153+3*k))
   # An asymmetric fine mark makes each rigid blade's pivoting visible.
   a=pivot(k)+rotate((-.7,.08),k*2*math.pi/N+angle)
   b=pivot(k)+rotate((-.9,.08),k*2*math.pi/N+angle)
   s.beam((a[0],y-.015,CZ+a[1]),(b[0],y-.015,CZ+b[1]),.018,(218,225,225))
 if 'ring' not in hidden:
  annulus(s,(0,-1.32,CZ),1.55,2.08,.10,(208,143,79),p['ring_angle'])
  for k in range(N):
   points=[rotate(slot_point(k,beta),p['ring_angle']) for beta in np.linspace(OPEN_ANGLE,CLOSED_ANGLE,17)]
   for a,b in zip(points,points[1:]):s.beam((a[0],-1.39,CZ+a[1]),(b[0],-1.39,CZ+b[1]),.027,(48,63,74))
   a=rotate((2.03,0),k*2*math.pi/N+p['ring_angle'])
   s.cylinder((a[0],-1.40,CZ+a[1]),.045,.025,(255,225,141),n=8)
 if 'pins' not in hidden:
  for k in range(N):
   x,z=pivot(k);s.cylinder((x,-1.29,CZ+z),.075,.25,(217,224,224),n=12)
   q=control_pin(k,angle)
   s.beam((q[0],-1.17,CZ+q[1]),(q[0],-1.46,CZ+q[1]),.045,(229,212,146))
   s.cylinder((q[0],-1.48,CZ+q[1]),.066,.04,(247,218,139),n=12)
 # Persistent front cap/glass is moved aside for the internal explanation.
 if 'cover' not in hidden:
  lift=8.0*cut
  annulus(s,(0,-1.9,CZ+lift),1.30,2.45,.35,(38,53,64))
  annulus(s,(0,-2.10,CZ+lift),1.24,1.30,.035,(61,121,144))
  for side in (-1,1):s.beam((side*.91,-2.13,CZ+lift+.62),(side*1.05,-2.13,CZ+lift+.39),.026,(133,185,196))
  for k in range(18):
   a=k*2*math.pi/18;s.beam((2.28*math.cos(a),-2.10,CZ+lift+2.28*math.sin(a)),(2.40*math.cos(a),-2.10,CZ+lift+2.40*math.sin(a)),.025,(112,126,131))
 # A fixed-gain, fixed-time exposure illustration, not optical image formation.
 if 'sensor' not in hidden:
  s.box((0,1.25,CZ),(2.0,.12,2.0),(35,43,61))
  brightness=.12+.88*p['brightness']
  for row in range(8):
   for col in range(10):
    target=(205,188,150) if (row//2+col//2)%2 else (90,143,164)
    rgb=tuple(int(c*brightness) for c in target)
    s.box((-1.02+col*.225,1.16,CZ-.75+row*.215),(.205,.025,.195),rgb)
 if p['beat']>=1 and 'light' not in hidden:
  for k in range(49):
   x=((k%7)-3)*.30;z=((k//7)-3)*.30
   clear=passes((x,z),angle);end=1.12 if clear else IRIS_Y-.10
   q=(t*.48+k*.073)%1;y=-5.2+q*(end+5.2)
   s.beam((x,y-.13,CZ+z),(x,y+.08,CZ+z),.016,(251,205,99))
 return p

SHOTS=[((.25,-.2,3.05),1.6,.36),
       ((0,-1.8,CZ),2.1,.18),
       ((0,-1.15,CZ),2.0,.12),
       ((0,-1.2,CZ),2.05,.06),
       ((0,-1.2,CZ),2.1,.04),
       ((0,-1.2,CZ),2.05,.08),
       ((0,1.1,CZ),1.85,.95),
       ((.25,-.2,3.05),1.6,.36)]
def shot(i):return SHOTS[min(i,7)]

def elevation(t,tl):
 i=min(7,next((i for i,b in enumerate(tl['beats']) if t<b['end']),7));b=tl['beats'][i]
 values=[10,5,3,2.8,1.5,2.8,14,10]
 blend=ease((t-b['start'])/1.4) if i else 1
 return values[max(0,i-1)]*(1-blend)+values[i]*blend
