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
 a=np.linspace(0,1,1280)[:,None,None]
 return Image.fromarray(np.uint8(np.broadcast_to(np.array(top)[None,None,:]*(1-a)+np.array(bottom)[None,None,:]*a,(1280,720,3))).copy())

def path_point(points,u):
 lengths=[np.linalg.norm(np.subtract(b,a)) for a,b in zip(points,points[1:])];remaining=min(.999999,max(0,u))*sum(lengths)
 for a,b,length in zip(points,points[1:],lengths):
  if remaining<=length:return np.asarray(a)+(np.asarray(b)-a)*(remaining/length)
  remaining-=length
 return np.asarray(points[-1])
