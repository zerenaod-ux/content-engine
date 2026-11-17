"""Procedural photovoltaic illustration; fixed connections, no AI geometry."""
import math
import numpy as np
from studio_lib.mesh import ease,ramp
def pose(t,tl):
    i=min(7,next((i for i,b in enumerate(tl['beats']) if t<b['end']),7));b=tl['beats'][i];u=max(0,min(1,(t-b['start'])/(b['end']-b['start'])))
    cut=ramp(t,tl['beats'][2]['start']-.7,tl['beats'][2]['start']+1)*(1-ramp(t,tl['beats'][7]['start'],tl['beats'][7]['start']+1.2))
    return {'beat':i,'u':u,'cut':cut,'powered':i>=5,'light':i>=1,'current':i>=5}
def dot(s,p,r,color):s.cylinder(p,r,r*.7,color,n=12)
def circuit_point(q):
    # From top contact to the lamp and back to bottom contact: a closed path.
    points=[(-2.2,-1.35,2.5),(-3.25,-1.35,2.5),(-3.25,-1.35,.7),(3.15,-1.35,.7),(3.15,-1.35,1.7),(3.15,-1.35,2.0),(1.9,-1.35,2.0),(1.9,-1.35,1.7)]
    k=int((q%1)*(len(points)-1));u=(q%1)*(len(points)-1)-k
    return np.array(points[k])*(1-u)+np.array(points[k+1])*u
def draw(s,t,tl,hidden=()):
    p=pose(t,tl);cut=p['cut']
    thickness=.18+.82*cut
    def height(z):return 2.3+(z-2.3)*thickness
    def panelbox(at,size,color):s.box((at[0],at[1],height(at[2])),(size[0],size[1],size[2]*thickness),color)
    # Panel stand and physical frame remain the same throughout the reveal.
    for x in [-2.15,1.75]:
        s.box((x,.35,.45),(.18,.18,.9),(100,131,141));s.beam((x,.35,.1),(x,.35,2.15),.065,(104,139,152))
    for x in [-2.4,2.0]:panelbox((x,.2,2.1),(.15,2.1,1.1),(176,192,196))
    for y in [-.85,1.25]:panelbox((-.2,y,2.1),(4.5,.12,1.1),(190,204,204))
    # Enlarged layers are explicitly diagrammatic and mechanically static.
    panelbox((-.2,.2,1.78),(4.2,1.95,.23),(218,156,120))
    panelbox((-.2,.2,2.05),(4.2,1.95,.30),(70,118,157))
    panelbox((-.2,.2,2.25),(4.2,1.95,.09),(229,200,120))
    top=2.37+cut*1.25
    if 'panel' not in hidden:
        s.box((-.2,.2,top),(4.25,1.98,.09),(37,82,125))
        for x in np.linspace(-2.05,1.65,6):
            for y in np.linspace(-.65,1.05,4):
                s.box((x,y,top+.055),(.56,.36,.025),(45,95,151))
                s.box((x,y,top+.072),(.025,.34,.012),(186,206,212))
        for x in np.linspace(-2.1,1.7,12):s.box((x,.2,top+.078),(.012,1.85,.01),(169,195,205))
    # Contacts and an actual connected two-wire DC circuit.
    panelbox((-2.2,.2,2.5),(.10,1.85,.13),(219,181,91));panelbox((1.9,.2,1.7),(.10,1.85,.13),(219,181,91))
    s.beam((-2.2,-.75,height(2.5)),(-2.2,-.75,2.5),.04,(219,181,91)) if abs(height(2.5)-2.5)>.001 else None
    s.beam((1.9,-.75,height(1.7)),(1.9,-.75,1.7),.04,(219,181,91)) if abs(height(1.7)-1.7)>.001 else None
    segments=[((-2.2,-.75,2.5),(-2.2,-1.35,2.5)),((-2.2,-1.35,2.5),(-3.25,-1.35,2.5)),((-3.25,-1.35,2.5),(-3.25,-1.35,1.95)),((-3.25,-1.35,1.45),(-3.25,-1.35,.7)),((-3.25,-1.35,.7),(3.15,-1.35,.7)),((3.15,-1.35,.7),(3.15,-1.35,1.7))]
    for a,b in segments:s.beam(a,b,.045,(61,78,89))
    # An explicit switch explains why the illuminated cell powers the lamp
    # only after the circuit beat; no unexplained delayed response to light.
    endpoint=(-3.25,-1.35,1.95) if p['current'] else (-2.88,-1.35,1.83)
    s.beam((-3.25,-1.35,1.45),endpoint,.045,(229,147,75))
    for zz in [1.45,1.95]:dot(s,(-3.25,-1.35,zz),.07,(215,183,116))
    for a,b in zip([(1.9,-.75,1.7),(1.9,-1.35,1.7),(1.9,-1.35,2.0),(3.15,-1.35,2.0)],[(1.9,-1.35,1.7),(1.9,-1.35,2.0),(3.15,-1.35,2.0),(3.15,-1.35,1.7)]):s.beam(a,b,.045,(188,91,61))
    # DC lamp, with a socket, glass outline and filament.
    s.box((3.15,-1.35,1.25),(.65,.60,.22),(93,115,125));s.cylinder((3.15,-1.35,1.65),.26,.38,(191,186,155))
    lamp=(255,222,110) if p['powered'] else (192,214,209)
    s.cylinder((3.15,-1.35,2.15),.42,.40,lamp,n=24)
    s.beam((2.99,-1.58,1.95),(3.15,-1.58,2.24),.024,(244,163,61));s.beam((3.15,-1.58,2.24),(3.31,-1.58,1.95),.024,(244,163,61))
    if p['light'] and 'light' not in hidden:
        for k in range(7):
            phase=(t*.7+k*.15)%1;x=-1.9+k*.55;z=2.14+3.8*(1-phase);y=.0
            s.beam((x-.15,y,z+.28),(x+.15,y,z-.28),.032,(250,195,69))
    if p['beat']>=2 and p['beat']<7 and 'carriers' not in hidden:
        for k in range(7):
            x=-1.7+k*.48;phase=(t*.5+k*.13)%1
            dot(s,(x,-.94,2.12+.33*phase),.065,(91,221,222))
            dot(s,(x,-.94,1.95-.18*phase),.065,(238,117,88))
    if p['current'] and 'current' not in hidden:
        for k in range(13):dot(s,circuit_point(t*.075+k/13),.07,(80,216,222))
    return p
