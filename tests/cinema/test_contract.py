"""Captions retain measured boundaries; punctuation and timing remain inspectable."""
import tempfile,unittest
from pathlib import Path
from studio_lib.cinema.build import captions,groups,ass_time
class CaptionTests(unittest.TestCase):
    def test_groups_keep_real_word_offsets(self):
        w=[dict(text=str(i),start=i*.4,end=i*.4+.3) for i in range(7)]
        parts=groups(w);self.assertEqual(list(map(len,parts)),[3,3,1]);self.assertAlmostEqual(parts[1][0]['start'],1.2)
    def test_ass_uses_metadata_and_escapes_control_text(self):
        with tempfile.TemporaryDirectory() as d:
            p=captions({'words':[{'text':'{Danger}','start':1.25,'end':1.55}]},Path(d));s=p.read_text()
            self.assertIn('0:00:01.25,0:00:01.62',s);self.assertNotIn('{Danger}',s)
    def test_caption_clock_rolls_minutes(self):
        self.assertEqual(ass_time(61.23),'0:01:01.23')
if __name__=='__main__':unittest.main()
