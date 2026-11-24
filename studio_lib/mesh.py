"""Reusable CPU perspective geometry from the owner-reviewed prototype."""
import math
import numpy as np
from PIL import Image,ImageDraw
W,H=720,1280
def ease(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)

def ramp(t,a,b): return ease((t-a)/(b-a))

def mix(a,b,p): return a+(b-a)*p

def unit(a): return a/np.linalg.norm(a)

class Scene:
    """A tiny perspective mesh renderer; all assets remain local and reusable."""
    def __init__(self,t,zoom,target,azimuth,elevation=10,raster_scale=1,lighting=False):
        self.t=t; self.glass_faces=[]; self.faces=[]; self.lines=[]; self.gear_marks=[]
        self.raster_scale=raster_scale;self.lighting=lighting;self.world_faces=[]
        self.target=np.array(target,dtype=float)
        self.eye=self.target+np.array([math.sin(azimuth)*16,-math.cos(azimuth)*16,elevation])/zoom
        self.forward=unit(self.target-self.eye)
        self.right=unit(np.cross(self.forward,[0,0,1])); self.up=np.cross(self.right,self.forward)
    def project(self,points):
        p=np.asarray(points)-self.eye; depth=p@self.forward
        return np.column_stack([W/2+780*(p@self.right)/depth,740-780*(p@self.up)/depth]),depth
    def face(self,points,color,bias=0.):
        """bias>0 sorts the face nearer to the viewer, so a small decal never sinks behind the larger surface it sits on."""
        p=np.asarray(points,float)
        dep=(p-self.eye)@self.forward
        if min(dep)<.2:
            clipped=[]
            for i,a in enumerate(p):
                b=p[(i+1)%len(p)];da=dep[i];db=dep[(i+1)%len(p)]
                if da>=.2:clipped.append(a)
                if (da>=.2)!=(db>=.2):clipped.append(a+(b-a)*((.2-da)/(db-da)))
            if len(clipped)<3:return
            p=np.array(clipped)
        if self.lighting:
            from studio_lib.visual_quality import lit_color
            color=lit_color(p,color,self.eye)
            self.world_faces.append(p.copy())
        q,dep=self.project(p)
        self.faces.append((float(dep.mean())-bias,[tuple(x) for x in q],color))
    def box(self,center,size,color,transform=None):
        x,y,z=center; a,b,c=np.array(size)/2
        p=np.array([[x+dx*a,y+dy*b,z+dz*c] for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
        if transform:p=transform(p)
        rgb=np.array(color)
        for ids,light in [([0,1,5,4],.79),([1,2,6,5],.69),([2,3,7,6],.9),([3,0,4,7],.94),([4,5,6,7],1.12),([0,3,2,1],.6)]:
            self.face(p[ids],tuple(np.clip(rgb*light,0,255).astype(int)))
    def beam(self,a,b,r,color,transform=None):
        a,b=np.array(a,float),np.array(b,float); d=unit(b-a)
        cross=unit(np.cross(d,[0,1,0] if abs(d[1])<.9 else [0,0,1]))*r
        other=np.cross(d,cross)
        p=np.array([a+cross+other,a-cross+other,a-cross-other,a+cross-other,b+cross+other,b-cross+other,b-cross-other,b+cross-other])
        if transform:p=transform(p)
        for ids in [[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7],[4,5,6,7]]:self.face(p[ids],color)
    def cylinder(self,center,r,length,color,angle=0,n=24):
        x,y,z=center
        rings=[np.array([[x+r*math.cos(a+angle),y+dy,z+r*math.sin(a+angle)] for a in np.linspace(0,2*math.pi,n,endpoint=False)]) for dy in [-length/2,length/2]]
        self.face(rings[0],color);self.face(rings[1],tuple(min(255,int(c*1.15)) for c in color))
        for i in range(n):self.face([rings[0][i],rings[0][(i+1)%n],rings[1][(i+1)%n],rings[1][i]],tuple(int(c*(.72+.18*math.sin(i/n*math.pi*2))) for c in color))
    def gear(self,center,r,teeth,angle,color):
        x,y,z=center; pts=[]
        for i in range(teeth*4):
            a=i/(teeth*4)*2*math.pi+angle; rr=r*(1.05 if i%4 in (1,2) else .92)
            pts.append([x+rr*math.cos(a),y-.10,z+rr*math.sin(a)])
        self.face(pts,color); self.cylinder(center,r*.3,.24,(53,70,80))
        for a in np.linspace(0,2*math.pi,6,endpoint=False):
            self.beam((x+.2*math.cos(a+angle),y-.13,z+.2*math.sin(a+angle)),(x+r*.8*math.cos(a+angle),y-.13,z+r*.8*math.sin(a+angle)),.045,(51,76,90))
        # One asymmetric painted spoke and tip make physical rotation readable.
        self.beam((x+r*.31*math.cos(angle),y-.18,z+r*.31*math.sin(angle)),(x+r*.88*math.cos(angle),y-.18,z+r*.88*math.sin(angle)),r*.055,(255,247,207))
        self.cylinder((x+r*.76*math.cos(angle),y-.20,z+r*.76*math.sin(angle)),r*.075,.045,(255,248,214),n=12)
        # Front-face paint belongs above the gear's single planar polygon.
        # Keep the large gear's mark on its exposed left/lower sector.
        marked=angle+(math.pi if r>.4 else 0)
        self.gear_marks.append(((x,y-.21,z),r,marked))
    def glass(self,points,rgba):
        """Translucent face (bottle glass): drawn after every solid face so the parts inside show through."""
        q,dep=self.project(np.asarray(points,float))
        if min(dep)>=.2:self.glass_faces.append((float(dep.mean()),[tuple(x) for x in q],rgba))
    def paint(self,im):
        d=ImageDraw.Draw(im)
        for _,p,c in sorted(self.faces,key=lambda x:-x[0]):d.polygon([tuple(v*self.raster_scale for v in point) for point in p],fill=c)
        for (x,y,z),r,a in self.gear_marks:
            q,_=self.project([(x+r*.38*math.cos(a),y,z+r*.38*math.sin(a)),(x+r*.79*math.cos(a),y,z+r*.79*math.sin(a))])
            q=q*self.raster_scale
            d.line([tuple(v) for v in q],fill=(255,247,207),width=(5 if r>.4 else 4)*self.raster_scale)
            px,py=q[-1];radius=3*self.raster_scale;d.ellipse((px-radius,py-radius,px+radius,py+radius),fill=(255,247,207))
        if self.glass_faces:
            over=Image.new('RGBA',im.size,(0,0,0,0));od=ImageDraw.Draw(over)
            for _,pg,rgba in sorted(self.glass_faces,key=lambda x:-x[0]):od.polygon([tuple(v*self.raster_scale for v in pt) for pt in pg],fill=rgba)
            im.paste(over,(0,0),over)
    def point(self,p):return tuple(self.project([p])[0][0])
