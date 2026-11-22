"""Small reusable physical solids for component-owned assemblies."""
import math
import numpy as np
from PIL import Image

def cylinder(s,center,r,length,color,axis='z',n=24):
 c=np.asarray(center,float);direction=np.array({'x':(1,0,0),'y':(0,1,0),'z':(0,0,1)}[axis],float)
 u=np.array((0,1,0) if axis=='x' else (1,0,0));v=np.cross(direction,u)
 rings=[np.array([c+direction*d+r*(u*math.cos(a)+v*math.sin(a)) for a in np.linspace(0,2*math.pi,n,endpoint=False)]) for d in (-length/2,length/2)]
 s.face(rings[0],color);s.face(rings[1],tuple(min(255,int(k*1.1)) for k in color))
 for i in range(n):s.face([rings[0][i],rings[0][(i+1)%n],rings[1][(i+1)%n],rings[1][i]],tuple(int(k*(.74+.18*math.cos(i*2*math.pi/n))) for k in color))

def sphere(s,center,r,color,n=18,bands=9):
 x,y,z=center
 for j in range(bands):
  a=-math.pi/2+j*math.pi/bands;b=a+math.pi/bands
  for k in range(n):
   c=k*2*math.pi/n;d=c+2*math.pi/n
   s.face([(x+r*math.cos(e)*math.cos(f),y+r*math.cos(e)*math.sin(f),z+r*math.sin(e)) for e,f in ((a,c),(a,d),(b,d),(b,c))],tuple(min(255,int(v*(.78+.19*math.cos(c-.5)+.08*math.sin(a)))) for v in color))

def background(top,bottom):
 """Studio backdrop: vertical gradient + soft key-light glow, faint blueprint grid, defocused light discs and a vignette.
 Deterministic (fixed seed) so cached renders stay identical."""
 from PIL import ImageFilter
 H,W=1280,720;a=np.linspace(0,1,H)[:,None,None]
 base=np.array(top,float)[None,None,:]*(1-a)+np.array(bottom,float)[None,None,:]*a
 base=np.broadcast_to(base,(H,W,3)).copy();dark=np.mean(top)<110
 y,x=np.mgrid[0:H,0:W];x=x/W;y=y/H
 glow=np.exp(-(((x-.5)/.55)**2+((y-.50)/.30)**2))[:,:,None]
 tint=np.array((70,130,170) if dark else (255,255,255),float)[None,None,:]
 base=base+glow*(tint*(.30 if dark else .09)-(base*0 if dark else 0))
 if not dark:base=base+glow*np.array((255,236,200),float)[None,None,:]*.03
 grid=np.zeros((H,W),float)
 grid[::80,:]=1;grid[:,::80]=1;grid[40::160,:]+=.5;grid=grid*(.045 if dark else .035)
 base=base*(1-grid[:,:,None])+grid[:,:,None]*(np.array((150,200,230),float) if dark else np.array((60,90,110),float))[None,None,:]
 rng=np.random.RandomState(7);layer=Image.new('RGB',(W,H),(0,0,0));from PIL import ImageDraw;d=ImageDraw.Draw(layer)
 for k in range(16):
  r=int(rng.uniform(24,84));cx=int(rng.uniform(0,W));cy=int(rng.choice([rng.uniform(40,380),rng.uniform(900,1240)]))
  col=(120,190,230) if dark else (255,244,218) if k%3 else (255,214,170)
  d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=tuple(int(c*(.55 if dark else .75)) for c in col))
 bok=np.asarray(layer.filter(ImageFilter.GaussianBlur(22)),float)
 base=base+bok*(.20 if dark else .10)
 vig=1-.20*np.clip((((x-.5)/.62)**2+((y-.5)/.66)**2),0,1.4)[:,:,None]
 base=base*vig
 return Image.fromarray(np.uint8(np.clip(base,0,255)))

def path_point(points,u):
 lengths=[np.linalg.norm(np.subtract(b,a)) for a,b in zip(points,points[1:])];remaining=min(.999999,max(0,u))*sum(lengths)
 for a,b,length in zip(points,points[1:],lengths):
  if remaining<=length:return np.asarray(a)+(np.asarray(b)-a)*(remaining/length)
  remaining-=length
 return np.asarray(points[-1])
