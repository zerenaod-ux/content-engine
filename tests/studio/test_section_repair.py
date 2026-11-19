import unittest
from unittest.mock import patch
from studio_lib.director import repair_short_sections,repair_causal_sections
class SectionRepairTests(unittest.TestCase):
 def test_only_requested_section_changes(self):
  plan={'mechanism':'piston_pump','beats':[{'action':'pump','say':'Valid original section stays exactly the same through targeted model repair.'},{'action':'inlet','say':'Too short.'}]}
  answer={'sections':[{'index':1,'say':'The inlet valve opens during intake while the outlet valve remains closed.'},{'index':0,'say':'An unwanted replacement must never overwrite the accepted original section.'}]}
  with patch('studio_lib.director.call',return_value=answer):
   result=repair_short_sections(plan,['beat 1: narration needs 9-23 words'])
  self.assertEqual(result['beats'][0],plan['beats'][0]);self.assertNotEqual(result['beats'][1],plan['beats'][1])
  self.assertEqual(plan['beats'][1]['say'],'Too short.')
 def test_nonlength_errors_keep_full_validation_route(self):
  with patch('studio_lib.director.call') as call:
   self.assertIsNone(repair_short_sections({},['unsupported mechanism']));call.assert_not_called()

 def test_total_length_repair_keeps_a_valid_brief_opening(self):
  from studio_lib.registry import REGISTRY
  plan={'mechanism':'electric_relay','beats':[{'action':a,'say':' '.join(['fixture']*(10 if i<2 else 16))} for i,a in enumerate(REGISTRY['electric_relay']['actions'])]}
  with patch('studio_lib.director.call',return_value={'sections':[]}) as writer:
   repaired=repair_causal_sections(plan,['total narration needs 140-176 words'])
  import json
  request=json.loads(writer.call_args.args[1]);sections=request['sections']
  self.assertTrue(sections);self.assertTrue(all(s['index']>=2 and s['target_words']==22 for s in sections))
  self.assertEqual(repaired['beats'][:2],plan['beats'][:2])
 def test_explicit_opening_repair_targets_a_short_question(self):
  from studio_lib.registry import REGISTRY
  plan={'mechanism':'electric_relay','beats':[{'action':a,'say':' '.join(['fixture']*18)} for a in REGISTRY['electric_relay']['actions']]}
  with patch('studio_lib.director.call',return_value={'sections':[]}) as writer:repair_causal_sections(plan,['beat 0: open with a concrete question'])
  import json
  self.assertEqual(json.loads(writer.call_args.args[1])['sections'][0]['target_words'],12)
