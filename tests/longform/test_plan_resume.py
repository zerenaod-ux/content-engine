import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.longform.contract import ACTIONS
from studio_lib.longform import build

def fixture():
 return {'mechanism':'rack_pinion','topic':'How a rack and pinion moves a carriage','title':'How a Rack Moves a Carriage','hook':'Turns become travel','beats':[{'action':a,'say':' '.join(['word']*30)+('?' if i==0 else '.'),'camera':'wide'} for i,a in enumerate(ACTIONS)]}

class PlanResumeTests(unittest.TestCase):
 def test_accepted_plan_is_the_repair_seed_not_an_unrelated_older_draft(self):
  original=fixture();original['beats'][10]['say']='That work becomes the kinetic energy '+' '.join(['word']*25)
  corrected=copy.deepcopy(original);corrected['beats'][10]['say']=' '.join(['corrected']*35)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'accepted-plan.json').write_text(json.dumps(original))
   draft=fixture();draft['beats'][2]['say']=' '.join(['wrongdraft']*30);(root/'draft-plan.json').write_text(json.dumps(draft))
   with patch.object(build,'select',return_value={'topic':original['topic'],'mechanism':'rack_pinion'}),patch.object(build,'repair_metadata',side_effect=lambda p,*a:p),patch.object(build,'repair_sections',return_value=corrected) as repair,patch.object(build,'call',return_value={'errors':[]}) as model:
    result=build.plan(root)
   self.assertEqual(repair.call_args.args[0],original);self.assertEqual(result,corrected)
   model.assert_called_once();self.assertIn('Audit',model.call_args.args[0])
   for i in range(16):
    if i!=10:self.assertEqual(result['beats'][i],original['beats'][i])
 def test_valid_saved_draft_is_audited_without_regenerating_it(self):
  p=fixture()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'draft-plan.json').write_text(json.dumps(p))
   with patch.object(build,'select',return_value={'topic':p['topic'],'mechanism':'rack_pinion'}),patch.object(build,'call',return_value={'errors':[]}) as model:result=build.plan(root)
   self.assertEqual(result,p);model.assert_called_once();self.assertIn('Audit',model.call_args.args[0])
