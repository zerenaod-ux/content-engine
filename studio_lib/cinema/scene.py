"""Reusable Blender component renderer. Reads generated measured timeline only."""
import bpy,json,math,sys,time
from pathlib import Path
from mathutils import Vector
from bpy.app.handlers import persistent
ROOT=Path(sys.argv[sys.argv.index('--')+1]);TL=json.loads((ROOT/'timeline.json').read_text())
PLAN=json.loads((ROOT/'plan.json').read_text());HAND=PLAN['mechanism']=='hand_generator'
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from studio_lib.cinema.presentation import camera_pose,rotor_angle
FPS=24
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def ramp(t,a,b):return smooth((t-a)/(b-a))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=540;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.render.fps=FPS;scene.render.image_settings.file_format='PNG'
sh=scene.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.5;sh.color_type='MATERIAL'
sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True
sh.background_type='WORLD';scene.world.color=(.33,.46,.52)
scene.view_settings.view_transform='Standard';scene.view_settings.exposure=.3
if hasattr(scene.display,'render_aa'):scene.display.render_aa='8'
M={}
for name,color in {'ceramic':(.78,.87,.89),'metal':(.34,.43,.50),'dark':(.055,.085,.12),'copper':(.72,.32,.10),'gold':(.95,.61,.15),'red':(.82,.16,.11),'blue':(.07,.43,.65),'grass':(.17,.29,.25),'concrete':(.39,.46,.45),'cyan':(.09,.80,.83)}.items():
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.metallic=.35 if name in ('metal','copper','gold') else .05;mat.roughness=.3;M[name]=mat
def finish(o,name,mat):
    o.name=name;o.data.materials.append(M[mat])
    if o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    return o
