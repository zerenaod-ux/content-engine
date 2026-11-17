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
