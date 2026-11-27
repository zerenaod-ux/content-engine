"""Shared helpers for hand-built machines (dark cinematic set). Everything is drawn in the X-Z plane at depth y (smaller y = nearer the camera).
Colours follow the first two hit videos: cool steel, dark housings, warm brass and orange accents, a red grip, pale blue input arrows."""
import math
import numpy as np
from studio_lib import parts_rich as P
STEEL=(186,198,206);DARK=(66,79,91);MID=(112,126,136);BRASS=(222,176,84);RED=(202,72,50);WARM=(236,152,72);PLATE=(46,60,74);ARROW=(120,205,230);COVER=(94,110,122)
def sh(c,k):return P.shade(c,k)
def _v(q):
 q=np.asarray(q,float)
 return np.array((q[0],0.,q[1])) if len(q)==2 else q
def pin(s,x,z,y,r,color=BRASS,length=.34):
 """Pivot pin along y with a bright head towards the viewer."""
 P.tube(s,(x,y-length/2,z),(x,y+length/2,z),r,color,n=14,chamfer=r*.25)
def bar(s,p0,p1,w,thick,y,color=STEEL,eyes=True):
 """Flat steel link between two points in the X-Z plane: lit front face, shaded edges, bright edge strip and a pivot eye at each end."""
 p0=_v(p0);p1=_v(p1);d=p1-p0;L=float(np.hypot(d[0],d[2]))
 if L<1e-6:return
 u=np.array((d[0]/L,0,d[2]/L));n=np.array((-u[2],0,u[0]))
 a=p0-u*w/2;b=p1+u*w/2
 c=[a+n*w/2,b+n*w/2,b-n*w/2,a-n*w/2]
 f=[(q[0],y-thick/2,q[2]) for q in c];r=[(q[0],y+thick/2,q[2]) for q in c]
 s.face(r,sh(color,.55))
 for k in range(4):
  j=(k+1)%4;s.face([f[k],f[j],r[j],r[k]],sh(color,.5+.5*(.5+.5*math.cos(1.6*k+1.2+math.atan2(u[2],u[0])))))
 s.face(f,color)
 inset=[p0+u*w*.1+n*w*.28,p1-u*w*.1+n*w*.28,p1-u*w*.1-n*w*.12,p0+u*w*.1-n*w*.12]
 s.face([(q[0],y-thick/2-.01,q[2]) for q in inset],sh(color,1.14))
 if eyes:
  for q in (p0,p1):
   P.disc(s,(q[0],0,q[2]),w*.36,y-thick/2-.02,sh(color,.62),n=18)
def block(s,c,size,color=STEEL,bevel=.05):P.chamfer_box(s,c,size,color,bevel=bevel)
def thread(s,x0,x1,z,y,r,phase,pitch=.28,color=STEEL,core=None):
 """Threaded shaft along x. Ridges slide along the shaft as phase grows, so turning is visible."""
 P.tube(s,(x0,y,z),(x1,y,z),r*.78,core or sh(color,.7),n=16)
 k0=int(math.floor((x0-phase)/pitch))-1
 xs=[phase+k*pitch for k in range(k0,k0+int((x1-x0)/pitch)+3)]
 for x in xs:
  if x0+.02<x<x1-.02:P.tube(s,(x-.045,y,z),(x+.045,y,z),r,sh(color,1.05),n=16,chamfer=.02)
def arrow(s,base,head,color=ARROW,w=.04):
 base=np.asarray(base,float);head=np.asarray(head,float);d=head-base;L=np.linalg.norm(d)
 if L<1e-6:return
 u=d/L;n=np.array((-u[2],0,u[0]))
 s.beam(tuple(base),tuple(head),w,color)
 for o in (-.28,.28):s.beam(tuple(head),tuple(head-u*.34+n*o),w*.9,color)
def hexhead(s,x,z,y,r,angle,color=BRASS,depth=.2):P.hex_prism(s,(x,0,z),r,y,y+depth,angle,color)
def floor_slab(s,c,size,color=PLATE):P.plate(s,c,size,color,tiles=(6,3))
def rack(s,x0,x1,zp,pitch,phase,y,thick,color=STEEL,body=.55,hgt_up=.114,hgt_dn=.133):
 """Toothed bar along x. zp = pitch line; teeth centres at phase + (j+.5)*pitch. Tip above the pitch line, root below it."""
 z_root=zp-hgt_dn;z_tip=zp+hgt_up
 s.box(((x0+x1)/2,y,z_root-body/2),(x1-x0,thick,body),sh(color,.8))
 s.face([(x0,y-thick/2-.01,z_root),(x1,y-thick/2-.01,z_root),(x1,y-thick/2-.01,z_root-body),(x0,y-thick/2-.01,z_root-body)],sh(color,1.0))
 j0=int(math.floor((x0-phase)/pitch));j1=int(math.ceil((x1-phase)/pitch))
 for j in range(j0,j1+1):
  c=phase+(j+.5)*pitch;w0=pitch*.46;w1=pitch*.22
  xa,xb=c-w0,c+w0
  if xa<x0 or xb>x1:continue
  top=[(c-w1,z_tip),(c+w1,z_tip)];fy=y-thick/2;by=y+thick/2
  front=[(xa,fy,z_root),(xb,fy,z_root),(top[1][0],fy,z_tip),(top[0][0],fy,z_tip)]
  back=[(q[0],by,q[2]) for q in front]
  s.face(back,sh(color,.6));s.face(front,sh(color,1.02+.08*math.cos(j*.9)))
  s.face([(xa,fy,z_root),(top[0][0],fy,z_tip),(top[0][0],by,z_tip),(xa,by,z_root)],sh(color,.78))
  s.face([(xb,fy,z_root),(top[1][0],fy,z_tip),(top[1][0],by,z_tip),(xb,by,z_root)],sh(color,.68))
  s.face([(top[0][0],fy,z_tip),(top[1][0],fy,z_tip),(top[1][0],by,z_tip),(top[0][0],by,z_tip)],sh(color,1.3))
def wheel_spokes(s,c,r_out,r_in,y,angle,spokes,color,thick=.16,spoke_w=.12):
 """Rim (annulus tube ring) with spokes to a hub; turns with angle."""
 cx,cz=c
 n=36
 for k in range(n):
  a=angle+k*2*math.pi/n;b=a+2*math.pi/n
  P.tube(s,(cx+(r_out-.05)*math.cos(a),y,cz+(r_out-.05)*math.sin(a)),(cx+(r_out-.05)*math.cos(b),y,cz+(r_out-.05)*math.sin(b)),.075,sh(color,.8+.3*math.cos(a-1.0)),n=8)
 for k in range(spokes):
  a=angle+k*2*math.pi/spokes
  bar(s,(cx+r_in*math.cos(a),cz+r_in*math.sin(a)),(cx+(r_out-.1)*math.cos(a),cz+(r_out-.1)*math.sin(a)),spoke_w,thick,y,color,eyes=False)
 P.tube(s,(cx,y-.12,cz),(cx,y+.12,cz),r_in*.95,sh(color,1.1),n=18,chamfer=.04)
