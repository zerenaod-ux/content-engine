import asyncio,hashlib,io,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import AsyncMock,patch
import numpy as np
import edge_tts
from studio_lib import cpu_voice,audio

class CpuVoiceTests(unittest.TestCase):
 def test_production_synthesis_refuses_the_owner_computer(self):
  with patch.dict(os.environ,{},clear=True),patch.object(cpu_voice,'engine') as engine:
   with self.assertRaises(ValueError):cpu_voice.render({'beats':[]},'unused')
   engine.assert_not_called()
 def test_model_asset_requires_expected_size_and_digest(self):
  data=b'known public fixture';asset=('fixture.onnx',(hashlib.sha256(data).hexdigest(),len(data)))
  with tempfile.TemporaryDirectory() as d,patch.dict(cpu_voice.ASSETS,[asset]),patch.object(cpu_voice.urllib.request,'urlopen',return_value=io.BytesIO(b'bad')):
   with self.assertRaises(ValueError):cpu_voice.asset(asset[0],d)
   self.assertFalse(Path(d,asset[0]).exists());self.assertFalse(list(Path(d).glob('*.part')))
 def test_all_fallback_lines_use_one_stock_voice_and_cache_valid_samples(self):
  class FakeModel:
   def __init__(self):self.calls=[]
   def create(self,text,**kw):self.calls.append((text,kw));return np.sin(np.arange(24000)*.1).astype(np.float32)*.3,24000
  model=FakeModel();spec={'beats':[{'say':'First authored unit test line.','action':'question'},{'say':'Second authored unit test line.','action':'payoff'}]}
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch.object(cpu_voice,'engine',return_value=model) as load:
   first=cpu_voice.render(spec,d);second=cpu_voice.render(spec,d)
   self.assertEqual(load.call_count,1);self.assertEqual(second['cached_lines'],2)
   self.assertTrue(all(x[1]['voice']=='am_fenrir' for x in model.calls));self.assertEqual([x[0] for x in model.calls],[b['say'] for b in spec['beats']])
   self.assertEqual(first['provider'],'kokoro-onnx-cpu')
 def test_outage_keeps_the_same_narrator_without_provider_switch(self):
  spec={'beats':[{'say':'Unit test fixture','seconds':6,'action':'question'}]}
  with tempfile.TemporaryDirectory() as d,patch.object(audio,'_cpu_narrate',new_callable=AsyncMock,side_effect=[TimeoutError('temporary'),{'voice':'am_fenrir'}]) as fixed:
   with self.assertRaises(TimeoutError):asyncio.run(audio.narrate(spec,d,d))
   result=asyncio.run(audio.narrate(spec,d,d))
   self.assertEqual(result['voice'],'am_fenrir');self.assertEqual(fixed.call_count,2)
 def test_cached_timeline_requires_current_identity_and_policy(self):
  from studio_lib.voice_policy import matches,VOICE,PROVIDER,VERSION
  self.assertFalse(matches({'voice':'am_michael','voice_provider':PROVIDER,'voice_policy':VERSION}))
  self.assertFalse(matches({'voice':VOICE,'voice_provider':PROVIDER,'voice_policy':'old'}))
  self.assertTrue(matches({'voice':VOICE,'voice_provider':PROVIDER,'voice_policy':VERSION}))
