import asyncio,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.audio import _cpu_narrate,duration_speed_scale
from studio_lib.voice_policy import VOICE,PROVIDER,VERSION
class MeasuredPacingTests(unittest.TestCase):
 def test_natural_speed_feedback_has_hard_bounds(self):
  self.assertIsNone(duration_speed_scale(50,(40,70)))
  self.assertLess(duration_speed_scale(39,(40,70)),1)
  self.assertGreater(duration_speed_scale(72,(40,70)),1)
  with self.assertRaises(ValueError):duration_speed_scale(20,(40,70))
 def test_short_audio_reuses_words_and_speaker_instead_of_inserting_dead_time(self):
  spec={'beats':[{'say':'An immutable authored speech fixture for timing only.','action':'fill','seconds':3.5} for _ in range(8)]};requests=[]
  with tempfile.TemporaryDirectory() as d:
   def render(command,**kw):
    request=json.loads(Path(command[command.index('--spec')+1]).read_text());requests.append(request)
    report={'provider':PROVIDER,'voice':VOICE,'voice_policy':VERSION,'cached_lines':0,'lines':[{'voice':'fixture.wav','speaker':VOICE,'delivery':{'pause_after':.18}} for _ in request['beats']]}
    Path(command[command.index('--report')+1]).write_text(json.dumps(report))
   def probe(*a,**kw):return str(4.7/requests[-1]['delivery_speed_scale']).encode()
   with patch('studio_lib.audio.subprocess.run',side_effect=render),patch('studio_lib.audio.subprocess.check_output',side_effect=probe):
    result=asyncio.run(_cpu_narrate(spec,d,d))
  self.assertEqual(len(requests),2);self.assertEqual(result['voice'],VOICE)
  self.assertTrue(40<=result['duration']<=70)
  self.assertEqual([r['beats'] for r in requests],[spec['beats'],spec['beats']])
  self.assertTrue(all(b['end']-b['start']-b['voice_duration']<.4 for b in result['beats']))
