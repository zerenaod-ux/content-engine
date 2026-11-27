"""Cross-scene physics, rendering and real failure regressions; no media calls."""
import copy,json,tempfile,unittest,math
from pathlib import Path
from unittest.mock import patch
import numpy as np
from studio_lib import float_valve as tank,combination_lock as lock,storytelling,narration_timing,action_contracts,novelty
from studio_lib.registry import REGISTRY
from studio_lib.director import verify_component,repair_causal_sections

def fixture(kind):
 beats=[{'action':a,'start':i*6.,'end':(i+1)*6.,'camera':'wide','say':'Engineering fixture, not production dialogue.'} for i,a in enumerate(REGISTRY[kind]['actions'])]
 return {'mechanism':kind,'hook':'Engineering geometry fixture','beats':beats},{'duration':48.,'beats':beats,'motion_policy':'engineering-fixture'}

class FloatValveTests(unittest.TestCase):
 def test_rigid_arm_float_immersion_and_positive_valve_clearance(self):
  previous=None
  for level in np.linspace(tank.LOW,tank.HIGH,101):
   p=tank.physical(level)
   self.assertAlmostEqual(np.linalg.norm(np.array(p['float_center'])-tank.PIVOT),tank.ARM)
   self.assertAlmostEqual(p['float_z']-level,.18)
   self.assertGreaterEqual(p['gap'],0)
   if previous:self.assertLess(p['gap'],previous['gap'])
   # Real bearing contact between the lever roller and guided stem platform.
   contact_z=tank.PIVOT[2]+.42*math.sin(p['angle'])
   platform_bottom=p['plug_z']-tank.STEM-.0325
   self.assertAlmostEqual(platform_bottom,contact_z+.10)
   previous=p
  p=tank.physical(tank.HIGH);self.assertAlmostEqual(p['flow'],0)
  self.assertAlmostEqual(p['plug_z'],tank.SEAT-.04)
 def test_no_closed_valve_flow_or_hidden_extra_cycle(self):
  _,tl=fixture('float_valve')
  for t in np.linspace(0,47.999,400):
   p=tank.state(t,tl)
   if p['gap']<1e-8:self.assertAlmostEqual(p['flow'],0)
   if p['beat'] in (4,7):self.assertAlmostEqual(p['level'],tank.HIGH)
  self.assertLess(tank.state(35.9,tl)['level'],tank.state(30.1,tl)['level'])
 def test_wrong_way_float_motion_is_detected(self):
  _,tl=fixture('float_valve');original=tank.state
  def broken(t,tl):
   p=original(t,tl);p['float_z']=-p['float_z'];return p
  with tempfile.TemporaryDirectory() as d,patch.object(tank,'state',side_effect=broken):
   errors=action_contracts.verify_motion('float_valve',tank,tl,d)
   self.assertTrue(any('float_z' in e for e in errors))

class GatedPadlockTests(unittest.TestCase):
 def test_bar_waits_for_all_three_gates_and_pull_waits_for_bar(self):
  _,tl=fixture('combination_lock')
  for t in np.linspace(0,47.999,800):
   p=lock.state(t,tl)
   if not lock.aligned(p['angles']):self.assertAlmostEqual(p['bar_z'],lock.BAR_HIGH);self.assertEqual(p['shackle'],0)
   if p['shackle']>0:self.assertGreaterEqual(p['free'],.999)
  self.assertAlmostEqual(lock.state(35,tl)['bar_z'],lock.BAR_LOW)
  self.assertEqual(lock.state(35,tl)['shackle'],0)
  self.assertGreater(lock.state(41.9,tl)['shackle'],.89)
 def test_gate_geometry_rotates_with_wheel_instead_of_being_painted(self):
  class Mesh:
   def __init__(self):self.faces=[]
   def face(self,points,color):self.faces.append(np.array(points))
   def beam(self,*a,**k):pass
  a=Mesh();b=Mesh();angle=.8
  lock.wheel(a,0,0,(200,200,200));lock.wheel(b,0,angle,(200,200,200))
  for original,moved in zip(a.faces[:216],b.faces[:216]):
   y=moved[:,1];z=moved[:,2]-lock.WHEEL_Z
   back=moved.copy();back[:,1]=y*math.cos(angle)+z*math.sin(angle);back[:,2]=-y*math.sin(angle)+z*math.cos(angle)+lock.WHEEL_Z
   np.testing.assert_allclose(back,original,atol=1e-12)
 def test_held_explanation_never_repeats_the_release(self):
  _,tl=fixture('combination_lock')
  samples=[lock.state(t,tl) for t in np.linspace(30.01,35.99,30)]
  self.assertTrue(all(p['bar_z']==lock.BAR_LOW for p in samples))