def box(name,loc,size,mat,bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('rounded machined edges','BEVEL');m.width=bevel;m.segments=3
        o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
    return finish(o,name,mat)
def cyl(name,loc,r,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=loc,rotation=(math.pi/2,0,0));return finish(bpy.context.object,name,mat)
def ball(name,loc,r,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=r,location=loc);return finish(bpy.context.object,name,mat)
def line(name,points,r,mat):
    cv=bpy.data.curves.new(name,'CURVE');cv.dimensions='3D';cv.bevel_depth=r;cv.bevel_resolution=2
    poly=cv.splines.new('POLY');poly.points.add(len(points)-1)
    for p,co in zip(poly.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,cv);scene.collection.objects.link(o);o.data.materials.append(M[mat]);return o
def empty(name,loc):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.location=loc;return o
def parent(o,p):world=o.matrix_world.copy();o.parent=p;o.matrix_world=world
# Environment gives scale and depth instead of a floating icon.
box('ground',(0,0,-.2),(200,200,.3),'grass',0)
box('foundation',(0,0,.05),(1.8,2,.3),'concrete')
for x in (-.65,.65):
    for y in (-.7,.7):cyl('foundation bolt',(x,y,.25),.07,.10,'metal')
box('tower',(0,.45,2.5),(.42,.55,4.8),'ceramic',.15)
box('service hatch',(0,.14,.6),(.22,.04,.6),'dark',.02)
for z in [i*.32+.7 for i in range(12)]:line('ladder rung',[(-.2,.80,z),(.2,.80,z)],.018,'metal')
box('nacelle bed',(0,.3,4.82),(2,2.2,.25),'metal')
shell=box('removable nacelle roof',(0,.35,5.7),(2.2,2.3,.7),'ceramic',.22)
rotor=empty('rigid rotor and shaft',(0,0,5.2))
shaft=cyl('direct-drive shaft',(0,-.15,5.2),.15,2.8,'metal');parent(shaft,rotor)
hub=cyl('blade hub',(0,-1.65,5.2),.35,.4,'ceramic');parent(hub,rotor)
for k in range(3):
    a=k*math.pi*2/3
    # A thick tapered airfoil silhouette, with a visible orange tip.
    def point(r,w,y):return (r*math.sin(a)+w*math.cos(a),y,5.2+r*math.cos(a)-w*math.sin(a))
    profile=[(.28,-.10),(.28,.10),(.8,.24),(2.5,.10),(2.8,.015),(2.5,-.05),(.9,-.14)]
    verts=[point(r,w,y) for y in (-1.90,-1.82) for r,w in profile];n=len(profile)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    mesh=bpy.data.meshes.new('airfoil');mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new('tapered blade',mesh);scene.collection.objects.link(ob);finish(ob,'tapered blade','ceramic');parent(ob,rotor)
    tip=line('orange blade marker',[point(2.4,-.01,-1.94),point(2.68,.02,-1.94)],.065,'gold');parent(tip,rotor)
    bearing=cyl('pitch bearing',point(.32,0,-1.76),.14,.20,'metal');parent(bearing,rotor)
cyl('main bearing outer',(0,-.90,5.2),.32,.28,'dark');cyl('main bearing race',(0,-1.05,5.2),.24,.05,'gold')
brake=cyl('brake disc',(0,-.55,5.2),.45,.06,'metal');parent(brake,rotor)
box('red brake caliper',(0,-.55,5.65),(.24,.26,.20),'red')
cyl('stator backing',(0,.88,5.2),1.02,.10,'dark')
disk=cyl('magnet rotor',(0,.15,5.2),.60,.22,'metal');parent(disk,rotor)
for k in range(8):
    a=k*math.pi/4
    o=box('north magnet' if k%2 else 'south magnet',(.50*math.sin(a),-.03,5.2+.50*math.cos(a)),(.16,.16,.19),'red' if k%2 else 'blue',.035);parent(o,rotor)
for k in range(12):
    a=k*math.pi/6;x,z=.83*math.sin(a),5.2+.83*math.cos(a)
    cyl('stationary iron core',(x,.55,z),.075,.62,'metal')
    for yy in (.35,.43,.51,.59,.67):
        bpy.ops.mesh.primitive_torus_add(major_radius=.115,minor_radius=.027,major_segments=16,minor_segments=6,location=(x,yy,z),rotation=(math.pi/2,0,0))
        finish(bpy.context.object,'stationary copper winding','copper')
# The new family reuses generator physics, with a visible crank instead of blades.
if HAND:
    for o in list(scene.objects):
        if o.name.startswith(('tapered blade','orange blade marker','pitch bearing','tower','service hatch','ladder rung')):o.hide_render=True
    box('bench support',(0,.45,2.45),(.6,.8,4.6),'dark',.08)
    box('workbench',(1,.4,4.6),(7,4,.18),'concrete')
    crank=line('crank arm',[(0,-1.95,5.2),(1.1,-1.95,5.2)],.11,'gold');parent(crank,rotor)
    grip=cyl('offset crank grip',(1.1,-2.2,5.2),.16,.55,'red');parent(grip,rotor)
line('outgoing cable',[(.85,.5,5.2),(1.4,.5,5.2),(1.4,-.4,.3),(3.5,-.4,.3),(3.5,-.4,1.3)],.035,'dark')
line('return cable',[(.55,.75,5.2),(1.1,.75,5.2),(1.1,-.4,.15),(4.3,-.4,.15),(4.3,-.4,1.3)],.035,'copper')
box('lamp base',(4.3,-.4,.5),(.7,.65,.2),'dark')
lamp=ball('lamp diffuser',(4.3,-.4,1.15),.35,'ceramic')
switch=line('switch blade',[(0,0,0),(.24,0,.255)],.045,'gold');switch.location=(3.5,-.4,1.3)
for k in range(2):ball('switch contact',(3.5+k*.35,-.4,1.3),.055,'metal')
line('switch-to-load connector',[(3.85,-.4,1.3),(4.3,-.4,1.3)],.035,'dark')
wind=[line('moving air trail',[(0,0,0),(0,.6,0)],.018,'cyan') for k in range(10)]
current=[ball('circuit marker',(0,0,0),.055,'cyan') for k in range(15)]
# Schematic field loops rotate with the magnets; coils remain stationary.
# These are explanatory geometry, not a measured field solution or literal light.
field_lines=[]
for k in range(4):
    a=(2*k+1)*math.pi/4
    points=[]
    for n in range(49):
        q=n/48*2*math.pi
        angle=a+(.5-.5*math.cos(q))*math.pi/4
        radius=.50+.50*math.sin(q)**2
        points.append((radius*math.sin(angle),.18+.16*math.sin(q),5.2+radius*math.cos(angle)))
    o=line('schematic magnetic field loop',points,.014,'cyan');parent(o,rotor);field_lines.append(o)
camdata=bpy.data.cameras.new('story camera');cam=bpy.data.objects.new('story camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.lens=48;camdata.clip_end=300;camdata.clip_start=.05
# A director grammar supplies a safe framing range; generated narration supplies timing.
SHOTS=[((1,0,3.9),(11.5,-19.5,11)),((0,-1.3,5.2),(4,-9,7)),((0,-1.5,5.2),(3,-6.5,6.6)),((0,-.45,5.2),(4,-5,7.4)),((0,.3,5.2),(3.7,-4.8,6.9)),((.55,.48,5.6),(2.3,-2.5,6.4)),((3.85,-.4,1.15),(6,-5,3)),((1,0,3.9),(11,-19,10.5))]
def state(t):
    i=min(7,next((i for i,b in enumerate(TL['beats']) if t<b['end']),7));b=TL['beats'][i];u=max(0,min(1,(t-b['start'])/(b['end']-b['start'])))
    return i,b,u
@persistent
def update(sc):
    t=(sc.frame_current-1)/FPS;i,b,u=state(t);rotor.rotation_euler[1]=rotor_angle(PLAN['mechanism'],t)
    for o in field_lines:o.hide_render=b['action'] not in ('generator','induction')
    cut=ramp(t,TL['beats'][3]['start']-.5,TL['beats'][3]['start']+.8)*(1-ramp(t,TL['beats'][7]['start'],TL['beats'][7]['start']+1))
    shell.location.z=5.7+3.5*cut
    for k,o in enumerate(wind):
        o.hide_render=HAND
        o.location=(-1.9+(k%4)*1.2,-6+(t*1.38+k*.63)%4.2,3.8+(k%3)*1.1)
    closed=i>=6
    angle=0 if closed else math.atan2(.255,.24)
    switch.data.splines[0].points[1].co=(.35*math.cos(angle),0,.35*math.sin(angle),1)
    lamp.data.materials[0]=M['gold'] if closed else M['ceramic']
    pts=[(1.4,-.4,5.2),(1.4,-.4,.3),(3.5,-.4,.3),(3.5,-.4,1.3),(4.3,-.4,1.3),(4.3,-.4,.15),(1.1,-.4,.15),(1.1,-.4,5.2)]
    for k,o in enumerate(current):
        o.hide_render=not closed;q=((t*.09+k/15)%1)*(len(pts)-1);j=int(q);o.location=Vector(pts[j]).lerp(Vector(pts[j+1]),q-j)
    target,pos=(Vector(v) for v in camera_pose(SHOTS,TL['beats'],t,PLAN['mechanism']))
    cam.location=pos;cam.rotation_euler=(target-pos).to_track_quat('-Z','Y').to_euler()
bpy.app.handlers.frame_change_pre.append(update)
scene.frame_start=1;scene.frame_end=math.ceil(TL['duration']*FPS)
if '--check-only' in sys.argv:
    # Validate scene geometry/visibility without generating any image or video.
    for beat in TL['beats']:
        t=(beat['start']+beat['end'])/2
        scene.frame_set(round(t*FPS)+1)
        visible=beat['action'] in ('generator','induction')
        if any(o.hide_render == visible or o.parent != rotor for o in field_lines):
            raise ValueError('Schematic field geometry/visibility is inconsistent')
        if any(o.parent == rotor for o in scene.objects if o.name.startswith('stationary')):
            raise ValueError('Stationary generator parts must not rotate')
    print(json.dumps({'geometry_check':'passed','rendered_images':0,'generated_video':False}),flush=True)
    sys.exit(0)
frames=ROOT/'frames';frames.mkdir(exist_ok=True)
# First preserve eight diagnostic renders, before spending time on the complete animation.
times=[(b['start']+b['end'])/2 for b in TL['beats']]
for i,t in enumerate(times):
    scene.frame_set(round(t*FPS)+1);scene.render.filepath=str(ROOT/f'check-{i}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'generated-scene.blend'))
scene.render.filepath=str(frames/'#####');bpy.ops.render.render(animation=True)
