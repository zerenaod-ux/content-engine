"""Rich reusable parts for hand-built machines: real tooth profiles, chamfers, helical springs, tapered links.

Every part is plain faceted geometry drawn into a mesh.Scene. The scene's own lighting shades each facet by its normal,
so bevels, flanks and chamfers read as metal without textures. Machine front view: X across, Z up, Y is depth (towards the viewer is -Y).
All functions are deterministic and return the key points a machine needs for motion (for example a gear's tooth tip radius)."""
import math
import numpy as np

def _unit(v):
 v=np.asarray(v,float);n=np.linalg.norm(v)
 return v/n if n>1e-12 else v

def shade(color,k):return tuple(int(min(255,max(0,c*k))) for c in color)

def _perp(d):
 d=_unit(d);a=np.array((0.,0.,1.)) if abs(d[2])<.9 else np.array((1.,0.,0.))
 u=_unit(np.cross(d,a));return u,np.cross(d,u)

def tube(s,a,b,r,color,n=16,chamfer=0.,cap=True,r_end=None):
 """Round bar or tapered pin from a to b. chamfer shrinks both end rims for a machined look."""
 a=np.asarray(a,float);b=np.asarray(b,float);d=_unit(b-a);u,v=_perp(d)
 length=float(np.linalg.norm(b-a));ch=min(chamfer,length*.25,r*.8)
 r1=r;r2=r if r_end is None else r_end
 def ring(p,rad):return [p+rad*(u*math.cos(k*2*math.pi/n)+v*math.sin(k*2*math.pi/n)) for k in range(n)]
 stations=[(a,r1-ch if ch else r1)]
 if ch:stations.append((a+d*ch,r1))
 if ch:stations.append((b-d*ch,r2))
 stations.append((b,r2-ch if ch else r2))
 rings=[ring(p,rad) for p,rad in stations]
 for lo,hi in zip(rings,rings[1:]):
  for k in range(n):
   j=(k+1)%n;shine=.62+.38*(.5+.5*math.cos(k*2*math.pi/n-.9))
   s.face([lo[k],lo[j],hi[j],hi[k]],shade(color,shine+.18))
 if cap:
  s.face(rings[0],shade(color,.9));s.face(rings[-1],shade(color,1.08))
 return {'axis':d,'length':length}

def disc(s,c,r,y,color,n=40,angle=0.):
 c=np.asarray(c,float)
 pts=[(c[0]+r*math.cos(angle+k*2*math.pi/n),y,c[2]+r*math.sin(angle+k*2*math.pi/n)) for k in range(n)]
 s.face(pts,color);return pts

def annulus(s,c,r_out,r_in,y,color,n=40,angle=0.):
 c=np.asarray(c,float)
 for k in range(n):
  a=angle+k*2*math.pi/n;b=a+2*math.pi/n
  s.face([(c[0]+r_out*math.cos(a),y,c[2]+r_out*math.sin(a)),(c[0]+r_out*math.cos(b),y,c[2]+r_out*math.sin(b)),(c[0]+r_in*math.cos(b),y,c[2]+r_in*math.sin(b)),(c[0]+r_in*math.cos(a),y,c[2]+r_in*math.sin(a))],color)

def tooth_profile(teeth,r,angle=0.,tip=.12,root=.14,flat=.30):
 """Outline of a spur gear: per tooth root arc, straight flank up, flat tip, flank down. Returns [(theta, radius)].
 tip/root are tooth height fractions of the pitch radius (outside/inside the pitch circle); flat is the tip width as a fraction of the pitch angle."""
 pitch=2*math.pi/teeth;pts=[]
 for k in range(teeth):
  a=angle+k*pitch
  pts+= [(a+.02*pitch,r*(1-root)),(a+.20*pitch,r*(1-root)),(a+(.50-.5*flat)*pitch,r*(1+tip)),(a+(.50+.5*flat)*pitch,r*(1+tip)),(a+.80*pitch,r*(1-root)),(a+.98*pitch,r*(1-root))]
 return pts

