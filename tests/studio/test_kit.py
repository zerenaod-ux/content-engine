import copy,sys,types,unittest
sys.modules.setdefault('edge_tts',types.ModuleType('edge_tts'))
from studio_lib.kit import recipe,samples
R=recipe.RecipeError
class Kit(unittest.TestCase):
 def test_samples_validate_and_state_is_deterministic(self):
  tl={'beats':[{'start':i*6,'end':(i+1)*6} for i in range(8)]}
  for name in ('DOOR_LATCH','GEAR_CRANK'):
   m=recipe.Machine(recipe.validate(getattr(samples,name)))
   self.assertEqual(m.state(20.,tl),m.state(20.,tl))
   self.assertEqual(len(m.SHOTS),8)
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
  v=m.state(40.,tl)['values'];self.assertLess(v['left']*v['big'],0)
 def test_slider_never_leaves_its_travel(self):
  m=recipe.Machine(recipe.validate(samples.DOOR_LATCH));tl={'beats':[{'start':i*6,'end':(i+1)*6} for i in range(8)]}
  for t in range(48):self.assertLessEqual(abs(m.state(float(t),tl)['values']['bolt']),1.1+1e-6)
 def test_slider_beyond_travel_is_rejected(self):
  r=copy.deepcopy(samples.DOOR_LATCH);r['parts'][2]['travel']=.5
  with self.assertRaises(R):recipe.validate(r)
