"""Captions retain measured boundaries; punctuation and timing remain inspectable."""
import tempfile,unittest
from pathlib import Path
from studio_lib.cinema.build import captions,groups,ass_time,scene_errors,contract
from studio_lib.cinema.review import word_error
class CaptionTests(unittest.TestCase):
    def test_groups_keep_real_word_offsets(self):
        w=[dict(text=str(i),start=i*.4,end=i*.4+.3) for i in range(7)]
        parts=groups(w);self.assertEqual(list(map(len,parts)),[3,3,1]);self.assertAlmostEqual(parts[1][0]['start'],1.2)
    def test_ass_uses_metadata_and_escapes_control_text(self):
        with tempfile.TemporaryDirectory() as d:
            p=captions({'words':[{'text':'{Danger}','start':1.25,'end':1.55}]},Path(d));s=p.read_text()
            self.assertIn('0:00:01.25,0:00:01.59',s);self.assertNotIn('{Danger}',s)
    def test_caption_clock_rolls_minutes(self):
        self.assertEqual(ass_time(61.23),'0:01:01.23')
    def test_actual_scene_contract_rejects_observed_narration_mismatches(self):
        p={'beats':[{'action':'rotor','say':'Each blade twists in its pitch bearing.'},{'action':'induction','say':'The coil glows as voltage spikes.'}]}
        self.assertGreaterEqual(len(scene_errors(p)),2)
        self.assertIn('NO blade pitch',contract()['facts']['rotor'])
    def test_open_circuit_cannot_be_described_as_producing_current(self):
        p={'beats':[{'action':'generator','say':'The rotating magnets produce alternating current through the copper coils.'}]}
        self.assertTrue(any('open circuit' in x for x in scene_errors(p)))
    def test_caption_overlap_and_cross_beat_groups_are_prevented(self):
        words=[{'text':'First.','start':0,'end':.40,'beat':0},{'text':'Next','start':.41,'end':.6,'beat':1},{'text':'line','start':.61,'end':.9,'beat':1}]
        with tempfile.TemporaryDirectory() as d:
            captions({'words':words},Path(d))
            import json
            rows=json.loads((Path(d)/'caption-checks.json').read_text())['intervals']
            self.assertEqual(len(rows),2);self.assertLess(rows[0]['end'],rows[1]['start'])
            self.assertEqual(rows[0]['text'],'First.')
    def test_transcription_review_detects_missing_speech(self):
        self.assertEqual(word_error('Turn the handle.','Turn the handle'),0)
        self.assertGreater(word_error('Turn the handle and close the switch.','Turn'),.5)
    def test_new_family_contract_has_no_turbine_actions(self):
        c=contract('How a hand-cranked generator powers a lamp')
        self.assertEqual(c['actions'][0],'machine');self.assertIn('OPEN',c['facts']['induction'])
if __name__=='__main__':unittest.main()
