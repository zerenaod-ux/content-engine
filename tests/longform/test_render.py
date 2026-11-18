import unittest
import numpy as np
from studio_lib.longform.render import frame
from studio_lib.longform.contract import ACTIONS
class NativeRenderTests(unittest.TestCase):
 def test_both_supported_mechanisms_use_native_landscape_and_actual_moving_geometry(self):
  timeline={'beats':[{'action':a,'start':i*10,'end':(i+1)*10} for i,a in enumerate(ACTIONS)]}
  for mechanism in ('rack_pinion','lead_screw','cam_follower'):
   p={'mechanism':mechanism,'hook':'Why does it move?'}
   a=frame(41,timeline,p);b=frame(49,timeline,p)
   self.assertEqual(a.size,(1280,720));self.assertGreater(np.count_nonzero(np.max(abs(np.asarray(a).astype(int)-np.asarray(b).astype(int)),axis=2)>25),1000)
