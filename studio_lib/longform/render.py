"""Native landscape procedural scenes. No downloaded clips or portrait panels."""
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from studio_lib.mesh import Scene,ease
from studio_lib.longform.contract import motion
WIDTH,HEIGHT=1280,720
class WideScene(Scene):
 def project(self,points):
  p=np.asarray(points)-self.eye;depth=p@self.forward
  return np.column_stack([WIDTH/2+1000*(p@self.right)/depth,HEIGHT*.46-1000*(p@self.up)/depth]),depth

def frame(t,timeline,plan):
 beats=timeline['beats'];index=min(len(beats)-1,next((i for i,b in enumerate(beats) if t<b['end']),len(beats)-1));beat=beats[index]
 phase=beat['action'];mechanism=plan['mechanism'];state=motion(t,mechanism,timeline);x=state['travel'];angle=state['angle']
 im=Image.new('RGB',(WIDTH,HEIGHT),(17,29,43));draw=ImageDraw.Draw(im)
 # Continuous small camera arc; close views keep the connected assembly in frame.
 zoom=1.45+.08*math.sin(t/23)**2;azimuth=(.95 if mechanism=='lead_screw' else .20)+.08*math.sin(t/28);sc=WideScene(t,zoom,(0,0,1.3),azimuth)
 blue=(63,170,210);gold=(237,175,60);steel=(135,156,170);red=(224,86,67)
 sc.box((0,0,.05),(9,5,.18),(36,54,69))
 if mechanism=='rack_pinion':
  for yy in (-.6,.6):sc.beam((-4,yy,.45),(4,yy,.45),.055,steel)
  sc.box((x,0,.68),(5.8,.8,.35),blue)
  # Rack pitch matches the marked pinion's circular pitch. Teeth are illustrative.
  pitch=2*math.pi*.6/16
  for i in range(-12,13):
   tx=x+i*pitch
   sc.box((tx,0,.92),(.10,.75,.13),gold)
  sc.gear((0,0,1.62),.6,16,angle,gold)
  sc.beam((0,-1.05,1.62),(0,1.05,1.62),.12,steel)
  for yy in (-1,1):sc.box((0,yy,.9),(.35,.3,1.4),steel)
  sc.box((x,0,.36),(1.2,1.4,.2),red)
  for xx in (-4.2,4.2):sc.box((xx,0,.6),(.2,1.5,.85),steel)
 elif mechanism=='lead_screw':
  for xx in (-.8,.8):sc.beam((xx,-3,.6),(xx,3,.6),.07,steel)
  sc.cylinder((0,0,1.2),.16,6,steel,n=16)
  # A visible continuous helix on the rotating screw; translation is derived from turns.
  points=[(.19*math.cos(a+angle),y,1.2+.19*math.sin(a+angle)) for y,a in [(y,2*math.pi*y/.45) for y in np.linspace(-3,3,120)]]
  for a,b in zip(points,points[1:]):sc.beam(a,b,.025,gold)
  for yy in (-3,3):sc.box((0,yy,.75),(.7,.35,1.1),steel)
  sc.box((0,x,1.2),(.75,.6,.65),gold)
  sc.box((0,x,.66),(2,.7,.25),blue)
  sc.box((0,x,1.72),(1,.55,.38),red)
  sc.cylinder((0,-3.35,1.2),.45,.16,blue,angle=angle,n=20)
  sc.beam((0,-3.5,1.2),(.4*math.cos(angle),-3.5,1.2+.4*math.sin(angle)),.035,gold)
 else:
  cx=state['cam_x'];cz=state['cam_z'];fz=state['follower_z']
  sc.cylinder((cx,0,cz),.8,.4,gold,n=40)
  sc.cylinder((0,-.27,1.5),.13,.6,steel,n=20)
  sc.beam((0,-.35,1.5),(.5*math.sin(angle),-.35,1.5+.5*math.cos(angle)),.035,red)
  sc.cylinder((0,0,fz),.16,.48,blue,angle=-angle,n=20)
  sc.beam((0,0,fz),(0,0,fz+1.15),.07,steel)
  for xx in (-1.4,1.4):sc.box((xx,0,1.9),(.18,.6,3.5),steel)
  sc.box((0,0,3.45),(3,.6,.22),steel)
  sc.box((0,0,fz+.35),(.65,.7,.13),red)
  sc.box((0,0,fz+1.15),(.6,.6,.18),blue)
  coil=[]
  for q in np.linspace(0,1,85):
   a=q*math.pi*2*7;coil.append((.23*math.sin(a),.23*math.cos(a),fz+.43+(3.32-fz-.43)*q))
  for a,b in zip(coil,coil[1:]):sc.beam(a,b,.018,gold)
 sc.paint(im)
 font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 try:small=ImageFont.truetype(font,22);large=ImageFont.truetype(font,44)
 except OSError:small=large=ImageFont.load_default()
 if t<4:draw.text((48,36),plan['hook'],font=large,fill=(248,244,229))
 draw.text((40,HEIGHT-40),'Illustration',font=small,fill=(166,185,202))
 draw.text((WIDTH-220,36),str(index+1)+' / '+str(len(beats)),font=small,fill=(166,185,202))
 return im