class CausalGateTests(unittest.TestCase):
 def test_both_new_assemblies_fit_and_show_real_parts(self):
  for kind in ('float_valve','combination_lock'):
   plan,tl=fixture(kind)
   with tempfile.TemporaryDirectory() as d:
    verify_component(plan,tl,Path(d))
    self.assertEqual(json.loads(Path(d,'causal-motion-checks.json').read_text())['errors'],[])
 def test_parts_catalogue_opening_is_rejected(self):
  plan,_=fixture('float_valve')
  self.assertTrue(any('question' in e for e in storytelling.errors(plan)))
 def test_held_state_narration_mismatches_are_rejected_before_voice(self):
  for kind,index,say in [('float_valve',7,'The float rises as water starts filling the tank again.'),('combination_lock',5,'The bar drops into the gates and then releases the shackle.'),('combination_lock',7,'The shackle rises because all three gates now line up.')]:
   plan,_=fixture(kind);plan['beats'][index]['say']=say
   self.assertTrue(action_contracts.narration_errors(plan))
 def test_new_families_do_not_recycle_any_old_visual_setup(self):
  used=[{'mechanism':k,'state':'created'} for k in REGISTRY if k not in ('float_valve','combination_lock')]
  self.assertEqual(set(novelty.unused(REGISTRY,used)),{'float_valve','combination_lock'})
  self.assertTrue(novelty.reason('Why a different tank float works','float_valve',used+[{'mechanism':'float_valve','state':'skipped'}]))
 def test_targeted_model_repair_preserves_good_peer_sections(self):
  plan,_=fixture('float_valve');prior=copy.deepcopy(plan)
  answer={'sections':[{'index':0,'say':'Why does a floating ball stop this tank before water spills over?'},{'index':6,'say':'An unrequested replacement must never overwrite another accepted original section here.'}]}
  with patch('studio_lib.director.call',return_value=answer):fixed=repair_causal_sections(plan,['beat 0: open with one concrete problem or useful question ending with ?'])
  self.assertNotEqual(fixed['beats'][0]['say'],plan['beats'][0]['say'])
  self.assertEqual(fixed['beats'][1:],prior['beats'][1:]);self.assertEqual(plan,prior)
 def test_repeated_part_name_gets_unique_existing_word_cue(self):
  plan={'mechanism':'float_valve','beats':[{'action':'fill','say':'The water rises, and the water lifts the floating ball.','motion_cue':'the water'}]}
  fixed=narration_timing.normalize_cues(plan)
  self.assertEqual(fixed['beats'][0]['say'],plan['beats'][0]['say'])
  self.assertEqual(narration_timing.cue_errors(fixed),[])


class CausalEvidenceTests(unittest.TestCase):
 def test_evidence_binds_to_the_measured_timeline_and_plan(self):
  plan,tl=fixture('float_valve')
  with tempfile.TemporaryDirectory() as d:
   action_contracts.verify_motion('float_valve',tank,tl,d,plan=plan)
   report=json.loads(Path(d,'causal-motion-checks.json').read_text())
   self.assertEqual(action_contracts.evidence_errors(report,plan,tl),[])
   changed=copy.deepcopy(tl);changed['beats'][2]['end']+=.2
   self.assertTrue(action_contracts.evidence_errors(report,plan,changed))
   changed_plan=copy.deepcopy(plan);changed_plan['beats'][2]['say']='Different narration'
   self.assertTrue(action_contracts.evidence_errors(report,changed_plan,tl))
 def test_empty_pass_label_cannot_replace_physical_measurements(self):
  plan,tl=fixture('combination_lock')
  report={'errors':[],'plan_sha256':action_contracts.fingerprint(plan),'timeline_sha256':action_contracts.fingerprint(tl),'measurements':[]}
  self.assertIn('Causal motion evidence is incomplete',action_contracts.evidence_errors(report,plan,tl))
 def test_reversed_measurement_cannot_pass_an_empty_errors_list(self):
  plan,tl=fixture('float_valve')
  with tempfile.TemporaryDirectory() as d:
   action_contracts.verify_motion('float_valve',tank,tl,d,plan=plan)
   report=json.loads(Path(d,'causal-motion-checks.json').read_text())
   row=next(row for row in report['measurements'] if row.get('channel')=='level' and 'delta' in row);row['delta']=-abs(row['delta'])
   self.assertIn('Measured causal action is absent or reversed',action_contracts.evidence_errors(report,plan,tl))