def gear(s,c,r,teeth,angle,thick,color,y=0.,tip=.12,root=.14,hub=.30,holes=5,hole_r=.12,mark=True):
 """Spur gear with real tooth flanks, a recessed web, lightening holes, a machined hub and one painted index tooth.
 Its front face is at y-thick/2 (towards the viewer). Returns tip and root radius so a machine can mesh or time against it."""
 c=np.asarray(c,float);prof=tooth_profile(teeth,r,angle,tip,root);yf=y-thick/2;yw=yf+.05;rw=r*(1-root)*.88
 front=[(c[0]+rr*math.cos(a),yf,c[2]+rr*math.sin(a)) for a,rr in prof]
 back=[(c[0]+rr*math.cos(a),y+thick/2,c[2]+rr*math.sin(a)) for a,rr in prof]
 s.face(back,shade(color,.62),bias=-(r+thick))   # the gear's own far face always paints first
 for k in range(len(prof)):
  j=(k+1)%len(prof);mid=(prof[k][0]+prof[j][0])/2
  s.face([front[k],front[j],back[j],back[k]],shade(color,.58+.42*(.5+.5*math.cos(mid-1.0))),bias=-.5*thick)
  # rim face between the tooth outline and the web circle (a ring, so the web can sit lower)
  a0,a1=prof[k][0],prof[j][0]
  s.face([front[k],front[j],(c[0]+rw*math.cos(a1),yf,c[2]+rw*math.sin(a1)),(c[0]+rw*math.cos(a0),yf,c[2]+rw*math.sin(a0))],color)
 nw=max(36,teeth*2)
 for k in range(nw):
  a=angle+k*2*math.pi/nw;b=a+2*math.pi/nw
  s.face([(c[0]+rw*math.cos(a),yw,c[2]+rw*math.sin(a)),(c[0]+rw*math.cos(b),yw,c[2]+rw*math.sin(b)),(c[0]+r*hub*math.cos(b),yw,c[2]+r*hub*math.sin(b)),(c[0]+r*hub*math.cos(a),yw,c[2]+r*hub*math.sin(a))],shade(color,.86))
 for h in range(holes):
  a=angle+h*2*math.pi/holes+math.pi/holes;mid=(rw+r*hub)/2;hc=(c[0]+mid*math.cos(a),0,c[2]+mid*math.sin(a));hr=r*hole_r
  for k in range(14):
   q0=k*2*math.pi/14;q1=q0+2*math.pi/14
   s.face([(hc[0]+hr*1.35*math.cos(q0),yw-.012,hc[2]+hr*1.35*math.sin(q0)),(hc[0]+hr*1.35*math.cos(q1),yw-.012,hc[2]+hr*1.35*math.sin(q1)),(hc[0]+hr*math.cos(q1),yw-.012,hc[2]+hr*math.sin(q1)),(hc[0]+hr*math.cos(q0),yw-.012,hc[2]+hr*math.sin(q0))],shade(color,1.15),bias=.14)
  s.face([(hc[0]+hr*math.cos(q*2*math.pi/14),yw-.016,hc[2]+hr*math.sin(q*2*math.pi/14)) for q in range(14)],(24,32,40),bias=.16)
 tube(s,(c[0],yf-.16,c[2]),(c[0],y+thick/2+.10,c[2]),r*hub,shade(color,1.04),n=20,chamfer=r*.05)
 s.face([(c[0]+r*hub*.38*math.cos(q*math.pi/6),yf-.17,c[2]+r*hub*.38*math.sin(q*math.pi/6)) for q in range(12)],(30,38,46),bias=.1)
 if mark:
  a=angle+.5*2*math.pi/teeth;w=r*.03;u0=r*.50;u1=r*(1+tip)*.96;nx,nz=-math.sin(a)*w,math.cos(a)*w
  s.face([(c[0]+u0*math.cos(a)+nx,yw-.02,c[2]+u0*math.sin(a)+nz),(c[0]+u1*math.cos(a)+nx,yw-.02,c[2]+u1*math.sin(a)+nz),(c[0]+u1*math.cos(a)-nx,yw-.02,c[2]+u1*math.sin(a)-nz),(c[0]+u0*math.cos(a)-nx,yw-.02,c[2]+u0*math.sin(a)-nz)],(255,247,207),bias=.2)
 return {'tip_radius':r*(1+tip),'root_radius':r*(1-root)}

def spring(s,a,b,coils,radius,wire,color,steps=9,squash=1.0):
 """Helical coil spring from a to b (any direction). squash<1 draws the same coils in a shorter span, as when compressed."""
 a=np.asarray(a,float);b=np.asarray(b,float);d=_unit(b-a);u,v=_perp(d);length=float(np.linalg.norm(b-a))
 pts=[a+d*(length*q/(coils*steps))+radius*(u*math.cos(2*math.pi*q/steps)+v*math.sin(2*math.pi*q/steps)) for q in range(int(coils*steps)+1)]
 for k,(p,q) in enumerate(zip(pts,pts[1:])):
  front=.78+.22*math.sin(2*math.pi*k/steps)
  s.beam(tuple(p),tuple(q),wire,shade(color,front))
 return pts

def hook_link(s,p0,p1,w0,w1,thick,color,y=0.,tip_cut=.35):
 """Flat tapered link (lever, pawl, latch) in the X-Z plane: wide at p0, narrow at p1, with a hooked tip. Faces are chamfered on the front edge."""
 p0=np.asarray(p0,float);p1=np.asarray(p1,float);d=_unit(p1-p0);n=np.array((-d[2],0.,d[0]))
 length=float(np.linalg.norm(p1-p0))
 outline=[p0+n*w0/2,p1+n*w1/2-d*length*tip_cut*.5,p1+n*w1*.15+d*0,p1-n*w1/2,p0-n*w0/2]
 def lift(pt,off):return (pt[0],y+off,pt[2])
 front=[lift(q,-thick/2) for q in outline];back=[lift(q,thick/2) for q in outline]
 s.face(back,shade(color,.6))
 for k in range(len(outline)):
  j=(k+1)%len(outline);s.face([front[k],front[j],back[j],back[k]],shade(color,.55+.4*(.5+.5*math.cos(k*1.3))))
 s.face(front,color)
 inset=[p0+n*w0*.30,p1+n*w1*.2-d*length*tip_cut*.5,p1-n*w1*.3,p0-n*w0*.30]
 s.face([lift(q,-thick/2-.012) for q in inset],shade(color,1.12))

