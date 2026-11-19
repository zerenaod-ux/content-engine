"""Single-acting piston pump cutaway with coupled volume and check valves."""
import math
import numpy as np
from studio_lib.mesh import ease,ramp
from studio_lib.narration_timing import progress,span_progress,event_started
def cylinder_x(s,x,y,z,r,length,color):
    rings=[np.array([[x+dx,y+r*math.cos(a),z+r*math.sin(a)] for a in np.linspace(0,2*math.pi,20,endpoint=False)]) for dx in [-length/2,length/2]]
    s.face(rings[0],color);s.face(rings[1],tuple(min(255,int(c*1.1)) for c in color))
    for i in range(20):s.face([rings[0][i],rings[0][(i+1)%20],rings[1][(i+1)%20],rings[1][i]],tuple(int(c*(.8+.15*math.sin(i/20*2*math.pi))) for c in color))
def phase(t,tl):
    beats=tl['beats'];i=min(7,next((i for i,b in enumerate(beats) if t<b['end']),7));b=beats[i];u=max(0,min(1,(t-b['start'])/(b['end']-b['start'])))
    if i<2:total=0.0
    elif i in (2,3):total=.5*ease(span_progress(t,beats,2,3))
    elif i in (4,5):total=.5+.5*ease(span_progress(t,beats,4,5))
    else:total=1+(t-beats[6]['start'])/4
    q=total%1;cycles=math.floor(total)
    # q 0..0.5: withdrawal; q .5..1: compression.
    withdrawal=q<.5
    fraction=(1-math.cos(2*math.pi*q))/2
    pistonx=.1-2.0*fraction
    intake_cycles=cycles+(fraction if withdrawal else 1)
    delivery_cycles=cycles+(0 if withdrawal else 1-fraction)
    # A normalized illustrative volume balance, not calibrated physical units.
    source_level=1.3-.23*intake_cycles;receiver_level=.25+.23*delivery_cycles
    return {'beat':i,'q':q,'piston_x':pistonx,'intake':withdrawal and i>=2 and event_started(t,beats[2]),'delivery':not withdrawal and i>=2 and event_started(t,beats[4]),'chamber_length':1.6-pistonx,'source_level':source_level,'receiver_level':receiver_level,'chamber_fill':intake_cycles-delivery_cycles}
def draw(s,t,tl,hidden=()):
    p=phase(t,tl);px=p['piston_x'];cut=ease(progress(t,tl['beats'][1]))*(1-ease(progress(t,tl['beats'][7]))) if tl.get('motion_policy') else ramp(t,tl['beats'][1]['start']-.5,tl['beats'][1]['start']+1)
    # Source and receiver reservoirs, open at the top.
    for x,waterlevel in [(-4.7,p['source_level']),(4.1,p['receiver_level'])]:
        s.box((x,0,.1),(1.45,1.5,.2),(181,199,201))
        s.box((x,.72,.9),(1.45,.10,1.6),(172,193,197))
        # Open-front tank cutaway makes the changing level visible.
        for zz in [.2,1.7]:s.beam((x-.7,-.72,zz),(x+.7,-.72,zz),.035,(161,184,189))
        for xx in [x-.7,x+.7]:s.beam((xx,-.72,.2),(xx,-.72,1.7),.035,(161,184,189))
        for xx in [x-.68,x+.68]:s.box((xx,0,.9),(.10,1.45,1.6),(185,204,205))
        s.box((x,0,waterlevel/2+.2),(1.25,1.25,waterlevel),(64,157,179))
    # Cylinder shows back, floor and end head. Front cover lifts out of sight.
    # Curved cylinder shell, split into a back half and a lifted front cutaway.
    for near in [False,True]:
        angles=np.linspace(math.pi/2,3*math.pi/2,17) if near else np.linspace(-math.pi/2,math.pi/2,17)
        offset=cut*2.3 if near else 0
        for a,b in zip(angles,angles[1:]):
            s.face([[-2.75,.82*math.cos(a),2.35+.82*math.sin(a)+offset],[1.55,.82*math.cos(a),2.35+.82*math.sin(a)+offset],[1.55,.82*math.cos(b),2.35+.82*math.sin(b)+offset],[-2.75,.82*math.cos(b),2.35+.82*math.sin(b)+offset]],(109,146,158) if near else (141,171,181))
    s.box((-.6,0,1.48),(4.3,1.7,.16),(136,160,166))
    s.box((1.6,0,2.35),(.20,.95,1.6),(160,179,182))
    for xx in [-2.6,1.55]:
        for zz in [1.82,2.9]:s.cylinder((xx,-.62,zz),.08,.05,(231,203,139),n=12)
    # Water volume is bounded by the piston face and fixed end head.
    if 'water' not in hidden:cylinder_x(s,(px+.13+1.48)/2,0,2.35,.68,max(.05,1.48-px-.13),(74,166,183))
    if 'piston' not in hidden:
        cylinder_x(s,px,0,2.35,.72,.25,(221,150,89))
        for xx in [px-.1,px+.1]:cylinder_x(s,xx,0,2.35,.74,.045,(65,87,96))
        s.beam((-3.25,0,2.35),(px-.15,0,2.35),.11,(189,202,198))
        s.box((-3.4,0,2.35),(.55,.65,.55),(79,116,133))
    # Connected inlet below the head; outlet above it.
    inlet=[(-4.7,0,.45),(-4.7,0,1.1),(1.0,0,1.1),(1.0,0,1.65)]
    outlet=[(1.0,0,3.1),(1.0,0,3.7),(4.1,0,3.7),(4.1,0,1.5)]
    for pts in (inlet,outlet):
        for a,b in zip(pts,pts[1:]):s.beam(a,b,.13,(105,139,151))
    # Flap valves sit inside the flow passages, front cutaway enlarged for clarity.
    for z,opened in [(1.60,p['intake']),(3.10,p['delivery'])]:
        s.box((1.0,-.35,z),(.65,.20,.11),(219,193,129))
        angle=math.radians(50 if opened else 0)
        a=(.70,-.49,z+.04);b=(.70+.60*math.cos(angle),-.49,z+.04+.60*math.sin(angle))
        s.beam(a,b,.04,(240,157,79))
        s.cylinder(a,.06,.12,(75,100,112),n=12)
    def droplets(points,count):
        for k in range(count):
            q=(t*.36+k/count)%1;idx=min(len(points)-2,int(q*(len(points)-1)));u=q*(len(points)-1)-idx
            a=np.array(points[idx])*(1-u)+np.array(points[idx+1])*u;a[1]=-.21
            s.cylinder(a,.09,.09,(71,217,227),n=12)
    if p['intake'] and 'flow' not in hidden:droplets(inlet,9)
    if p['delivery'] and 'flow' not in hidden:droplets(outlet,8)
    return p

# CLOSE_SHOTS (owner 2026-11-16): camera pushes in on the part each line talks about.
SHOTS=[((-.3,0,2.1),.85,.34),      # pump: whole connected system before the cutaway
       ((-.6,0,2.35),1.7,.40),      # cutaway: cylinder opens
       ((-.9,0,2.35),2.4,.45),      # suction: piston pulls back, chamber fills
       ((.3,-.25,1.9),2.7,.35),     # inlet: inlet flap valve opens
       ((-.4,0,2.35),2.4,.30),      # compression: piston pushes in
       ((.3,-.25,2.8),2.7,.35),     # outlet: outlet flap valve opens
       ((1.6,0,2.2),1.4,.30),       # repeat: water reaching the receiving tank
       ((-.3,0,2.1),.85,.30)]       # payoff: whole system
def shot(i):return SHOTS[min(i,7)]
