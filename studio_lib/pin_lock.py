"""Pin tumbler lock (side cutaway): a notched key slides into the plug and lifts four spring-loaded pin stacks. When every split between key pin and driver pin sits exactly on the shear line, the plug is free to turn.
Exact: key pin length = shear height - floor - cut depth, so only the matching key puts every split on the line. Teaching model, no door shown."""
import functools,math
import numpy as np
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P,hb
KLEN=4.4
FLOOR=.30;GROUND=(34,47,59);DARK=True
KZ=1.5;SZ=3.1;PX=(0.9,1.75,2.6,3.45);CUT=(.55,.2,.75,.4);KL=[SZ-KZ-c for c in CUT];DRV=1.0;CEIL=5.0;TIPOUT=-.3;TIPIN=4.3;DS=(3.55,2.7,1.85,1.0)

def sm(q):q=min(1.,max(0.,q));return q*q*(3-2*q)
def keyh(d):
 """Key top height above the channel floor at distance d behind the tip."""
 if d<0:return 0.
 h=CUT[0]*0.0
 base=.12*sm(d/.35)
 val=base
 for c,dc in zip(CUT,DS):val=max(val,c) if abs(d-dc)<.14 else val
 # blend ramps between flats
 pts=[(0,0)]+[(x,v) for dc,c in zip(DS[::-1],CUT[::-1]) for x,v in ((dc-.28,None),(dc-.14,c),(dc+.14,c),(dc+.28,None))]
 xs=[0.,.4]+[q for dc in DS[::-1] for q in (dc-.14,dc+.14)]+[6.5]
 hs=[0.,.12]+[c for c in CUT[::-1] for _ in (0,1)]+[.12]
 for k in range(len(xs)-1):
  if xs[k]<=d<=xs[k+1]:
   return hs[k]+(hs[k+1]-hs[k])*sm((d-xs[k])/(xs[k+1]-xs[k])) if xs[k+1]>xs[k] else hs[k]
 return .12
def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 e=[ease(progress(t,b[k])) for k in range(8)]
 ins=.72*e[2]+.28*e[3]-.8*e[5]+.8*e[6]
 return dict(beat=i,cut=e[1]*(1-e[7]),ins=ins)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl);ins=p['ins'];cut=p['cut'];beat=p['beat'];tip=TIPOUT+(TIPIN-TIPOUT)*ins
 if 'body' not in hidden:
  hb.block(s,(2.2,.55,.5),(6.6,1.2,.5),hb.DARK,.07)
  P.plate(s,(2.2,.85,3.4),(5.8,.2,5.4),hb.PLATE,tiles=(8,8))
  hb.block(s,(2.2,.6,(SZ+CEIL+.4)/2+.2),(5.8,.5,CEIL+.4-SZ),hb.sh(hb.DARK,1.1),.06)
  hb.block(s,(2.2,.6,(SZ+KZ-1.0)/2-.0),(5.8,.5,SZ-KZ+1.0),hb.sh(hb.MID,.85),.06)
  hb.block(s,(2.2,.15,SZ),(5.8,.14,.07),hb.BRASS,.02)
  P.rivets(s,[(x,.5) for x in (-.6,.9,2.2,3.5,4.8)],.06,hb.BRASS,y=-.4)
 for i,x in enumerate(PX):
  if 'pins' in hidden:break
  lift=keyh(tip-x);zb=KZ+lift;zt=zb+KL[i]
  hb.block(s,(x,0,(zb+zt)/2),(.46,.46,KL[i]),hb.BRASS,.04)
  hb.block(s,(x,0,zt+DRV/2),(.46,.46,DRV),hb.sh(hb.STEEL,1.0),.04)
  P.spring(s,(x,-.05,zt+DRV),(x,-.05,CEIL),5,.2,.035,hb.sh(hb.STEEL,.8))
 if 'key' not in hidden:
  top=[];xs=[tip-KLEN+KLEN*k/60 for k in range(61)]
  for x in xs:top.append((x,KZ+keyh(tip-x)))
  poly=[(tip,KZ-.62)]+top[::-1]+[(tip-KLEN,KZ-.62)]
  fr=[(x,-.22,z) for x,z in poly];rr=[(x,.22,z) for x,z in poly]
  s.face(rr,hb.sh(hb.STEEL,.6))
  for k in range(len(poly)):
   j=(k+1)%len(poly);s.face([fr[k],fr[j],rr[j],rr[k]],hb.sh(hb.STEEL,.62+.3*(k%3)/2))
  s.face(fr,hb.STEEL)
  P.disc(s,(tip-KLEN,0,KZ-.1),.72,-.26,hb.RED,n=24);P.disc(s,(tip-KLEN,0,KZ-.1),.25,-.3,hb.sh(hb.RED,.6),n=14)
 if beat in (2,3,6):
  hb.arrow(s,(tip-KLEN-.9,-.8,KZ-.1),(tip-KLEN+.3,-.8,KZ-.1),hb.ARROW,.05)
 if beat==5:
  hb.arrow(s,(tip-KLEN+.3,-.8,KZ-.1),(tip-KLEN-.9,-.8,KZ-.1),hb.ARROW,.05)
 if 'cover' not in hidden and cut<.99:
  zc=3.6+7.0*cut;hb.block(s,(2.2,-.4,zc),(4.4,.14,2.6),hb.COVER,.06)
  P.rivets(s,[(.4,zc+1.0),(4.0,zc+1.0),(.4,zc-1.0),(4.0,zc-1.0)],.06,hb.sh(hb.STEEL,.8),y=-.5)
 return p
SHOTS=[((1.1, 0, 3.2), 1.3, 0.3), ((2.2, 0, 3.2), 1.4, 0.3), ((1.2, 0, 3.2), 1.15, -0.45), ((2.2, 0, 3.0), 1.68, 0.8), ((1.2, 0, 3.2), 1.2, 0.2), ((1.2, 0, 3.2), 1.15, -0.7), ((1.2, 0, 3.2), 1.1, 0.5), ((1.1, 0, 3.2), 1.3, 0.3)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
