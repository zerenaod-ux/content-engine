import asyncio,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.cinema.speech import cache_key,delivery,VOICE
from studio_lib.cinema.build import voice

class SpeechTests(unittest.TestCase):
    def test_expression_changes_by_story_role_and_cache_tracks_all_controls(self):
        first=delivery('machine',0,8);last=delivery('payoff',7,8)
        self.assertNotEqual(first['tone'],last['tone'])
        for field in ('pitch','volume','rate','policy','pause_after'):
            altered=dict(first);altered[field]=str(first[field])+'changed'
            self.assertNotEqual(cache_key('Same words',first),cache_key('Same words',altered))
        self.assertEqual(VOICE,'en-US-AndrewNeural')

    def test_synthesis_receives_profile_and_timestamps_follow_measured_speech(self):
        calls=[]
        class FakeTTS:
            def __init__(self,text,voice,**kw):calls.append((text,voice,kw))
            async def save(self,a,m):
                Path(a).write_bytes(b'0'*2000)
                Path(m).write_text(json.dumps({'type':'WordBoundary','text':'Why','offset':1000000,'duration':2000000})+'\n')
        with tempfile.TemporaryDirectory() as d:
            # All service/media calls are mocked: no audio or video is generated.
            with patch('studio_lib.cinema.build.Path',side_effect=lambda x:Path(d)/x if x=='.ce-cache/cinema-voice' else Path(x)),patch('studio_lib.cinema.build.edge_tts.Communicate',FakeTTS),patch('studio_lib.cinema.build.subprocess.check_output',return_value=b'5.0'):
                plan={'mechanism':'hand_generator','beats':[{'action':a,'say':f'Why does {a} move?'} for a in ('machine','input','crank','shaft','generator','induction','load','payoff')]}
                tl=asyncio.run(voice(plan,Path(d)))
                again=asyncio.run(voice(plan,Path(d)))
        self.assertEqual(len(calls),8)
        self.assertEqual(again['requests'],0)
        self.assertEqual(again['cached_lines'],8)
        for i,b in enumerate(tl['beats']):
            profile=b['delivery']
            self.assertEqual(calls[i][2]['pitch'],profile['pitch'])
            self.assertEqual(calls[i][2]['volume'],profile['volume'])
            self.assertAlmostEqual(tl['words'][i]['start'],b['start']+.16)
            self.assertGreaterEqual(b['end']-b['start'],b['voice_duration']+.06)

    def test_empty_service_response_retries_and_preserves_successful_cached_lines(self):
        calls=[]
        class FlakyTTS:
            def __init__(self,text,voice,**kw):self.text=text
            async def save(self,a,m):
                calls.append(self.text)
                if len(calls)==1:
                    Path(a).write_bytes(b'partial')
                    raise __import__('edge_tts').exceptions.NoAudioReceived('outage')
                Path(a).write_bytes(b'0'*2000)
                Path(m).write_text(json.dumps({'type':'WordBoundary','text':'Why','offset':1000000,'duration':2000000})+'\n')
        with tempfile.TemporaryDirectory() as d:
            with patch('studio_lib.cinema.build.Path',side_effect=lambda x:Path(d)/x if x=='.ce-cache/cinema-voice' else Path(x)),patch('studio_lib.cinema.build.edge_tts.Communicate',FlakyTTS),patch('studio_lib.cinema.build.asyncio.sleep') as wait,patch('studio_lib.cinema.build.subprocess.check_output',return_value=b'5.0'):
                plan={'mechanism':'hand_generator','beats':[{'action':a,'say':f'Why does {a} move?'} for a in ('machine','input','crank','shaft','generator','induction','load','payoff')]}
                result=asyncio.run(voice(plan,Path(d)))
                again=asyncio.run(voice(plan,Path(d)))
        self.assertEqual(result['requests'],9);self.assertEqual(again['requests'],0);self.assertEqual(len(calls),9);wait.assert_called_once_with(10)
