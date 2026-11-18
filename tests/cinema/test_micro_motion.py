import unittest
from studio_lib.science.components import diagram
from studio_lib.science.micro_motion import lattice,transfer_markers
class MicroMotionTests(unittest.TestCase):
 def test_solid_particles_move_locally_without_crossing_the_contact_surface(self):
  for clock in range(100):
   for side,x,temp in [(0,-1,90),(1,1,10)]:
    for item in lattice((x,-.12,2),temp,clock,side):
     self.assertLess(item['at'][0],0) if side==0 else self.assertGreater(item['at'][0],0)
  self.assertNotEqual(lattice((-1,0,2),90,0,0),lattice((-1,0,2),90,.2,0))
 def test_energy_symbols_stop_at_equilibrium_while_vibration_continues(self):
  self.assertTrue(all(not x['visible'] for x in transfer_markers(1,3)))
  self.assertNotEqual(lattice((-1,0,2),50,1,0),lattice((-1,0,2),50,2,0))
 def test_highlight_and_arrow_exist_and_particle_inventory_is_persistent(self):
  a=diagram('thermal_contact',0,0,0);b=diagram('thermal_contact',.6,4,.8)
  self.assertEqual([x['id'] for x in a['objects']],[x['id'] for x in b['objects']])
  self.assertIn('contact_surface',[x['id'] for x in b['objects']]);self.assertIn('heat_arrow_head',[x['id'] for x in b['objects']])
  self.assertGreater(len(b['objects']),30)