def chamfer_box(s,c,size,color,bevel=.04):
 """Box whose top and front edges are bevelled so the light catches them."""
 x,y,z=c;a,b,h=(size[0]/2,size[1]/2,size[2]/2);e=min(bevel,a*.5,b*.5,h*.5)
 s.box(c,size,color)
 s.face([(x-a+e,y-b-.004,z+h),(x+a-e,y-b-.004,z+h),(x+a,y-b-.004,z+h-e),(x-a,y-b-.004,z+h-e)],shade(color,1.35))
 s.face([(x-a,y-b-.004,z-h+e),(x+a,y-b-.004,z-h+e),(x+a-e,y-b-.004,z-h),(x-a+e,y-b-.004,z-h)],shade(color,.55))
 s.face([(x-a,y-b-.004,z-h+e),(x-a+e,y-b-.004,z-h+e),(x-a+e,y-b-.004,z+h-e),(x-a,y-b-.004,z+h-e)],shade(color,1.15))

def plate(s,c,size,color,tiles=(8,6),bevel=.05):
 """Large backing plate built from small tiles. One huge face sorts by its centre and can paint over parts that sit in front of its far side; tiles cannot."""
 x,y,z=c;w,t,h=size;nx,nz=tiles;fy=y-t/2
 for i in range(nx):
  for j in range(nz):
   x0=x-w/2+w*i/nx;x1=x-w/2+w*(i+1)/nx;z0=z-h/2+h*j/nz;z1=z-h/2+h*(j+1)/nz
   s.face([(x0,fy,z0),(x1,fy,z0),(x1,fy,z1),(x0,fy,z1)],shade(color,1.0+.05*math.cos(i*.9+j*.7)))
 s.face([(x-w/2,fy,z+h/2),(x+w/2,fy,z+h/2),(x+w/2,y+t/2,z+h/2),(x-w/2,y+t/2,z+h/2)],shade(color,1.3),bias=-.2)
 s.face([(x-w/2,fy,z-h/2),(x-w/2,y+t/2,z-h/2),(x-w/2,y+t/2,z+h/2),(x-w/2,fy,z+h/2)],shade(color,.8),bias=-.2)
 s.face([(x+w/2,fy,z-h/2),(x+w/2,y+t/2,z-h/2),(x+w/2,y+t/2,z+h/2),(x+w/2,fy,z+h/2)],shade(color,.7),bias=-.2)

def rivets(s,points,r,color,y=0.):
 for p in points:
  tube(s,(p[0],y,p[1]),(p[0],y-r*.9,p[1]),r,shade(color,1.15),n=10,chamfer=r*.3)

def hex_prism(s,c,r,y0,y1,angle,color):
 c=np.asarray(c,float)
 top=[(c[0]+r*math.cos(angle+k*math.pi/3),y0,c[2]+r*math.sin(angle+k*math.pi/3)) for k in range(6)]
 bot=[(p[0],y1,p[2]) for p in top]
 for k in range(6):s.face([top[k],top[(k+1)%6],bot[(k+1)%6],bot[k]],shade(color,.74+.22*math.cos(angle+k*math.pi/3-1.0)))
 s.face(top,shade(color,1.05));s.face(bot,shade(color,.8))
 return top

def piston_cylinder(s,base,radius,height,head_u,color,glass=(170,220,235,70),rod_r=.07):
 """Vertical cylinder with a glass wall, a piston head at fraction head_u of the stroke (0 bottom, 1 top) and a rod that leaves the top."""
 base=np.asarray(base,float);zc=base[2]+height*(.1+.8*head_u)
 tube(s,(base[0],base[1],base[2]),(base[0],base[1],base[2]+.12),radius*1.05,shade(color,.8),n=24,chamfer=.02)
 tube(s,(base[0],base[1],zc-.10),(base[0],base[1],zc+.10),radius*.96,shade(color,1.05),n=24,chamfer=.02)
 tube(s,(base[0],base[1],zc),(base[0],base[1],base[2]+height+.9),rod_r,(190,198,205),n=10,chamfer=.01)
 n=28
 for k in range(n):
  a=k*2*math.pi/n;b=a+2*math.pi/n
  s.glass([(base[0]+radius*math.cos(a),base[1]+radius*math.sin(a),base[2]+.12),(base[0]+radius*math.cos(b),base[1]+radius*math.sin(b),base[2]+.12),(base[0]+radius*math.cos(b),base[1]+radius*math.sin(b),base[2]+height),(base[0]+radius*math.cos(a),base[1]+radius*math.sin(a),base[2]+height)],glass)
 return {'head_z':zc}

CATALOGUE=['tube','disc','annulus','gear','spring','hook_link','chamfer_box','plate','rivets','hex_prism','piston_cylinder']
