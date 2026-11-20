import json,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
from studio_lib.audio_mastering import mastering_args
class EncodedPeakTests(unittest.TestCase):
 @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg is required for the real encoder regression')
 def test_aac_output_retains_headroom_after_transient_input(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/'audio.m4a'
   source='aevalsrc=0.4*sin(2*PI*440*t)+0.55*lt(mod(t\,0.7)\,0.015):s=44100:d=5'
   subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',source,*mastering_args(),'-c:a','aac','-b:a','160k',str(target)],check=True)
   result=subprocess.run(['ffmpeg','-hide_banner','-i',str(target),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
   measure=json.loads(re.search(r'\{\s*"input_i"[\s\S]*?\}',result.stderr)[0])
   self.assertLessEqual(float(measure['input_tp']),-.8)
   self.assertGreaterEqual(float(measure['input_i']),-20)
   self.assertLessEqual(float(measure['input_i']),-12)

 def test_master_removes_measurable_dc_imbalance(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/'clean.wav'
   subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','aevalsrc=0.06+0.2*sin(2*PI*440*t):s=24000:d=2',*mastering_args(),str(target)],check=True)
   result=subprocess.run(['ffmpeg','-hide_banner','-i',str(target),'-af','astats=reset=0','-f','null','-'],capture_output=True,text=True,check=True)
   offsets=re.findall(r'DC offset: ([-0-9.]+)',result.stderr)
   self.assertTrue(offsets);self.assertLess(abs(float(offsets[-1])),.001)
