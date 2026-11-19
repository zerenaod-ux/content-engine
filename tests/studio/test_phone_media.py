import hashlib,subprocess,tempfile,unittest
from pathlib import Path
from studio_lib.phone_media import prepare
class PhoneMedia(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.folder=tempfile.TemporaryDirectory();cls.root=Path(cls.folder.name);cls.source=cls.root/'source.mp4'
  subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=navy:s=128x224:r=10','-f','lavfi','-i','sine=frequency=440:sample_rate=24000','-t','0.5','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(cls.source)],check=True)
 @classmethod
 def tearDownClass(cls):cls.folder.cleanup()
 def test_small_encoded_media_is_delivered_byte_exact(self):
  target=self.root/'phone.mp4';r=prepare(self.source,target)
  self.assertTrue(r['original_preserved']);self.assertEqual(self.source.read_bytes(),target.read_bytes());self.assertEqual(r['source_sha256'],r['delivered_sha256'])
 def test_unreadably_small_transport_budget_is_held(self):
  with self.assertRaisesRegex(ValueError,'cannot preserve readable'):prepare(self.source,self.root/'refused.mp4',limit=1)
