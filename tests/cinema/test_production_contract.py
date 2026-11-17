import unittest
from studio_lib.cinema.production_contract import framing_errors,ESSENTIAL_PARTS

class ProductionContractTests(unittest.TestCase):
    def test_missing_clipped_or_behind_camera_part_cannot_pass(self):
        for points in ([],[(.2,.2,-1)],[(-.1,.5,1)],[(.5,float('nan'),1)]):
            self.assertTrue(framing_errors({'load':points},['load']))
        self.assertEqual(framing_errors({'load':[(.2,.2,1),(.8,.8,1)]},['load']),[])
    def test_lever_motion_requires_input_pivot_and_output_context(self):
        self.assertIn('fixed_pivot_pin',ESSENTIAL_PARTS['lever_balance']['change'])
        self.assertIn('load_crate',ESSENTIAL_PARTS['lever_balance']['change'])
        self.assertIn('input_weight',ESSENTIAL_PARTS['lever_balance']['input'])
