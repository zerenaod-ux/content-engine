"""Data-driven Blender diagram backend; shares narration/audio/delivery pipeline.

--check-only constructs and samples geometry without rendering any images/video.
"""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import bpy
from mathutils import Vector
from bpy.app.handlers import persistent
from studio_lib.science.components import diagram,SPECS
from studio_lib.cinema.presentation import ease
ROOT=Path(sys.argv[sys.argv.index('--')+1]);TL=json.loads((ROOT/'timeline.json').read_text());PLAN=json.loads((ROOT/'plan.json').read_text())
mechanism=PLAN['mechanism']
if mechanism not in SPECS:raise ValueError('No diagram component')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=540;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.render.fps=24;scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.world.color=(.16,.22,.28);scene.display.shading.background_type='WORLD'
scene.view_settings.view_transform='Standard'
camdata=bpy.data.cameras.new('diagram camera');cam=bpy.data.objects.new('diagram camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=11.5
cam.location=(1.5,-16,6);target=Vector((0,0,2.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
objects={};texts=[]
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m

def add(item):
 kind=item['kind'];name=item['id']
 if kind=='box':
  bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object
  bevel=o.modifiers.new('soft edges','BEVEL');bevel.width=.04;bevel.segments=2
 elif kind=='ball':
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1);o=bpy.context.object
 elif kind=='line':
  curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=item['radius'];curve.bevel_resolution=2
  spline=curve.splines.new('POLY');spline.points.add(len(item['points'])-1)
  o=bpy.data.objects.new(name,curve);scene.collection.objects.link(o)
 else:raise ValueError('Unknown geometry primitive')
 o.name=name;o.data.materials.append(material(name,item['color']));objects[name]=o

first=diagram(mechanism,0)
for item in first['objects']:add(item)
for i,label in enumerate(first['labels']):
 curve=bpy.data.curves.new('label '+str(i),'FONT');curve.size=.20;curve.align_x='CENTER'
 obj=bpy.data.objects.new('label '+str(i),curve);scene.collection.objects.link(obj);obj.data.materials.append(material('text '+str(i),(.95,.96,1)));texts.append(obj)

def progress(t):
 # Motion follows its narration beat, not an arbitrary physical time scale.
 start=TL['beats'][3]['start'];end=TL['beats'][5]['end']
 return ease((t-start)/(end-start))

@persistent
def update(sc):
 t=(sc.frame_current-1)/24;p=progress(t);data=diagram(mechanism,p)
 for item in data['objects']:
  o=objects[item['id']];o.data.materials[0].diffuse_color=(*item['color'],1)
  if item['kind']=='line':
   for point,co in zip(o.data.splines[0].points,item['points']):point.co=(*co,1)
  else:
   o.location=item['at'];o.scale=item['size'] if item['kind']=='box' else (item['radius'],)*3
 for o,label in zip(texts,data['labels']):
  o.data.body=label['text'];o.location=label['at'];o.rotation_euler=(cam.location-o.location).to_track_quat('Z','Y').to_euler()
 # Gentle whole-diagram framing, continuous with zero velocity at endpoints.
 camdata.ortho_scale=11.5-.35*ease(t/TL['duration'])

bpy.app.handlers.frame_change_pre.append(update)
scene.frame_start=1;scene.frame_end=math.ceil(TL['duration']*24)
if '--check-only' in sys.argv:
 for beat in TL['beats']:
  scene.frame_set(round((beat['start']+beat['end'])/2*24)+1)
  if any(not all(math.isfinite(x) for x in o.location) for o in objects.values()):raise ValueError('Invalid geometry')
 print(json.dumps({'geometry_check':'passed','mechanism':mechanism,'objects':len(objects),'rendered_images':0,'generated_video':False}),flush=True)
 sys.exit(0)
frames=ROOT/'frames';frames.mkdir(exist_ok=True)
for i,b in enumerate(TL['beats']):
 scene.frame_set(round((b['start']+b['end'])/2*24)+1);scene.render.filepath=str(ROOT/f'check-{i}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'generated-scene.blend'))
scene.render.filepath=str(frames/'#####');bpy.ops.render.render(animation=True)
