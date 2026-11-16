"""Physics/event invariants for newly supported mechanisms, no model calls."""
import tempfile,unittest
from pathlib import Path
import numpy as np
from studio_lib.registry import REGISTRY
from studio_lib.director import validate,verify,picture
from studio_lib import solar,pump
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
    def test_new_components_expose_required_visual_evidence(self):
        for kind in ('photovoltaic_cell','piston_pump'):
            with tempfile.TemporaryDirectory() as d:verify(fixture(kind),timeline(kind),Path(d))
if __name__=='__main__':unittest.main()
