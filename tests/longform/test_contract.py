import math,unittest
from studio_lib.longform.contract import motion,require_media,errors
class FullContractTests(unittest.TestCase):
 def test_full_duration_and_native_landscape_are_distinct_from_shorts(self):
  require_media(150,1280,720)
  for values in [(40,1280,720),(301,1280,720),(150,720,1280),(float('nan'),1280,720)]:
   with self.assertRaises(ValueError):require_media(*values)
 def test_rigid_motion_uses_one_causal_coordinate_and_stays_bounded(self):
  for t in range(300):
   r=motion(t,'rack_pinion');self.assertLessEqual(abs(r['travel']),1.45);self.assertAlmostEqual(r['travel'],-.6*r['angle'])
   s=motion(t,'lead_screw');self.assertAlmostEqual(s['travel'],s['angle']/(2*math.pi)*.45)
 def test_compilation_or_unsupported_plan_cannot_pass(self):
  self.assertTrue(errors({'mechanism':'compilation','beats':[]}))
 def test_forward_and_reverse_follow_their_actual_narration_chapters(self):
  from studio_lib.longform.contract import ACTIONS
  tl={'beats':[{'action':a,'start':i*10,'end':(i+1)*10} for i,a in enumerate(ACTIONS)]}
  self.assertLess(motion(40.1,'rack_pinion',tl)['travel'],motion(49.9,'rack_pinion',tl)['travel'])
  self.assertGreater(motion(60.1,'rack_pinion',tl)['travel'],motion(69.9,'rack_pinion',tl)['travel'])
  for i in range(1,16):self.assertAlmostEqual(motion(i*10-.00001,'lead_screw',tl)['travel'],motion(i*10+.00001,'lead_screw',tl)['travel'],places=7)
 def test_cam_roller_contact_and_direction_are_physically_coupled(self):
  from studio_lib.longform.contract import cam_state,mechanism_facts
  for angle in [i*.1 for i in range(100)]:
   s=cam_state(angle);distance=math.hypot(s['cam_x'],s['follower_z']-s['cam_z'])
   self.assertAlmostEqual(distance,s['cam_radius']+s['roller_radius']);self.assertLess(s['follower_z']+.43,3.32)
  self.assertIn('SAME direction',mechanism_facts('cam_follower')['reverse'])
 def test_cam_rise_and_return_match_their_spoken_chapters(self):
  from studio_lib.longform.contract import ACTIONS
  tl={'beats':[{'action':a,'start':i*10,'end':(i+1)*10} for i,a in enumerate(ACTIONS)]}
  self.assertLess(motion(40.1,'cam_follower',tl)['follower_z'],motion(49.9,'cam_follower',tl)['follower_z'])
  self.assertGreater(motion(60.1,'cam_follower',tl)['follower_z'],motion(69.9,'cam_follower',tl)['follower_z'])
