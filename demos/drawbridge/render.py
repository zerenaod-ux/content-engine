"""Deterministic reusable bascule scene. CPU rendering, no image/model calls.

World units are illustrative. A rigid leaf/counterweight share a fixed pivot.
Preview: python render.py --preview; full: python render.py
"""
import argparse, json, math, subprocess, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
W,H=720,1280
APPROACHES=((-7.2,4.0),(5.8,6.0))
BG=Image.fromarray(np.broadcast_to(np.linspace([245,246,233],[201,225,225],H,dtype=np.uint8)[:,None,:],(H,W,3)).copy())
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(n,bold=False): return ImageFont.truetype(BOLD if bold else FONT,n)
FONTS={n:font(n,b) for n,b in [(17,False),(21,False),(24,True),(32,True),(50,True),(58,True)]}
def ease(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
def ramp(t,a,b): return ease((t-a)/(b-a))
def mix(a,b,p): return a+(b-a)*p
def unit(a): return a/np.linalg.norm(a)

class Scene:
    """A tiny perspective mesh renderer; all assets remain local and reusable."""
    def __init__(self,t,zoom,target,azimuth):
        self.t=t; self.faces=[]; self.lines=[]; self.gear_marks=[]
        self.target=np.array(target,dtype=float)
        self.eye=self.target+np.array([math.sin(azimuth)*16,-math.cos(azimuth)*16,10])/zoom
        self.forward=unit(self.target-self.eye)
        self.right=unit(np.cross(self.forward,[0,0,1])); self.up=np.cross(self.right,self.forward)
    def project(self,points):
        p=np.asarray(points)-self.eye; depth=p@self.forward
        return np.column_stack([W/2+780*(p@self.right)/depth,740-780*(p@self.up)/depth]),depth
    def face(self,points,color):
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
        q,dep=self.project(p)
        self.faces.append((float(dep.mean()),[tuple(x) for x in q],color))
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
    def paint(self,im):
        d=ImageDraw.Draw(im)
        for _,p,c in sorted(self.faces,key=lambda x:-x[0]):d.polygon(p,fill=c)
        for (x,y,z),r,a in self.gear_marks:
            q,_=self.project([(x+r*.38*math.cos(a),y,z+r*.38*math.sin(a)),(x+r*.79*math.cos(a),y,z+r*.79*math.sin(a))])
            d.line([tuple(v) for v in q],fill=(255,247,207),width=5 if r>.4 else 4)
            px,py=q[-1];d.ellipse((px-3,py-3,px+3,py+3),fill=(255,247,207))
    def point(self,p):return tuple(self.project([p])[0][0])

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

def state(t,beats):
    b=next((b for b in beats if b['start']<=t<b['end']),beats[-1]);i=beats.index(b);u=(t-b['start'])/(b['end']-b['start'])
    # sequential actions, all camera moves are eased, never random
    angle=0
    if i==3:angle=math.radians(52)*ease(u)
    elif i==4:angle=math.radians(52+20*ease(u))
    elif i==5:angle=math.radians(72)
    elif i==6:angle=math.radians(72)*(1-ease(u))
    gate=0 if i==0 else (ease(u*1.5) if i==1 else 1)
    if i==7:gate=1-ramp(u,.30,.65)
    cut=ramp(t,beats[2]['start']-.8,beats[2]['start']+1.2)*(1-ramp(t,beats[5]['start']-.8,beats[5]['start']+1.3))
    close=ramp(t,beats[2]['start']-1,beats[2]['start']+1.4)*(1-ramp(t,beats[5]['start']-1,beats[5]['start']+1.2))
    target=[mix(0,-2.2,close),0,mix(1.6,2.25,close)]
    zoom=mix(1.05,1.85,close)
    az=mix(.45,.18,close)+.035*math.sin(t*.08)
    detail=ramp(t,beats[4]['start']-.4,beats[4]['start']+1.2)*(1-ramp(t,beats[4]['end']-1.5,beats[4]['end']+.3))
    zoom=mix(zoom,2.8,detail)
    target=[mix(target[0],-3.1,detail),mix(target[1],-.55,detail),mix(target[2],2.3,detail)]
    shipy=-6.0
    if i==5:shipy=mix(-6,6,ease(u))
    elif i>=6:shipy=6+2*ease((t-beats[5]['end'])/(beats[-1]['end']-beats[5]['end']))
    carx=-6.7
    if i==0:carx=mix(-8.5,-6.7,ease(u))
    elif i==7:carx=mix(-6.7,7,ramp(u,.5,1))
    return dict(angle=angle,gate=gate,cut=cut,target=target,zoom=zoom,az=az,shipy=shipy,carx=carx,beat=i,u=u)

def frame(t,timeline,hidden=()):
    st=state(t,timeline['beats'])
    # bright, quiet studio environment with a warm horizon
    im=BG.copy();d=ImageDraw.Draw(im)
    d.ellipse((-150,300,870,1210),fill=(216,234,230))
    s=Scene(t,st['zoom'],st['target'],st['az'])
    # Water is the background layer. Mean-depth sorting a giant plane amongst
    # solid meshes incorrectly painted it over the distant ship.
    water=Scene(t,st['zoom'],st['target'],st['az'])
    water.face([[-10,-10,-.06],[10,-10,-.06],[10,18,-.06],[-10,18,-.06]],(66,160,175))
    # deterministic water ripples; restrained movement leaves the mechanism readable
    for k in range(60):
        x=math.sin(k*12.3)*9;y=((k*.71+t*.06)%18)-9
        length=.18+.30*(1+math.sin(k*2.7))
        water.face([[x,y,0],[x+length,y,0],[x+length+.08,y+.025,0],[x+.08,y+.025,0]],(104,186,190))
    water.paint(im)
    bridge(s,st['angle'],st['cut'],st['gate'],st['carx'])
    if 'ship' not in hidden:boat(s,st['shipy'])
    # subtle twin wake lines follow the ship only when it moves
    if st['beat']>=5:
        for side in [-1,1]:
            s.face([[1+side*.5,st['shipy']-1.4,.02],[1+side*.9,st['shipy']-3,.02],[1+side*.87,st['shipy']-3,.02],[1+side*.47,st['shipy']-1.4,.02]],(190,223,216))
    s.paint(im)
    # Keep the fixed hook clear during the mechanism close-up.
    header=Image.new('L',(W,H),0)
    hd=ImageDraw.Draw(header)
    for yy in range(330):hd.line((0,yy,W,yy),fill=255 if yy<275 else int(255*(330-yy)/55))
    im.paste(BG,(0,0),header);d=ImageDraw.Draw(im)
    d.text((48,68),'HOW IT TICKS',font=FONTS[21],fill=(31,77,89))
    d.line((48,108,112,108),fill=(221,102,57),width=4)
    # one fixed hook; no running captions
    d.text((46,143),'A road that',font=FONTS[58],fill=(30,65,78))
    d.text((46,210),'gets out of the way.',font=FONTS[50],fill=(30,65,78))
    # restrained helper labels only during the close-up
    if st['cut']>.95:
        items=[('FIXED PIVOT',(-2.8,-1.22,2.5),(.53,.34))]
        if st['beat'] in [3,4]:
            weight=leaf_transform(st['angle'])(np.array([[-1.6,-.85,-.8]]))[0]
            items.append(('COUNTERWEIGHT',weight,(.08,.81)))
        for label,point,xy in items:
            x,y=s.point(point);lx,ly=W*xy[0],H*xy[1]
            d.line([(x,y),(lx+10,ly+32)],fill=(45,88,98),width=2);d.ellipse((x-4,y-4,x+4,y+4),fill=(238,170,75))
            box=d.textbbox((lx,ly),label,font=FONTS[17]);d.rectangle((box[0]-8,box[1]-6,box[2]+8,box[3]+6),fill=(241,245,233));d.text((lx,ly),label,font=FONTS[17],fill=(33,75,86))
    # minimal progress rail, with no instructional text over the object
    d.rounded_rectangle((48,1195,672,1198),radius=1,fill=(172,200,200))
    d.rounded_rectangle((48,1195,48+624*min(1,t/timeline['duration']),1198),radius=1,fill=(219,111,65))
    d.text((48,1220),'BASCULE / MECHANISM STUDY',font=FONTS[17],fill=(65,108,116))
    return im

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--fps',type=int,default=30);args=ap.parse_args()
    OUT.mkdir(exist_ok=True);tl=json.loads((OUT/'timeline.json').read_text());t0=time.monotonic()
    if args.preview:
        times=[b['start']+(b['end']-b['start'])*.65 for b in tl['beats']]
        sheet=Image.new('RGB',(W*4,H*2))
        for i,t in enumerate(times):
            fr=frame(t,tl);fr.save(OUT/f'preview-{i}.jpg');sheet.paste(fr,((i%4)*W,(i//4)*H))
        sheet.resize((1440,1280)).save(OUT/'contact.jpg');print('preview seconds',time.monotonic()-t0);return
    total=math.ceil(tl['duration']*args.fps)
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(args.fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(OUT/'silent.mp4')],stdin=subprocess.PIPE)
    for k in range(total):
        proc.stdin.write(frame(k/args.fps,tl).tobytes())
        if k%150==0:print(f'frame {k}/{total}',flush=True)
    proc.stdin.close()
    if proc.wait():raise RuntimeError('encoder failed')
    report={'render_seconds':time.monotonic()-t0,'frames':total,'fps':args.fps,'width':W,'height':H,'duration':tl['duration'],'model_calls':0,'asset_generation_calls':0,'renderer':'CPU perspective meshes, authored prototype'}
    (OUT/'render-metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
