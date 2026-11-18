import unittest
from unittest.mock import patch
from studio_lib.director import repair_short_sections
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
