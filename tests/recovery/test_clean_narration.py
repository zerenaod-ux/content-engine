import tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
import numpy as np
from studio_lib import audio
from studio_lib.cinema import build,speech

class CleanNarrationTests(unittest.TestCase):
 def test_normal_delivery_is_not_rushed_and_identity_is_fixed(self):
  from studio_lib.voice_policy import VOICE,VERSION
  self.assertEqual(VOICE,'am_fenrir');self.assertIn('clean',VERSION)
  for i,a in enumerate(('question','cutaway','load','explain','payoff')):
   rate=float(speech.delivery(a,i,5)['rate'].strip('%'));self.assertLessEqual(rate,6)
 def test_silent_source_does_not_gain_music_or_clicks(self):
  with tempfile.TemporaryDirectory() as d:
   tl={'duration':2,'beats':[{'start':0,'end':2,'voice':'fixture.wav','action':'load'}]}
   with patch.object(audio.subprocess,'check_output',return_value=np.zeros(24000,dtype=np.float32).tobytes()),patch.object(audio.subprocess,'run'):
    audio.assemble({},tl,Path(d))
   with wave.open(str(Path(d)/'mix.wav'),'rb') as w:self.assertFalse(np.frombuffer(w.readframes(w.getnframes()),np.int16).any())
   with patch.object(build.subprocess,'check_output',return_value=np.zeros(24000,dtype=np.float32).tobytes()):build.soundtrack(tl,Path(d))
   with wave.open(str(Path(d)/'mix.wav'),'rb') as w:self.assertFalse(np.frombuffer(w.readframes(w.getnframes()),np.int16).any())
