import json,tempfile,unittest
from pathlib import Path
from studio_lib.quality_gate import seal,require_seal
class OutputGateTests(unittest.TestCase):
 def prepare(self,p):
  (p/'video.mp4').write_bytes(b'encoded-test-placeholder')
  (p/'plan.json').write_text('{}')
  (p/'narration-critique.json').write_text('{"errors":[]}')
  (p/'audio-review.json').write_text(json.dumps({'errors':[],'integrated_lufs':-16,'true_peak_dbfs':-1.5,'independent_asr_word_error_rate':0}))
 def test_missing_evidence_never_passes(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):require_seal(Path(d),'short')
   with self.assertRaises(ValueError):seal(Path(d),'short',{'duration':50,'width':720,'height':1280})
 def test_changed_media_and_changed_reports_are_blocked(self):
  for name in ('video.mp4','audio-review.json','plan.json'):
   with tempfile.TemporaryDirectory() as d:
    p=Path(d);self.prepare(p);seal(p,'short',{'duration':50,'width':720,'height':1280});require_seal(p,'short');(p/name).write_text('changed')
    with self.assertRaises(ValueError):require_seal(p,'short')
 def test_failed_audio_or_narration_contract_is_not_sealed(self):
  for name in ('audio-review.json','narration-critique.json'):
   with tempfile.TemporaryDirectory() as d:
    p=Path(d);self.prepare(p);(p/name).write_text('{"errors":["failed"]}')
    with self.assertRaises(ValueError):seal(p,'short',{'duration':50,'width':720,'height':1280})
 def test_native_finish_requires_its_evidence_and_real_dimensions(self):
  for mode in ('missing','wrong_dimensions','valid'):
   with tempfile.TemporaryDirectory() as d:
    p=Path(d);self.prepare(p);(p/'plan.json').write_text('{"render_policy":"native-studio-1080-v1"}')
    if mode!='missing':(p/'render-quality-checks.json').write_text('{"policy":"native-studio-1080-v1","width":1080,"height":1920,"errors":[]}')
    media={'duration':50,'width':720 if mode=='wrong_dimensions' else 1080,'height':1280 if mode=='wrong_dimensions' else 1920}
    if mode=='valid':
     seal(p,'short',media);self.assertIn('render-quality-checks.json',require_seal(p,'short')['hashes'])
    else:
     with self.assertRaises(ValueError):seal(p,'short',media)
