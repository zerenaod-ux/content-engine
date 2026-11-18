import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.cinema.length_repair import repair_length
class LengthRepairTests(unittest.TestCase):
 def test_total_length_repair_preserves_unselected_valid_beats(self):
  beats=[{'action':str(i),'say':' '.join(['word']*n),'camera':'wide'} for i,n in enumerate([12,13,14,15,18,20,21,22])]
  plan={'title':'Why This Works','hook':'Small input, big result','beats':beats}
  # Total 135; the shortest four sections provide enough extra room for 154.
  def model(*args,**kwargs):
   import json
   rows=json.loads(args[1].split('REQUESTED: ')[1]);return {'replacements':[{'index':r['index'],'say':' '.join(['repaired']*21)} for r in rows]}
  with tempfile.TemporaryDirectory() as d,patch('studio_lib.cinema.length_repair.call',side_effect=model):fixed=repair_length(plan,{'facts':{}},Path(d),0)
  self.assertGreaterEqual(sum(len(b['say'].split()) for b in fixed['beats']),140)
  self.assertEqual(fixed['beats'][7],plan['beats'][7]);self.assertEqual(fixed['title'],plan['title'])
