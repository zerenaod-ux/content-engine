import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.longform.contract import ACTIONS
from studio_lib.longform.repair import repair_sections,unsupported_comparison
class SectionRepairTests(unittest.TestCase):
 def test_two_invalid_sections_are_model_repaired_without_changing_valid_chapters(self):
  p={'mechanism':'rack_pinion','topic':'How a rack and pinion moves a carriage','title':'How a Pinion Moves a Carriage','hook':'Turns become travel','beats':[{'action':a,'say':' '.join(['word']*33),'camera':'wide'} for a in ACTIONS]}
  p['beats'][11]['say']=' '.join(['short']*29);p['beats'][13]['say']=' '.join(['short']*28);original=copy.deepcopy(p)
  answer={'replacements':[{'index':i,'say':' '.join(['repaired']*35)} for i in (11,13)]}
  with tempfile.TemporaryDirectory() as d,patch('studio_lib.longform.repair.call',return_value=answer) as model:r=repair_sections(p,Path(d))
  model.assert_called_once();self.assertEqual(p,original)
  for i in range(16):
   if i not in (11,13):self.assertEqual(r['beats'][i],original['beats'][i])
  self.assertEqual(r['topic'],original['topic']);self.assertEqual(r['title'],original['title'])
 def test_unrequested_rewrite_is_rejected(self):
  p={'mechanism':'rack_pinion','beats':[{'action':a,'say':' '.join(['word']*(29 if i==11 else 33)),'camera':'wide'} for i,a in enumerate(ACTIONS)]}
  with tempfile.TemporaryDirectory() as d,patch('studio_lib.longform.repair.call',return_value={'replacements':[{'index':0,'say':' '.join(['wrong']*35)}]}):self.assertEqual(repair_sections(p,Path(d)),p)
 def test_unshown_geometry_comparison_is_not_a_supported_topic(self):
  self.assertTrue(unsupported_comparison('Why does travel change when pinion diameter is increased?','rack_pinion'))
  self.assertFalse(unsupported_comparison('How a rack and pinion moves a carriage','rack_pinion'))
 def test_title_repair_never_rewrites_valid_narration_or_hook(self):
  from studio_lib.longform.repair import repair_metadata
  plan={'topic':'How a lead screw moves a carriage','title':'How a Very Long Screw Title Contains Far Too Many Words','hook':'Turns become travel','beats':[{'say':'Existing valid words'}]}
  with tempfile.TemporaryDirectory() as d,patch('studio_lib.longform.repair.call',return_value={'title':'How Lead Screws Move a Carriage','hook':'Do not replace this'}):r=repair_metadata(plan,Path(d))
  self.assertEqual(r['beats'],plan['beats']);self.assertEqual(r['hook'],plan['hook']);self.assertEqual(r['title'],'How Lead Screws Move a Carriage')
