import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.cinema.coverage import FAMILIES,topic_brief,require_component
from studio_lib.cinema.build import generate
class CoverageTests(unittest.TestCase):
    def test_six_families_accept_varied_topics_without_claiming_renderer(self):
        for family,item in FAMILIES.items():
            self.assertTrue(item['sources'])
            for topic in item['examples']:
                brief=topic_brief('How '+topic+' works')
                self.assertIn(family,brief['families'],topic)
                self.assertFalse(brief['sources_verified_for_this_topic'])
                self.assertFalse(brief['automatic_quality_approved'])
                if topic!='hand-cranked generator':
                    self.assertEqual(brief['render_status'],'research_and_component_work_required')

    def test_known_components_only_and_cross_topic_ambiguity_rejected(self):
        self.assertEqual(require_component('How a hand-cranked generator makes light'),'hand_generator')
        self.assertEqual(require_component('How a wind turbine generates electricity'),'wind_turbine')
        for topic in ('How a steam turbine works','How a hand-cranked pump works','Compare a wind turbine versus a hand-cranked generator','How a generator works','How a wind turbine charges a battery'):
            with self.assertRaises(ValueError):require_component(topic)

    def test_unsupported_topic_stops_before_model_and_saves_useful_brief(self):
        with tempfile.TemporaryDirectory() as d,patch('studio_lib.cinema.build.call') as model:
            with self.assertRaises(ValueError):generate('How DNA replication works',Path(d))
            model.assert_not_called()
            brief=json.loads((Path(d)/'topic-brief.json').read_text())
            self.assertIn('biology',brief['families'])
            self.assertTrue(brief['research_requirements'])
            self.assertIsNone(brief['mechanism'])

    def test_unknown_topic_and_invalid_input_never_invent_support(self):
        self.assertEqual(topic_brief('How a new unknown object works')['families'],['unclassified'])
        for invalid in (None,'',42,'a'*301):
            with self.assertRaises(ValueError):topic_brief(invalid)
