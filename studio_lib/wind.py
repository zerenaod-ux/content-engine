"""Direct-drive wind turbine: coupled rotor, shaft and magnet illustration."""
import math
import numpy as np
from studio_lib.mesh import ramp

def pose(t,tl):
    i=min(7,next((i for i,b in enumerate(tl['beats']) if t<b['end']),7))
    cut=ramp(t,tl['beats'][3]['start']-.8,tl['beats'][3]['start']+1.2)*(1-ramp(t,tl['beats'][7]['start'],tl['beats'][7]['start']+1.2))
    return dict(beat=i,angle=t*.85,shaft_angle=t*.85,magnet_angle=t*.85,cut=cut,closed=i>=6)

def wire_point(q):
    pts=np.array([(1.35,-.35,5.1),(1.35,-.35,.55),(3.4,-.35,.55),(3.4,-.35,1.55),(4.3,-.35,1.55),(4.3,-.35,.25),(.95,-.35,.25),(.95,-.35,5.1)])
    z=(q%1)*(len(pts)-1);i=int(z);return pts[i]*(1-z+i)+pts[i+1]*(z-i)

def draw(s,t,tl,hidden=()):
    p=pose(t,tl);a=p['angle'];cut=p['cut'];cx=-.65;cz=5.1
    s.box((cx,.5,.1),(1.5,1.7,.2),(152,170,165))
    s.beam((cx,.5,.15),(cx,.5,4.85),.22,(200,216,216))
    s.box((cx,.5,4.95),(1.9,1.9,.25),(161,181,188))
    if 'shell' not in hidden:
        s.box((cx,.5,5.45+cut*1.8),(2.1,2.0,.55),(211,226,225))
    # Shaft runs directly into the generator, without gears.
    s.cylinder((cx,-.20,cz),.13,2.5,(100,124,137),angle=a)
    s.cylinder((cx,-1.5,cz),.32,.40,(215,229,229))
    if 'blades' not in hidden:
        for k in range(3):
            ang=a+k*2*math.pi/3
            def pt(r,w,y=-1.55):return (cx+r*math.sin(ang)+w*math.cos(ang),y,cz+r*math.cos(ang)-w*math.sin(ang))
            s.face([pt(.24,-.10),pt(.24,.10),pt(1.05,.26),pt(2.65,.08),pt(2.8,-.035),pt(.9,-.14)],(231,240,233))
            s.face([pt(2.3,-.05,-1.57),pt(2.3,.10,-1.57),pt(2.65,.08,-1.57),pt(2.8,-.035,-1.57)],(228,132,71))
    # Stationary copper coils surround a rotating magnet disk in the cutaway.
    if cut>.01:
        for k in range(12):
            ang=k*math.pi/6
            s.cylinder((cx+.83*math.sin(ang),.5,cz+.83*math.cos(ang)),.14,.45,(199,127,70),n=10)
        if 'magnets' not in hidden:
            s.cylinder((cx,.16,cz),.55,.22,(82,107,121),angle=a)
            for k in range(8):
                ang=a+k*math.pi/4
                s.cylinder((cx+.48*math.sin(ang),-.04,cz+.48*math.cos(ang)),.105,.16,(224,110,79) if k%2 else (75,164,194),n=8)
            s.beam((cx,-.15,cz),(cx+.46*math.sin(a),-.15,cz+.46*math.cos(a)),.035,(255,232,149))
    if 'wind' not in hidden:
        for k in range(7):
            y=-5.0+((t*.9+k*.47)%3.2);x=cx-1.7+(k%4)*1.05;z=3.7+(k%3)*1.05
            s.beam((x,y-.45,z),(x,y,z),.025,(103,183,188))
    # Illustrative two-wire output to a switch and load; no grid connection.
    pts=[(cx+.83,.5,cz),(1.35,.5,cz),(1.35,-.35,cz),(1.35,-.35,.55),(3.4,-.35,.55),(3.4,-.35,1.55)]
    for b,c in zip(pts,pts[1:]):s.beam(b,c,.035,(78,104,113))
    pts=[(cx+.6,.7,cz),(.95,.7,cz),(.95,-.35,cz),(.95,-.35,.25),(4.3,-.35,.25),(4.3,-.35,1.55),(3.85,-.35,1.55)]
    for b,c in zip(pts,pts[1:]):s.beam(b,c,.035,(192,112,73))
    s.beam((3.4,-.35,1.55),(3.85,-.35,1.55) if p['closed'] else (3.7,-.35,1.85),.035,(232,164,81))
    s.box((4.3,-.35,.8),(.6,.6,.25),(104,127,133))
    s.cylinder((4.3,-.35,1.2),.3,.4,(255,218,109) if p['closed'] else (174,199,196),n=16)
    if p['closed'] and 'current' not in hidden:
        for k in range(15):s.cylinder(wire_point(t*.09+k/15),.065,.07,(69,219,219),n=8)
    return p
