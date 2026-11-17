"""Physics/event invariants for newly supported mechanisms, no model calls."""
import tempfile,unittest
from pathlib import Path
import numpy as np
from studio_lib.registry import REGISTRY
from studio_lib.director import validate,verify,picture
from studio_lib import solar,pump,wind
def fixture(kind):
    return {'mechanism':kind,'title':'How This Tested Mechanism Transfers Useful Energy','hook':'Look inside the moving mechanism','beats':[{'action':a,'say':'This authored engineering fixture checks visible component behavior rather than proving automatically generated narration quality.','camera':'mechanism' if i in (2,3,4,5) else 'wide'} for i,a in enumerate(REGISTRY[kind]['actions'])]}
def timeline(kind):return {'beats':[dict(b,start=i*6,end=(i+1)*6) for i,b in enumerate(fixture(kind)['beats'])],'duration':48}
class LibraryTests(unittest.TestCase):
    def test_all_registered_plans_validate(self):
        for kind in REGISTRY:self.assertEqual(validate(fixture(kind)),[])
    def test_solar_load_requires_closed_circuit_stage(self):
        tl=timeline('photovoltaic_cell');self.assertFalse(solar.pose(29.9,tl)['powered']);self.assertTrue(solar.pose(30,tl)['powered'])
    def test_pump_valves_never_both_open(self):
        tl=timeline('piston_pump')
        for t in np.linspace(0,47.99,300):
            p=pump.phase(t,tl);self.assertFalse(p['intake'] and p['delivery'])
    def test_pump_volume_increases_on_intake_and_decreases_on_delivery(self):
        tl=timeline('piston_pump');intake=[pump.phase(t,tl)['chamber_length'] for t in np.linspace(12,23.99,80)];delivery=[pump.phase(t,tl)['chamber_length'] for t in np.linspace(24.01,35.99,80)]
        self.assertTrue(all(b>=a for a,b in zip(intake,intake[1:])));self.assertTrue(all(b<=a for a,b in zip(delivery,delivery[1:])))
    def test_pump_reservoirs_follow_strokes_and_preserve_normalized_volume(self):
        tl=timeline('piston_pump')
        for t in np.linspace(0,47.99,300):
            p=pump.phase(t,tl);self.assertAlmostEqual(p['source_level']+p['receiver_level']+.23*p['chamber_fill'],1.55)
            if p['intake']:
                later=pump.phase(t+.001,tl);self.assertAlmostEqual(p['receiver_level'],later['receiver_level'],places=5)
        self.assertGreater(pump.phase(47,tl)['receiver_level'],pump.phase(0,tl)['receiver_level'])
    def test_solar_cannot_claim_visible_wires_are_absent(self):
        s=fixture('photovoltaic_cell');s['beats'][1]['say']='Yellow arrows approach the solar cells without any wiring shown beside this illuminated panel.'
        self.assertTrue(any('wires are visible' in e for e in validate(s)))
    def test_new_components_expose_required_visual_evidence(self):
        for kind in ('photovoltaic_cell','piston_pump','wind_turbine'):
            with tempfile.TemporaryDirectory() as d:verify(fixture(kind),timeline(kind),Path(d))
    def test_direct_drive_stays_coupled_and_load_waits_for_switch(self):
        tl=timeline('wind_turbine')
        for t in np.linspace(0,47.99,200):
            p=wind.pose(t,tl)
            self.assertEqual(p['angle'],p['shaft_angle']);self.assertEqual(p['angle'],p['magnet_angle'])
            self.assertEqual(p['closed'],t>=36)
        # Coils stay fixed in draw(); differing rotor angles must produce visible motion.
        plan=fixture('wind_turbine')
        a=np.asarray(picture(27,tl,plan)).astype(int);b=np.asarray(picture(27.7,tl,plan)).astype(int)
        self.assertGreater(np.count_nonzero(np.max(abs(a-b),axis=2)>22),100)
if __name__=='__main__':unittest.main()
