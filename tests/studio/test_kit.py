import copy,sys,types,unittest
sys.modules.setdefault('edge_tts',types.ModuleType('edge_tts'))
from studio_lib.kit import recipe,samples
R=recipe.RecipeError
class Kit(unittest.TestCase):
 def test_samples_validate_and_state_is_deterministic(self):
  tl={'beats':[{'start':i*6,'end':(i+1)*6} for i in range(8)]}
  for name in samples.SAMPLES:
   m=recipe.Machine(recipe.validate(getattr(samples,name)))
   self.assertEqual(m.state(20.,tl),m.state(20.,tl))
   self.assertEqual(len(m.SHOTS),8)
   for tgt,zoom,az in m.SHOTS:self.assertTrue(1.0<=zoom<=2.8)
 def bad(self,change):
  r=copy.deepcopy(samples.GEAR_CRANK);change(r)
  with self.assertRaises(R):recipe.validate(r)
 def test_rejects_unsafe_recipes(self):
  self.bad(lambda r:r['parts'][2].update(center=[-2.4,3.5]))            # gears no longer mesh
  self.bad(lambda r:r['parts'][1].update(kind='rocket'))               # unknown kind
  self.bad(lambda r:r['parts'].append(dict(r['parts'][1])))            # duplicate id
  self.bad(lambda r:r.update(drive=[{'beat':1,'part':'big','to':3}]))  # too little motion
  self.bad(lambda r:r.update(labels={'big':'Drive gear'}))             # too few labels
  self.bad(lambda r:r['drive'].append({'beat':2,'part':'left','to':1}))# keyframing a driven part
  self.bad(lambda r:r['parts'][2].update(r=3.0))                       # gear leaves frame / too big
 def test_mesh_ratio_and_direction(self):
  m=recipe.Machine(recipe.validate(samples.GEAR_CRANK));tl={'beats':[{'start':i*6,'end':(i+1)*6} for i in range(8)]}
  v=m.state(40.,tl);self.assertLess(v['left']*v['big'],0)
 def test_slider_never_leaves_its_travel(self):
  m=recipe.Machine(recipe.validate(samples.DOOR_LATCH));tl={'beats':[{'start':i*6,'end':(i+1)*6} for i in range(8)]}
  for t in range(48):self.assertTrue(-1e-9<=m.state(float(t),tl)['bolt']<=1.0+1e-6)
 def test_slider_beyond_travel_is_rejected(self):
  r=copy.deepcopy(samples.DOOR_LATCH);r['parts'][2]['travel']=.5
  with self.assertRaises(R):recipe.validate(r)

 def test_recipe_installs_as_full_mechanism_and_passes_real_preflight(self):
  import tempfile
  from pathlib import Path
  from studio_lib.kit import register
  from studio_lib import director,action_contracts,novelty
  from studio_lib.registry import REGISTRY
  for name in samples.SAMPLES:
   with self.subTest(name),tempfile.TemporaryDirectory() as folder:
    key=register.install(samples.with_facts(getattr(samples,name)),director.COMPONENTS)
    self.assertIn(key,REGISTRY);self.assertIn(key,novelty.FAMILIES)
    tl={'beats':[{'start':i*6,'end':(i+1)*6,'action':a,'camera':'wide','say':'Engineering test fixture only'} for i,a in enumerate(REGISTRY[key]['actions'])],'duration':48,'motion_policy':'fixture'}
    director.verify_component({'mechanism':key,'beats':tl['beats'],'hook':'Engineering check'},tl,Path(folder))
 def test_family_of_unknown_recipe_key_is_single_use(self):
  from studio_lib import novelty
  self.assertEqual(novelty.families({'mechanism':'recipe_never_seen_before'}),{'recipe_never_seen_before'})

 def test_yoke_slot_must_keep_the_lever_tip_joined(self):
  r=copy.deepcopy(samples.DOOR_LATCH);r['parts'][2]['size']=[3.2,.6]
  with self.assertRaises(R):recipe.validate(r)
 def test_cam_and_rope_geometry_is_checked(self):
  r=copy.deepcopy(samples.CAM_PRESS);r['parts'][2]['origin']=[0,3.0]
  with self.assertRaises(R):recipe.validate(r)
  r=copy.deepcopy(samples.ROPE_LIFT);r['parts'][2]['origin']=[2.0,2.6]
  with self.assertRaises(R):recipe.validate(r)
 def test_moving_parts_stay_inside_the_screen_for_the_whole_video(self):
  import numpy as np
  from studio_lib.mesh import Scene
  from studio_lib.camera_direction import tracked_shot,flourish
  tl={'beats':[{'start':i*6.,'end':(i+1)*6.,'say':'Test narration for the framing check.','voice_duration':5.} for i in range(8)],'duration':48}
  for name in samples.SAMPLES:
   m=recipe.Machine(recipe.validate(getattr(samples,name)));moving=m.moving_ids()
   hidden=tuple(p['id'] for p in m.r['parts'] if p['id'] not in moving)
   for t in np.linspace(.2,47.8,160):
    i=min(7,int(t//6));zoom,target,az=tracked_shot(t,tl['beats'],i,m);zoom,target,az=flourish(t,tl['beats'][i],i,8,zoom,target,az)
    s=Scene(t,zoom,target,az,elevation=5.5);m.draw(s,t,tl,hidden)
    pts=np.array([q for _,poly,_ in s.faces for q in poly])
    self.assertTrue(pts[:,0].min()>=15 and pts[:,0].max()<=705 and pts[:,1].min()>=290 and pts[:,1].max()<=1175,(name,round(t,1),pts.min(0).tolist(),pts.max(0).tolist()))
