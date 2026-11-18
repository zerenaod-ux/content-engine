"""Existing release/review contract and failure behavior, no external writes."""
import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib.production import build,emit_review_files
class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.before=Path.cwd();os.chdir(self.tmp.name)
        # Explicit empty fixture history belongs only to this isolated test.
        # Real missing production history must continue to block generation.
        root=Path('data/scenes');root.mkdir(parents=True)
        for name in ('history.json','videos.json','topic-ledger.json'):(root/name).write_text('[]')
    def tearDown(self):os.chdir(self.before);self.tmp.cleanup()
    def fake_build(self,topic,work):
        work=Path(work);work.mkdir(parents=True)
        (work/'video.mp4').write_bytes(b'fixture-video')
        (work/'director-plan.json').write_text(json.dumps({'title':'How a Solar Cell Supplies Direct Current','mechanism':'photovoltaic_cell'}))
        (work/'timeline.json').write_text(json.dumps({'duration':48,'beats':[{'start':0,'end':48,'say':'Authored test fixture, not an automatic video.','action':'panel'}]}))
        (work/'component-checks.json').write_text(json.dumps({'errors':[]}))
    def test_completed_build_emits_legacy_review_contract_without_autoapproval(self):
        Path('topic.txt').write_text('How solar panels work\n')
        with patch('studio_lib.production.run',side_effect=self.fake_build):build('topic.txt','finished.mp4')
        self.assertTrue(Path('finished.mp4').exists());self.assertEqual(json.loads(Path('ce-checks.json').read_text())['verdict'],'warn')
        self.assertFalse(json.loads(Path('auto-scene.json').read_text())['owner_approved']);self.assertEqual(json.loads(Path('auto-scene.json').read_text())['mechanism'],'photovoltaic_cell')
    def test_failed_build_does_not_emit_video_or_review_verdict(self):
        Path('topic.txt').write_text('unsupported\n')
        with patch('studio_lib.production.run',side_effect=ValueError('unsupported component')):
            with self.assertRaises(ValueError):build('topic.txt','finished.mp4')
        self.assertFalse(Path('finished.mp4').exists());self.assertFalse(Path('ce-checks.json').exists())
    def test_existing_video_is_preserved(self):
        Path('topic.txt').write_text('topic');Path('finished.mp4').write_bytes(b'original')
        with self.assertRaises(FileExistsError):build('topic.txt','finished.mp4')
        self.assertEqual(Path('finished.mp4').read_bytes(),b'original')
