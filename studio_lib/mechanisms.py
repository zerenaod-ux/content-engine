"""Tested procedural components, not per-video generated geometry or narration."""
import math
import numpy as np
from studio_lib.mesh import ramp
APPROACHES=((-7.2,4.0),(5.8,6.0))
def leaf_transform(angle):
    c,s=math.cos(angle),math.sin(angle)
    def tx(p):
        p=np.asarray(p);x=p[:,0];z=p[:,2]
        return np.column_stack([-2.8+x*c-z*s,p[:,1],2.5+x*s+z*c])
    return tx

def bridge(scene,angle,cut,gate,carx):
    s=scene; tx=leaf_transform(angle)
    # masonry quays and the two fixed approaches
    for x,length in APPROACHES:
        s.box((x,0,.05),(6.4,5.5,.35),(196,207,204))
        for y in [-1.05,1.05]:
            # expose the near chamber wall, not just its thin decorative shell
            s.box((x,y,1.15),(length,.36,2.2),(182,195,198))
        # Short road tiles prevent a long painter-sorted face covering the car.
        for xx in np.arange(x-length/2,x+length/2,.4):
            width=min(.4,x+length/2-xx)
            s.box((xx+width/2,0,2.47),(width,2.3,.24),(87,106,113))
        for xx in np.arange(x-length/2+.2,x+length/2,.58):
            s.box((xx,0,2.53),(.29,.045,.012),(238,225,159))
        for y in [-1.05,1.05]:
            for xx in np.arange(x-length/2,x+length/2,.6):s.box((xx,y,2.8),(.04,.04,.55),(218,229,227))
            s.box((x,y,3.08),(length,.045,.045),(231,235,223))
    # open chamber, with removable front wall for the reveal
    s.box((-3.7,.90,.85),(2.25,.28,1.7),(165,186,190))
    s.box((-3.7,0,.12),(2.25,2.0,.20),(126,150,157))
    if cut<.6:s.box((-3.7,-.96,1.15),(2.25,.24,2.3),(174,193,197))
    for y in [-.78,.78]:
        s.box((-2.8,y,1.72),(.45,.32,1.4),(124,146,154))
    # one rigid rotating assembly: roadway, underdeck girders, short heel, weight
    for xx in np.arange(-2.4,5.6,.4):s.box((xx+.2,0,0),(.4,2.0,.18),(67,89,99),tx)
    for y in [-.95,.95]:
        s.box((1.6,y,-.27),(8.0,.16,.50),(220,102,57),tx)
        for x in np.arange(-2.3,5.5,.48):
            s.box((x,y,-.27),(.065,.19,.48),(244,149,85),tx)
            s.box((x,y,.35),(.035,.035,.62),(225,225,204),tx)
        s.box((1.6,y,.66),(8.0,.045,.045),(238,231,211),tx)
    for x in np.arange(-2.3,5.6,.55):
        s.box((x,0,.10),(.29,.055,.015),(248,220,136),tx)
        s.box((x,0,-.38),(.08,1.85,.10),(168,73,43),tx)
    s.box((-1.6,0,-.5),(1.10,1.65,1.0),(210,190,141),tx)
    for x in [-1.95,-1.6,-1.25]:s.box((x,0,-.5),(.025,1.69,1.02),(151,137,107),tx)
    s.cylinder((-2.8,0,2.5),.18,2.45,(231,191,105))
    # seating receiver and a sliding span-lock pin at the far end
    s.box((2.95,-.82,2.28),(.42,.28,.24),(51,73,84))
    locked=1-ramp(angle,0,.06)
    s.box((3.0-.20*locked,-.82,2.31),(.5,.085,.085),(231,187,93))
    # operating gear is rigidly attached to the pivot; smaller motor pinion meshes
    if cut>.3:
        s.gear((-2.8,-1.16,2.5),.70,28,angle,(232,165,76))
        # 28:12 opposing rotation; centers separated by sum of pitch radii
        s.gear((-3.8,-1.16,2.5),.30,12,-angle*28/12+math.pi/12,(113,150,168))
        s.box((-3.8,-.65,2.5),(.48,.8,.45),(55,119,140))
        for yy in [-.9,-.7,-.5]:s.box((-3.8,yy,2.5),(.52,.035,.49),(91,156,172))
    # warning lamps and road barrier: drops before the bridge moves
    for x in [-5.8,5.2]:
        s.box((x,-1.25,2.92),(.09,.09,.90),(54,73,85))
        s.box((x,-1.25,3.25),(.28,.12,.45),(42,60,69))
        for zz in [3.15,3.35]:s.cylinder((x,-1.33,zz),.055,.035,(246,74 if gate<.8 else 105,55))
        length=1.9; a=(1-gate)*math.pi/2
        a0=(x,-.95,2.8); a1=(x,-.95+length*math.cos(a),2.8+length*math.sin(a))
        s.beam(a0,a1,.055,(236,233,215))
        for k in range(5):
            p=np.array(a0)+(np.array(a1)-a0)*(k+.15)/5;q=np.array(a0)+(np.array(a1)-a0)*(k+.6)/5
            s.beam(p,q,.060,(232,84,60))
    car(s,carx,-.40,2.58,(234,187,74))

def car(s,x,y,z,color):
    s.box((x,y,z+.16),(.8,.38,.24),color)
    s.box((x-.04,y,z+.34),(.42,.34,.18),(46,83,102))
    for xx in [x-.25,x+.25]:
        for yy in [y-.2,y+.2]:s.cylinder((xx,yy,z+.07),.11,.075,(39,55,64),n=12)

def boat(s,y):
    x=1.0
    # bow + tapered hull, rather than a generic box
    lower=np.array([[x-.55,y-1.6,.12],[x+.55,y-1.6,.12],[x+.65,y+.8,.12],[x,y+1.8,.12],[x-.65,y+.8,.12]])
    upper=lower.copy();upper[:,2]=.70;upper[:,0]=x+(upper[:,0]-x)*1.15
    s.face(upper,(241,237,209))
    for i in range(5):s.face([lower[i],lower[(i+1)%5],upper[(i+1)%5],upper[i]],(32,89,115) if i%2 else (44,111,138))
    s.box((x,y-.60,.90),(1.0,1.15,.42),(239,231,202))
    s.box((x,y-.6,1.18),(.85,.9,.23),(86,145,158))
    s.box((x,y-.6,1.34),(1.06,1.13,.12),(242,238,211))
    s.beam((x,y+.35,.75),(x,y+.35,4.1),.04,(227,227,210))
    s.beam((x-.55,y+.35,3.2),(x+.55,y+.35,3.2),.025,(231,227,208))
    for yy in [y-1.35,y-.95,y-.55,y-.15,y+.25,y+.65]:
        for xx in [x-.65,x+.65]:s.beam((xx,yy,.65),(xx,yy,.95),.014,(226,230,220))
    for yy in [y-1.3,y-.1]:s.cylinder((x-.7,yy,.57),.13,.08,(43,56,63),n=12)
