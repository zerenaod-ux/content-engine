import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.cinema.build import load_or_generate
class ResumePlanTests(unittest.TestCase):
    def test_accepted_stage_reused_without_model(self):
        topic='How a hydraulic lift works'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);saved=root/'saved';saved.mkdir();out=root/'out';out.mkdir()
            plan={'mechanism':'hydraulic_lift','beats':[]}
            for name,data in [('plan',plan),('topic-brief',{'topic':topic}),('narration-critique',{'errors':[]})]:(saved/(name+'.json')).write_text(json.dumps(data))
            with patch.dict(os.environ,{'CE_CINEMA_RESUME_DIR':str(saved)}),patch('studio_lib.cinema.build.repair_resumed_plan',side_effect=lambda plan,topic,out:(plan,{'errors':[]},0)),patch('studio_lib.cinema.build.generate') as writer:
                self.assertEqual(load_or_generate(topic,out),plan);writer.assert_not_called()
            self.assertTrue((out/'resume-evidence.json').exists())
            with patch.dict(os.environ,{'CE_CINEMA_RESUME_DIR':str(saved)}),patch('studio_lib.cinema.build.script_errors',return_value=[]):
                with self.assertRaises(ValueError):load_or_generate('How a lever works',out)
