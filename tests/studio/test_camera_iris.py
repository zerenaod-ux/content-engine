"""Physical invariants for the reusable optical iris, without media calls."""
import unittest,math,json,os,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from studio_lib import iris,novelty

class CameraIrisTests(unittest.TestCase):
 def test_rigid_blades_and_fixed_pivots(self):
  for k in range(iris.N):
   expected=np.linalg.norm(iris.blade_points(k,iris.OPEN_ANGLE)[1]-iris.blade_points(k,iris.OPEN_ANGLE)[0])
   for a in np.linspace(iris.OPEN_ANGLE,iris.CLOSED_ANGLE,25):
    self.assertAlmostEqual(np.linalg.norm(iris.blade_points(k,a)[1]-iris.blade_points(k,a)[0]),expected)
    self.assertAlmostEqual(np.linalg.norm(iris.pivot(k)),iris.PIVOT_RADIUS)
 def test_ring_slots_follow_control_pins(self):
  for k in range(iris.N):
   for a in np.linspace(iris.OPEN_ANGLE,iris.CLOSED_ANGLE,50):
    np.testing.assert_allclose(iris.rotate(iris.slot_point(k,a),iris.ring_angle(a)),iris.control_pin(k,a),atol=1e-12)
 def test_closing_reduces_opening_without_sealing_center(self):
  areas=[iris.opening_area(a) for a in np.linspace(iris.OPEN_ANGLE,iris.CLOSED_ANGLE,50)]
  self.assertTrue(all(a>b>0 for a,b in zip(areas,areas[1:])))
  for a in np.linspace(iris.OPEN_ANGLE,iris.CLOSED_ANGLE,50):self.assertTrue(iris.passes((0,0),a))
 def test_off_axis_light_blocked_by_closed_iris(self):
  self.assertTrue(iris.passes((.65,0),iris.OPEN_ANGLE))
  self.assertFalse(iris.passes((.65,0),iris.CLOSED_ANGLE))
 def test_stage_holds_and_reversal(self):
  tl={'beats':[{'start':i*6,'end':(i+1)*6} for i in range(8)]}
  self.assertAlmostEqual(iris.state(29,tl)['angle'],iris.CLOSED_ANGLE)
  self.assertAlmostEqual(iris.state(37,tl)['angle'],iris.OPEN_ANGLE)
  self.assertLess(iris.state(25,tl)['brightness'],iris.state(37,tl)['brightness'])
  self.assertAlmostEqual(iris.state(47.999,tl)['angle'],iris.OPEN_ANGLE)
 def test_final_iris_hold_uses_existing_spoken_words(self):
  from studio_lib.narration_timing import normalize_cues,cue_errors
  plan={'mechanism':'camera_iris','beats':[{'action':'payoff','say':'Finally the iris stays open, showing how coordinated blades control the light.','motion_cue':'iris stays open'}]}
  fixed=normalize_cues(plan)
  self.assertEqual(fixed['beats'][0]['say'],plan['beats'][0]['say'])
  self.assertEqual(cue_errors(fixed),[])
 def test_new_family_does_not_unblock_old_families(self):
  self.assertEqual(novelty.identity('', 'camera_iris'),'optical_iris')
  self.assertEqual(novelty.identity('How a camera aperture controls light'),'optical_iris')
  self.assertTrue(novelty.reason('Why another wind turbine spins','wind_turbine',[{'mechanism':'hand_generator','state':'created'}],None))

class IrisVisibilityTests(unittest.TestCase):
 def test_overview_and_internal_parts_visible_before_production(self):
  from studio_lib.director import verify_component
  from studio_lib.registry import REGISTRY
  beats=[{'start':i*6,'end':(i+1)*6,'action':a,'camera':'wide','say':'Engineering fixture only.'} for i,a in enumerate(REGISTRY['camera_iris']['actions'])]
  plan={'mechanism':'camera_iris','hook':'Engineering visibility fixture','beats':beats}
  timeline={'beats':beats,'duration':48,'motion_policy':'engineering-fixture'}
  with tempfile.TemporaryDirectory() as directory:
   verify_component(plan,timeline,Path(directory))
   evidence=json.loads((Path(directory)/'component-checks.json').read_text())
   self.assertEqual(evidence['errors'],[])
   self.assertEqual({row['part'] for row in evidence['measurements']},{'blades','ring','pins','sensor'})

class FinalNarrationStateTests(unittest.TestCase):
 def test_iris_cannot_return_again_during_housing_return(self):
  from studio_lib.director import validate
  from test_library import fixture
  plan=fixture('camera_iris')
  plan['beats'][2]['say']='This simplified cutaway exposes the fixed pivots and blade control ring inside the camera so their physical connections become visible.'
  plan['beats'][7]['say']='The iris returns to its original state, showing how coordinated blade movement directly controls brightness.'
  self.assertTrue(any('already open and held' in error for error in validate(plan)))
  plan['beats'][7]['say']='The housing returns over the lens while the iris stays open, preserving the same mechanical control of incoming light.'
  self.assertFalse(any('already open and held' in error for error in validate(plan)))

class SelectionProvenanceTests(unittest.TestCase):
 def test_only_owned_system_selection_supplies_component(self):
  from studio_lib.production import selected_mechanism
  original=Path.cwd()
  with tempfile.TemporaryDirectory() as directory:
   try:
    os.chdir(directory)
    d={'topic':'Why an aperture changes light','subject':'camera_iris','selected_by_system':True,'selection_owner':'proof'}
    Path('idea.json').write_text(json.dumps(d))
    with patch.dict(os.environ,{'GITHUB_RUN_ID':'proof'}):
     self.assertEqual(selected_mechanism(d['topic']),'camera_iris')
     self.assertIsNone(selected_mechanism('Another topic'))
    with patch.dict(os.environ,{'GITHUB_RUN_ID':'foreign'}):self.assertIsNone(selected_mechanism(d['topic']))
   finally:os.chdir(original)

if __name__=='__main__':unittest.main()
