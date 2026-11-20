import unittest
import numpy as np
from studio_lib.camera_direction import tracked_shot,pose
from studio_lib import electric_relay

class SpokenCameraTests(unittest.TestCase):
 def setUp(self):
  self.beats=[{'start':i*6.,'end':(i+1)*6.,'motion_window':[i*6.+2.,i*6.+4.]} for i in range(8)]
 def test_detail_is_closer_but_context_is_preserved(self):
  for i in (0,7):self.assertEqual(pose(electric_relay,i,8)[1],electric_relay.shot(i)[1])
  self.assertGreater(pose(electric_relay,3,8)[1],electric_relay.shot(3)[1]*1.2)
 def test_camera_arrives_before_measured_action_and_holds(self):
  for i in range(1,8):
   b=self.beats[i];expected=pose(electric_relay,i,8)
   for t in (b['motion_window'][0],b['end']-.001):
    z,p,a=tracked_shot(t,self.beats,i,electric_relay)
    self.assertAlmostEqual(z,expected[1]);np.testing.assert_allclose(p,expected[0]);self.assertAlmostEqual(a,expected[2])
 def test_no_jump_between_beats_and_no_random_drift(self):
  for i in range(1,8):
   left=tracked_shot(self.beats[i]['start']-1e-7,self.beats,i-1,electric_relay)
   right=tracked_shot(self.beats[i]['start'],self.beats,i,electric_relay)
   self.assertAlmostEqual(left[0],right[0],places=5);np.testing.assert_allclose(left[1],right[1],atol=1e-5)
 def test_early_action_still_gets_a_bounded_smooth_transition(self):
  self.beats[3]['motion_window']=[18.1,20.]
  for t in np.linspace(18,24,60):
   z,p,a=tracked_shot(t,self.beats,3,electric_relay);self.assertTrue(np.isfinite([z,*p,a]).all())