class StoryWordingRegressionTests(unittest.TestCase):
 def test_active_causal_clauses_are_not_mistaken_for_a_parts_list(self):
  plan,_=fixture('float_valve')
  lines=['What stops this tank before its water spills over?',
         'Inside the tank, a low float rides on a rigid pivoted arm.',
         'Incoming water lifts the floating ball, rotating its arm around a fixed pivot.',
         'The rising arm pushes the washer toward its seat until the inlet stops flowing.',
         'The washer stays seated, so the high water level remains held.',
         'Opening the separate outlet lowers the water, releasing the washer and reopening the inlet.',
         'The outlet closes and inlet flow raises the float to shut the valve again.',
         'The tank stays full while this mechanical feedback keeps its inlet closed.']
  for b,line in zip(plan['beats'],lines):b['say']=line
  self.assertEqual(storytelling.errors(plan),[])
 def test_open_tank_is_not_given_an_unshown_burst_scenario(self):
  plan,_=fixture('float_valve');plan['beats'][0]['say']='What prevents this open tank from bursting as the water rises?'
  self.assertTrue(any('burst or explosion' in e for e in action_contracts.narration_errors(plan)))
 def test_held_beat_requires_a_held_explanation(self):
  plan,_=fixture('float_valve');plan['beats'][4]['say']='High water lifts the float, pivoting the arm to press the washer shut, sealing the inlet.'
  self.assertTrue(any('already held' in e for e in action_contracts.narration_errors(plan)))

class DraftRecoveryTests(unittest.TestCase):
 def test_rejected_draft_is_persisted_for_later_targeted_repair(self):
  import os
  from studio_lib.director import plan_topic,validate
  from studio_lib.checkpoints import Checkpoint
  plan,_=fixture('float_valve');plan.update(title='How This Tank Controls Its Level',hook='Why does the water stop?')
  original=Path.cwd()
  with tempfile.TemporaryDirectory() as d:
   try:
    os.chdir(d);out=Path('attempt');out.mkdir()
    with patch('studio_lib.director.call',return_value=plan):
     with self.assertRaisesRegex(ValueError,'director rejected'):plan_topic('An engineering draft recovery fixture',out,mechanism='float_valve')
    saved=Checkpoint('An engineering draft recovery fixture',validator=validate,namespace='tested-library-spoken-v1').load()
    self.assertEqual(saved['stage'],'needs_repair');self.assertEqual(saved['repair_kind'],'validation')
    self.assertEqual(saved['scene']['beats'][3]['say'],plan['beats'][3]['say'])
   finally:os.chdir(original)

class SemanticRepairTests(unittest.TestCase):
 def test_invalid_motion_replacement_is_rejected_without_losing_the_old_section(self):
  plan,_=fixture('float_valve');plan['beats'][4]['say']='The washer is already seated and the inlet remains closed while the water level stays high.'
  answer={'sections':[{'index':4,'say':'The float lifts and pivots the arm to seal the inlet now.'}]}
  with patch('studio_lib.director.call',return_value=answer):fixed=repair_causal_sections(plan,['beat 4: narration needs 9-23 words'])
  self.assertEqual(fixed['beats'][4]['say'],plan['beats'][4]['say'])
 def test_bad_sentence_is_not_fed_back_as_a_rewrite_example(self):
  plan,_=fixture('float_valve');plan['beats'][4]['say']='The floating disc rises and then pushes the washer closed.'
  with patch('studio_lib.director.call',return_value={'sections':[]}) as writer:repair_causal_sections(plan,['beat 4: explain the held state'])
  request=json.loads(writer.call_args.args[1])
  self.assertTrue(request['sections'][0]['state_only']);self.assertNotIn('say',request['sections'][0])

class RepairedTimingPointerTests(unittest.TestCase):
 def test_valid_spoken_repair_is_not_rejected_for_its_old_timing_pointer(self):
  from studio_lib.director import validate
  plan,_=fixture('float_valve');plan['motion_policy']=narration_timing.VERSION
  plan['beats'][7].update(say='Return to the whole tank; high water and closed inlet are already held.',motion_cue='tank; high')
  new='The tank stays full while its raised float and seated washer keep the incoming water stopped.'
  with patch('studio_lib.director.call',return_value={'sections':[{'index':7,'say':new}]}):fixed=repair_causal_sections(plan,['beat 7: do not speak visual production directions to the audience'])
  self.assertEqual(fixed['beats'][7]['say'],new)
  self.assertNotEqual(fixed['beats'][7]['motion_cue'],plan['beats'][7]['motion_cue'])
  self.assertFalse(any(e.startswith('beat 7:') for e in validate(fixed)))
 def test_level_control_is_not_presented_as_pressure_regulation(self):
  plan,_=fixture('float_valve');plan['beats'][7]['say']='The tank stays full because its float keeps pressure steady.'
  self.assertTrue(any('not regulated pressure' in e for e in action_contracts.narration_errors(plan)))

class FirstActuatorTimingTests(unittest.TestCase):
 def test_refill_tracks_the_outlet_closing_clause_before_the_water_result(self):
  plan={'mechanism':'float_valve','beats':[{'action':'refill','say':'When the draw-off valve shuts, inlet water lifts the ball and turns its rigid arm.','motion_cue':'water lifts'}]}
  fixed=narration_timing.normalize_cues(plan)
  self.assertEqual(fixed['beats'][0]['say'],plan['beats'][0]['say'])
  self.assertEqual(fixed['beats'][0]['motion_cue'],'draw-off valve shuts')
  self.assertEqual(narration_timing.cue_errors(fixed),[])

if __name__=='__main__':unittest.main()
