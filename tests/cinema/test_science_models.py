import unittest
from studio_lib.science.models import lever,resistor,hydraulics,heat_contact,complementary_dna,transfer_water
class ScienceModelTests(unittest.TestCase):
    def test_mechanisms_torque_balance(self):
        x=lever(10,2,.5)
        self.assertEqual(x['output_force']*.5,x['input_torque'])
    def test_electricity_open_circuit_has_no_power(self):
        self.assertEqual(resistor(12,6)['load_power'],24)
        self.assertEqual(resistor(12,6,False)['load_power'],0)
        with self.assertRaises(ValueError):resistor(12,0)
    def test_hydraulics_conserves_work_and_volume(self):
        for area in (.1,1,10):
            x=hydraulics(20,1,area,2)
            self.assertAlmostEqual(x['output_force']*x['output_distance'],40)
            self.assertAlmostEqual(area*x['output_distance'],2)
    def test_heat_conserves_energy_and_never_crosses_equilibrium(self):
        for progress in (0,.3,1):
            x=heat_contact(90,10,2,3,progress)
            self.assertAlmostEqual(x['temp_a']*2+x['temp_b']*3,210)
            self.assertGreaterEqual(x['temp_a']+1e-10,x['temp_b'])
        with self.assertRaises(ValueError):heat_contact(90,10,2,3,2)
    def test_biology_complement_is_antiparallel_and_reversible(self):
        x=complementary_dna('aTcG')
        self.assertEqual(x['aligned_complement'],'TAGC')
        self.assertEqual(complementary_dna(x['aligned_complement'])['aligned_complement'],'ATCG')
        self.assertNotEqual(x['template_direction'],x['aligned_complement_direction'])
        with self.assertRaises(ValueError):complementary_dna('AUG')
    def test_earth_model_never_creates_water_or_negative_stores(self):
        x=transfer_water(2,3,100)
        self.assertEqual(x['source_volume'],0)
        self.assertEqual(x['destination_volume'],5)
        with self.assertRaises(ValueError):transfer_water(-1,3,2)
    def test_invalid_nonfinite_values_fail(self):
        with self.assertRaises(ValueError):lever(float('nan'),1,2)
        with self.assertRaises(ValueError):hydraulics(10,True,2,1)
