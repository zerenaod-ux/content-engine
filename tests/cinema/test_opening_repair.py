import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.cinema.build import repair_opening,contract,script_errors
class OpeningRepairTests(unittest.TestCase):
    def test_targeted_question_comes_from_model_and_preserves_other_beats(self):
        plan={'beats':[{'say':'The cylinders are connected by a sealed fluid path.'},{'say':'Second beat unchanged.'}]}
        question='How does a small piston help raise a much heavier load?'
        with tempfile.TemporaryDirectory() as d,patch('studio_lib.cinema.build.call',return_value={'question':question}) as model:
            result=repair_opening(plan,'How a hydraulic lift works',contract('How a hydraulic lift works'),Path(d),0)
            self.assertEqual(result['beats'][0]['say'],question)
            self.assertEqual(result['beats'][1],plan['beats'][1])
            self.assertNotEqual(result,plan)
            self.assertTrue((Path(d)/'opening-repair-0.json').exists())
            model.assert_called_once()
    def test_invalid_question_never_becomes_a_local_authored_fix(self):
        plan={'beats':[{'say':'A descriptive opening sentence that needs to become a question.'}]}
        with tempfile.TemporaryDirectory() as d,patch('studio_lib.cinema.build.call',return_value={'question':'The lift moves.'}):
            self.assertEqual(repair_opening(plan,'How a hydraulic lift works',contract('How a hydraulic lift works'),Path(d),0),plan)
