import os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib import hook_intro as h

def _clip(path,seconds=8):
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=360x640:rate=30:duration=%d'%seconds,'-f','lavfi','-i','sine=duration=%d'%seconds,'-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(path)],check=True)

class HookIntroTests(unittest.TestCase):
    def test_command_takes_middle_zoomed_teaser_then_full_video(self):
        c=' '.join(h.command('in.mp4','out.mp4',40.0))
        self.assertIn('trim=start=18.750:duration=2.5',c);self.assertIn('eval=frame',c);self.assertIn('concat=n=2',c)
    def test_real_file_gets_hook_and_is_longer(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'CE_HOOK_INTRO':'on'}):
            d=Path(d);src=d/'in.mp4';_clip(src)
            self.assertTrue(h.deliver(src,d/'out.mp4'))
            self.assertLess(abs(h._duration(d/'out.mp4')-(h._duration(src)+h.HOOK_SECONDS)),0.3)
    def test_failure_delivers_original(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'CE_HOOK_INTRO':'on'}):
            d=Path(d);src=d/'bad.mp4';src.write_bytes(b'not a video')
            self.assertFalse(h.deliver(src,d/'out.mp4'));self.assertEqual((d/'out.mp4').read_bytes(),b'not a video')
    def test_wordless_uses_foley_audio(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'CE_HOOK_INTRO':'on'}):
            d=Path(d);src=d/'in.mp4';_clip(src,6)
            wav=d/'foley.wav';subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','anoisesrc=d=6:r=24000','-ac','1',str(wav)],check=True)
            self.assertTrue(h.deliver_wordless(src,wav,d/'o-wordless.mp4'));self.assertTrue((d/'o-wordless.mp4').exists())
            self.assertFalse(h.deliver_wordless(src,d/'none.wav',d/'x.mp4'))
    def test_hook_is_off_by_default(self):
        env={k:v for k,v in os.environ.items() if k!='CE_HOOK_INTRO'}
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,env,clear=True):
            d=Path(d);src=d/'a.mp4';src.write_bytes(b'x')
            self.assertFalse(h.deliver(src,d/'b.mp4'));self.assertEqual((d/'b.mp4').read_bytes(),b'x')
if __name__=='__main__':unittest.main()
