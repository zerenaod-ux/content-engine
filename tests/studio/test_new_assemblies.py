import math,tempfile,unittest
from pathlib import Path
import numpy as np
from studio_lib import zipper,stapler,optical_fiber as fiber,ratchet_wrench as ratchet
from studio_lib.registry import REGISTRY
from studio_lib.director import verify_component

def intersects(a,b):
 a,b=np.asarray(a),np.asarray(b)
 if np.any(np.minimum(a.max(0),b.max(0))-np.maximum(a.min(0),b.min(0))<=1e-7):return False
 for pts in (a,b):
  for p,q in zip(pts,np.roll(pts,-1,axis=0)):
   axis=np.array([q[1]-p[1],p[0]-q[0]]);aa=a@axis;bb=b@axis
   if min(aa.max(),bb.max())-max(aa.min(),bb.min())<=1e-7:return False
 return True

class Assemblies(unittest.TestCase):
 def timeline(self,key):return {'beats':[{'start':i*6,'end':(i+1)*6,'action':a,'camera':'wide','say':'Engineering test fixture only'} for i,a in enumerate(REGISTRY[key]['actions'])],'duration':48,'motion_policy':'fixture'}
 def test_zipper_rigid_elements_do_not_interpenetrate_in_the_y_guide(self):
  rectangles=[[(-.07,-.2),(.07,-.2),(.07,.05),(-.07,.05)],[(-.13,.05),(.13,.05),(.13,.22),(-.13,.22)]]
  for slider in np.linspace(zipper.START,zipper.END,49):
   elements=[(side,float(x),np.array(zipper.tooth_pose(side,x,slider,rect))) for side,xs in ((-1,zipper.LEFT),(1,zipper.RIGHT)) for x in xs if abs(x-slider)<1.6 for rect in rectangles]
   for i,(side,x,a) in enumerate(elements):
    for other,y,b in elements[i+1:]:
     if side==other and x==y:continue
     self.assertFalse(intersects(a,b),'Rigid zipper elements crossed inside the slider')
 def test_zipper_completes_one_close_and_one_open(self):
  tl=self.timeline('zipper');closed=zipper.state(35.9,tl);opened=zipper.state(47.9,tl)
  self.assertEqual(closed['joined'],len(zipper.LEFT)+len(zipper.RIGHT));self.assertEqual(opened['joined'],0)
  original=np.array(zipper.tooth(-1,0,zipper.START));moved=np.array(zipper.tooth(-1,0,0))
  self.assertAlmostEqual(np.linalg.norm(original[0]-original[4]),np.linalg.norm(moved[0]-moved[4]))
 def test_staple_wire_preserves_length_and_bends_at_the_anvil(self):
  for crown in np.linspace(2.2,stapler.FINAL,121):
   for side in (-1,1):
    p=stapler.leg_points(crown,side)
    length=sum(np.linalg.norm(np.subtract(b,a)) for a,b in zip(p,p[1:]))
    self.assertAlmostEqual(length,stapler.LEG,delta=1e-4)
    self.assertGreaterEqual(p[-1][2],stapler.ANVIL-1e-8)
    if crown>stapler.CONTACT:self.assertEqual(stapler.bend_angle(crown),0)
    else:self.assertAlmostEqual(p[-1][2],stapler.ANVIL,places=8)
 def test_clinched_staple_stays_when_the_driver_returns(self):
  tl=self.timeline('stapler');a=stapler.state(36.01,tl);b=stapler.state(41.99,tl)
  self.assertAlmostEqual(a['crown_z'],b['crown_z']);self.assertGreater(b['driver_z'],a['driver_z']);self.assertAlmostEqual(b['bend'],math.pi/2)
 def test_fibre_reflects_at_real_boundaries_above_critical_angle(self):
  for point in fiber.PATH:self.assertLessEqual(abs(point[2]-fiber.Z),fiber.RADIUS+1e-9)
  for a,b,c in zip(fiber.PATH,fiber.PATH[1:],fiber.PATH[2:]):
   incoming=np.subtract(b,a);incoming/=np.linalg.norm(incoming);outgoing=np.subtract(c,b);outgoing/=np.linalg.norm(outgoing)
   self.assertAlmostEqual(incoming[0],outgoing[0]);self.assertAlmostEqual(incoming[2],-outgoing[2])
   self.assertGreater(math.acos(abs(incoming[2])),fiber.CRITICAL)
 def test_fibre_receiver_waits_for_the_signal(self):
  tl=self.timeline('optical_fiber')
  self.assertEqual(fiber.state(23.99,tl)['output'],0);self.assertEqual(fiber.state(30.,tl)['output'],1)
 def test_ratchet_wheel_never_reverses_and_pawl_stays_on_the_teeth(self):
  tl=self.timeline('ratchet_wrench');last=-1.
  for t in np.linspace(0,47.99,600):
   p=ratchet.state(t,tl);self.assertGreaterEqual(p['wheel'],last-1e-12);last=p['wheel']
   self.assertGreaterEqual(p['pawl_r'],ratchet.R0-1e-9);self.assertLessEqual(p['pawl_r'],ratchet.R1+1e-9)
  self.assertAlmostEqual(ratchet.state(47.99,tl)['wheel'],2*ratchet.STROKE);self.assertAlmostEqual(ratchet.state(47.99,tl)['handle'],0.)
 def test_each_new_assembly_passes_real_visibility_and_motion_preflight(self):
  for key in ('zipper','stapler','optical_fiber','pendulum_clock','ratchet_wrench'):
   with self.subTest(key=key),tempfile.TemporaryDirectory() as folder:
    tl=self.timeline(key);verify_component({'mechanism':key,'beats':tl['beats'],'hook':'Engineering check'},tl,Path(folder))
