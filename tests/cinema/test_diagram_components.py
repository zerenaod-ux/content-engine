import math,tempfile,unittest
from pathlib import Path
from studio_lib.science.components import SPECS,ACTIONS,diagram
from studio_lib.cinema.coverage import require_component,topic_brief
from studio_lib.cinema.build import contract,script_errors,captions
TOPICS={'lever_balance':'How a lever raises a load','resistive_circuit':'How a resistor circuit works','hydraulic_lift':'How a hydraulic lift raises a load','thermal_contact':'How thermal contact moves heat','dna_pairing':'How DNA base pairing works','water_transfer':'How water between reservoirs changes storage'}
class DiagramTests(unittest.TestCase):
    def test_all_six_route_to_exact_contract(self):
        for mechanism,topic in TOPICS.items():
            self.assertEqual(require_component(topic),mechanism)
            self.assertEqual(contract(topic)['actions'],ACTIONS)
            self.assertEqual(topic_brief(topic)['render_status'],'implemented_diagram_unverified')
            self.assertTrue(script_errors({'mechanism':'wind_turbine','beats':[]},topic))

    def test_components_persist_with_bounded_finite_geometry(self):
        for mechanism in SPECS:
            first=diagram(mechanism,0)
            for p in (0,.1,.25,.5,.75,.99,1):
                d=diagram(mechanism,p)
                self.assertEqual([o['id'] for o in d['objects']],[o['id'] for o in first['objects']])
                self.assertEqual(len(d['labels']),len(first['labels']))
                for o in d['objects']:
                    points=o['points'] if o['kind'] in ('line','beam') else [o['at']]
                    self.assertTrue(all(math.isfinite(x) and abs(x)<10 for v in points for x in v))
                    if o['kind']=='box':self.assertTrue(all(x>0 for x in o['size']))
            self.assertTrue(d['disclosure'])

    def test_encoded_caption_recipe_discloses_simplification(self):
        with tempfile.TemporaryDirectory() as d:
            text=captions({'mechanism':'dna_pairing','diagram':True,'duration':40,'beats':[{'action':'payoff','start':30,'end':40}],'words':[]},Path(d)).read_text()
            self.assertIn('Illustration',text)
            self.assertNotIn('Scale and progress illustrative',text)
            self.assertNotIn('Circuit markers',text)

    def test_no_full_process_substitution(self):
        for topic in ('How DNA replication works','How a nuclear reactor works','How a heat exchanger works','How a hydraulic brake works','How the water cycle works'):
            with self.assertRaises(ValueError):require_component(topic)

class RichLeverTests(unittest.TestCase):
    def test_input_moves_before_lift_and_load_stays_rigidly_attached(self):
        def named(d,name):return next(x for x in d['objects'] if x['id']==name)
        start=diagram('lever_balance',0,2,0)
        pressed=diagram('lever_balance',0,2,1)
        self.assertEqual(named(start,'rigid_bar')['points'],named(pressed,'rigid_bar')['points'])
        self.assertLess(named(pressed,'input_weight')['at'][2],named(start,'input_weight')['at'][2])
        for p in (0,.3,.8,1):
            d=diagram('lever_balance',p,3,1);a=.45*p
            crate=named(d,'load_crate');self.assertAlmostEqual(crate['rotation_y'],-a)
            self.assertAlmostEqual(crate['at'][0],math.cos(a)-.57*math.sin(a))
            self.assertAlmostEqual(crate['at'][2],2+math.sin(a)+.57*math.cos(a))
            self.assertEqual(named(d,'fixed_pivot_pin')['points'],named(start,'fixed_pivot_pin')['points'])
