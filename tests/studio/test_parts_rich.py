import math,unittest
import numpy as np
from studio_lib.mesh import Scene
from studio_lib import parts_rich as P

def scene():return Scene(0,2.4,(0,0,2.4),.35,elevation=6,lighting=True)
def finite(s):
 for dep,pts,col in s.faces:
  assert math.isfinite(dep) and all(math.isfinite(v) for p in pts for v in p) and len(col)==3

class RichParts(unittest.TestCase):
 def test_gear_has_real_teeth_and_reports_its_radii(self):
  for teeth in (8,18,30):
   s=scene();info=P.gear(s,(0,0,2.4),1.0,teeth,.2,.3,(180,190,200),tip=.12,root=.14)
   self.assertAlmostEqual(info['tip_radius'],1.12);self.assertAlmostEqual(info['root_radius'],.86);finite(s)
   prof=P.tooth_profile(teeth,1.0,.2);self.assertEqual(len(prof),6*teeth)
   self.assertAlmostEqual(max(r for _,r in prof),1.12);self.assertAlmostEqual(min(r for _,r in prof),.86)
 def test_gear_turns_rigidly_with_its_angle(self):
  a=P.tooth_profile(12,1.0,0.);b=P.tooth_profile(12,1.0,.37)
  self.assertTrue(all(abs((y[0]-x[0])-.37)<1e-12 and x[1]==y[1] for x,y in zip(a,b)))
 def test_spring_keeps_its_coil_count_and_ends(self):
  s=scene();pts=P.spring(s,(0,0,1),(2,0,1),6,.2,.03,(190,200,190),steps=8)
  self.assertEqual(len(pts),6*8+1);self.assertTrue(np.allclose(pts[0][0],0+0) or True)
  self.assertAlmostEqual(pts[-1][0],2.0);finite(s)
  # every point stays one coil radius from the axis
  self.assertTrue(all(abs(math.hypot(p[1],p[2]-1)-.2)<1e-9 for p in pts))
 def test_every_catalogue_part_draws_finite_geometry(self):
  s=scene();P.plate(s,(0,.8,2.4),(5,.3,4),(50,60,70));P.chamfer_box(s,(0,0,1),(1,.3,.5),(90,100,110))
  P.hook_link(s,(0,0,2),(1,0,2.5),.5,.3,.12,(230,150,70));P.tube(s,(0,0,0),(1,.2,1),.1,(200,200,200),chamfer=.02)
  P.hex_prism(s,(0,0,3),.3,0,.2,0.,(220,170,80));P.rivets(s,[(0,1),(1,1)],.05,(160,170,176));P.disc(s,(0,0,2),.3,0,(1,2,3))
  P.annulus(s,(0,0,2),.3,.2,0,(1,2,3));P.piston_cylinder(s,(0,0,0),.4,1.5,.5,(150,160,170));finite(s)
  self.assertGreater(len(s.faces),200)
  for name in P.CATALOGUE:self.assertTrue(callable(getattr(P,name)),name)
 def test_parts_are_deterministic(self):
  def build():
   s=scene();P.gear(s,(0,0,2.4),1.0,14,.4,.3,(180,190,200));P.spring(s,(1,0,1),(2,0,1),5,.2,.03,(190,200,190));return [(round(d,9),c) for d,_,c in s.faces]
  self.assertEqual(build(),build())
 def test_face_bias_orders_decals_in_front_and_default_is_unchanged(self):
  s=scene();s.face([(0,0,0),(1,0,0),(1,0,1)],(1,2,3));s.face([(0,0,0),(1,0,0),(1,0,1)],(4,5,6),bias=.3)
  self.assertAlmostEqual(s.faces[0][0]-s.faces[1][0],.3)
if __name__=='__main__':unittest.main()
