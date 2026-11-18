import json,tempfile,unittest
from pathlib import Path
from studio_lib.cinema.overlays import events,hook_errors
from studio_lib.cinema.build import captions
class OverlayTests(unittest.TestCase):
    def test_hook_first_and_disclosure_does_not_compete(self):
        tl={'hook':'Can a small push lift this?','diagram':True,'mechanism':'lever_balance','duration':40,'beats':[{'action':'overview','start':0,'end':4},{'action':'parts','start':4,'end':8}],'words':[{'text':'Narrated','start':.2,'end':.7,'beat':0}]}
        rows=events(tl);self.assertEqual(rows[0]['role'],'hook');self.assertEqual(rows[1]['text'],'Illustration');self.assertGreaterEqual(rows[1]['start'],rows[0]['end'])
        with tempfile.TemporaryDirectory() as d:
            text=captions(tl,Path(d),subtitles=False).read_text()
            self.assertIn('Can a small push lift this?',text);self.assertNotIn('Narrated',text)
            self.assertNotIn('Scale and progress',text)
            self.assertFalse(json.loads((Path(d)/'presentation-checks.json').read_text())['speech_captions_burned_in'])
    def test_long_or_jargon_hooks_are_rejected(self):
        self.assertTrue(hook_errors('Simplified schematic scale and progress illustrative'))
        self.assertTrue(hook_errors('This hook has far too many words for an opening'))
        self.assertFalse(hook_errors('Small push. Big lift?'))
