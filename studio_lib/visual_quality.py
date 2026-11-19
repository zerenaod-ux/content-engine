"""A fixed native-resolution studio finish, independent of topic geometry."""
import functools
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
POLICY='native-studio-1080-v1'
SAMPLE_SCALE=2
WIDTH,HEIGHT=1080,1920
KEY=np.array([-.36,-.48,.80])
KEY=KEY/np.linalg.norm(KEY)

def lit_color(points,color,eye):
 p=np.asarray(points,float);normal=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(normal)
 if length<1e-10:return color
 normal/=length
 center=p.mean(axis=0);view=np.asarray(eye)-center;view/=max(np.linalg.norm(view),1e-9)
 diffuse=abs(float(normal@KEY));half=KEY+view;half/=max(np.linalg.norm(half),1e-9)
 spec=abs(float(normal@half))**36
 # Broad fill keeps small internal components legible; highlights are bounded.
 linear=(np.asarray(color,dtype=float)/255)**2.2
 output=np.clip(linear*(.70+.33*diffuse)+.035*spec,0,1)**(1/2.2)
 return tuple(np.uint8(output*255))

def shadow(scene,image,floor):
 mask=Image.new('L',image.size);draw=ImageDraw.Draw(mask);scale=scene.raster_scale
 for points in scene.world_faces:
  if np.min(points[:,2])<floor-.02:continue
  ground=points-((points[:,2]-floor)/KEY[2])[:,None]*KEY
  projected,depth=scene.project(ground)
  if min(depth)<.2:continue
  draw.polygon([tuple(point*scale) for point in projected],fill=43)
 mask=mask.filter(ImageFilter.GaussianBlur(5*scale))
 shade=Image.new('RGB',image.size,(12,22,29));image.paste(shade,(0,0),mask)

def finish(image):
 if image.size!=(720*SAMPLE_SCALE,1280*SAMPLE_SCALE):raise ValueError('Quality rendering requires native supersampled geometry, not an upscaled low-resolution frame')
 return image.resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)

@functools.lru_cache(maxsize=16)
def font(original):return original.font_variant(size=original.size*SAMPLE_SCALE)
