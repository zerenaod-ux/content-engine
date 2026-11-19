import json,tempfile,unittest
from pathlib import Path
from test_components import plan_fixture,timeline
from studio_lib.director import validate,verify

class CounterweightQualityTests(unittest.TestCase):
 def test_rising_counterweight_cannot_be_claimed_as_releasing_energy(self):
  plan=plan_fixture()
  plan['beats'][6]['say']='After the ship clears the rising counterweight returns energy to the system as the road descends.'
  self.assertTrue(any('potential energy' in error for error in validate(plan)))
  plan['beats'][6]['say']='After the ship clears the road descends while the counterweight rises and gains gravitational potential energy.'
  self.assertFalse(any('potential energy' in error for error in validate(plan)))
 def test_counterweight_must_remain_visible_across_its_explanation(self):
  with tempfile.TemporaryDirectory() as folder:
   verify(plan_fixture(),timeline(),Path(folder))
   self.assertEqual(json.loads((Path(folder)/'component-checks.json').read_text())['errors'],[])

if __name__=='__main__':unittest.main()
