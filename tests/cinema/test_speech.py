import asyncio,json,tempfile,unittest,copy
from pathlib import Path
from unittest.mock import patch,AsyncMock
from studio_lib.cinema.speech import cache_key,delivery,VOICE
from studio_lib.cinema.build import voice
from studio_lib.voice_policy import VERSION,PROVIDER

class SpeechTests(unittest.TestCase):
 def test_expression_changes_by_story_role_and_cache_tracks_controls(self):
  first=delivery('machine',0,8);last=delivery('payoff',7,8)
  self.assertNotEqual(first['tone'],last['tone'])
  for field in ('pitch','volume','rate','policy','pause_after'):
   altered=dict(first);altered[field]=str(first[field])+'changed'
   self.assertNotEqual(cache_key('Same words',first),cache_key('Same words',altered))
  self.assertEqual(VOICE,'am_fenrir')
 def test_all_formats_use_fixed_narrator_and_actual_word_times(self):
  plan={'mechanism':'hand_generator','beats':[{'action':'machine','say':'Why does this move?'}]}
  timeline={'voice':VOICE,'voice_provider':PROVIDER,'voice_policy':VERSION,'cached_lines':1,'duration':41,'beats':[{'start':0,'end':41,'voice_duration':40,'voice':'fixture.wav','action':'machine'}]}
  with tempfile.TemporaryDirectory() as d,patch('studio_lib.audio.narrate',new_callable=AsyncMock,return_value=timeline) as narrate,patch('studio_lib.word_timing.measured_words',return_value=[{'text':'Why','start':.1,'end':.3}]):
   result=asyncio.run(voice(plan,Path(d),duration_range=(120,300)))
   self.assertEqual(result['voice'],VOICE)
   self.assertAlmostEqual(result['words'][0]['start'],.16)
   self.assertAlmostEqual(result['words'][0]['end'],.36)
   self.assertEqual(narrate.call_args.kwargs['duration_range'],(120,300))
 def test_missing_word_evidence_holds_instead_of_guessing(self):
  timeline={'duration':41,'beats':[{'start':0,'end':41,'voice_duration':40,'voice':'fixture.wav'}]}
  with tempfile.TemporaryDirectory() as d,patch('studio_lib.audio.narrate',new_callable=AsyncMock,return_value=timeline),patch('studio_lib.word_timing.measured_words',return_value=[]):
   with self.assertRaisesRegex(ValueError,'No measured'):asyncio.run(voice({'mechanism':'hand_generator','beats':[{'action':'machine','say':'Fixture only'}]},Path(d)))
 def test_failed_voice_does_not_fall_back_to_another_speaker(self):
  with tempfile.TemporaryDirectory() as d,patch('studio_lib.audio.narrate',new_callable=AsyncMock,side_effect=TimeoutError('service failure')):
   with self.assertRaises(TimeoutError):asyncio.run(voice({'mechanism':'hand_generator','beats':[]},Path(d)))
