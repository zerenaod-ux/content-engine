import json,tempfile,unittest
from pathlib import Path
from studio_lib.topic_guard import require_new,reserve,duplicate,signature
class TopicGuardTests(unittest.TestCase):
    def setup_root(self,d):
        p=Path(d);(p/'history.json').write_text(json.dumps([{'topic':'How turning a handle lights a lamp'}]+[{'topic':f'Unrelated topic {i}'} for i in range(100)]));(p/'videos.json').write_text('[]');return p
    def test_old_topics_still_block_and_titles_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.setup_root(d)
            with self.assertRaises(ValueError):require_new('Why turning a handle lights a lamp',p)
            (p/'videos.json').write_text('[{"title":"How a Hydraulic Lift Multiplies Force"}]')
            with self.assertRaises(ValueError):require_new('How a hydraulic lift multiplies force',p)
    def test_reservation_blocks_other_runs_but_allows_its_owner(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.setup_root(d);reserve('Why solar cells need contacts',p,'run-a')
            require_new('Why solar cells need contacts',p,'run-a')
            with self.assertRaises(ValueError):require_new('Why solar cells need contacts',p,'run-b')
            reserve('Why solar cells need contacts',p,'run-a')
            self.assertEqual(len(json.loads((p/'topic-ledger.json').read_text())),1)
    def test_bad_history_never_silently_resets_memory(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):require_new('How a pump works',Path(d))
            p=self.setup_root(d);(p/'history.json').write_text('broken')
            with self.assertRaises(ValueError):require_new('How a pump works',p)
    def test_failed_attempt_is_not_completed_video(self):
        self.assertEqual(duplicate('How thermal contact transfers heat',[{'topic':'How a pump draws water'}]),'')
if __name__=='__main__':unittest.main()
