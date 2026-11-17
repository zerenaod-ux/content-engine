import unittest
from studio_lib.science.checks import lever_narration_errors
class LeverNarration(unittest.TestCase):
    def test_observed_contradictions_are_rejected(self):
        p={'beats':[{'action':'input','say':'A downward arrow pushes on the long left side.'},{'action':'change','say':'The two ends are swapping positions.'},{'action':'result','say':'The right-hand load lifts upward.'}]}
        self.assertEqual(len(lever_narration_errors(p)),3)
    def test_static_result_and_illustrated_force_are_valid(self):
        p={'beats':[{'action':'input','say':'The arrow illustrates the force applied by the input weight.'},{'action':'change','say':'The short arm rises as the long arm moves down.'},{'action':'result','say':'The load has risen and is now held in place.'}]}
        self.assertEqual(lever_narration_errors(p),[])
