import copy,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from review_lib.decisions import decision_for,video_for,file_decision,save
from review_lib import process

VIDEO={'tag':'ce-20261113-2105','title':'Example','video':'https://cdn.jsdelivr.net/gh/zerenaod-ux/content-engine@gh-pages/videos/ce-20261113-2105.mp4'}
ISSUE={'number':6,'title':'Content Engine: Example','html_url':'https://github.com/zerenaod-ux/content-engine/issues/6','state':'open','labels':[{'name':'scene-review'},{'name':'ce-approve'}],'body':'Watch: '+VIDEO['video']}

class ReviewDecisionTests(unittest.TestCase):
    def test_only_content_engine_review_cards_have_decisions(self):
        self.assertEqual('saved',decision_for(ISSUE))
        self.assertIsNone(decision_for({**ISSUE,'pull_request':{}}))
        # Real pull_request object is nonempty; even empty PR marker must be ignored.
        self.assertIsNone(decision_for({**ISSUE,'labels':[{'name':'approve'}]}))
        both=copy.deepcopy(ISSUE);both['labels'].append({'name':'ce-skip'})
        with self.assertRaises(ValueError):decision_for(both)

    def test_release_and_phone_links_identify_same_stored_video(self):
        self.assertEqual(VIDEO,video_for(ISSUE,[VIDEO]))
        issue={**ISSUE,'body':'Watch: https://github.com/zerenaod-ux/content-engine/releases/download/ce-20261113-2105/ce-20261113-2105.mp4'}
        self.assertEqual(VIDEO,video_for(issue,[VIDEO]))
        with self.assertRaises(ValueError):video_for({**ISSUE,'body':'https://evil.example/ce-20261113-2105.mp4'},[VIDEO])
        with self.assertRaises(ValueError):video_for(ISSUE,[])

    def test_saved_and_delete_are_retained_and_reclassification_is_reversible(self):
        empty={'version':1,'items':[]}
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/'original.mp4';original.write_bytes(b'original')
            root=Path(d)/'folders'
            index,a=file_decision(empty,ISSUE,VIDEO,'saved','100-1',now='first');save(root,index,a)
            self.assertTrue(a['ready_for_future_publish']);self.assertFalse(a['publishing_enabled'])
            index,b=file_decision(index,ISSUE,VIDEO,'delete','101-1',now='second');save(root,index,b)
            self.assertFalse(b['ready_for_future_publish'])
            self.assertEqual('delete',index['items'][0]['folder'])
            self.assertTrue((root/a['record']).exists());self.assertTrue((root/b['record']).exists())
            self.assertEqual(b'original',original.read_bytes())
            same,event=file_decision(index,ISSUE,VIDEO,'delete','102-1')
            self.assertIsNone(event);self.assertEqual(index,same)
            self.assertEqual([],empty['items'])

    def test_old_decision_file_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            index,event=file_decision({'items':[]},ISSUE,VIDEO,'saved','100-1',now='first');save(d,index,event)
            event['title']='changed'
            with self.assertRaises(ValueError):save(d,index,event)

    def run_worker(self,push_ok):
        closed=[];commands=[];pushed=[]
        def api(path,method='GET',body=None):
            if path=='/labels':return {}
            if path.startswith('/issues?'):return [ISSUE] if 'ce-approve' in path else []
            if method=='PATCH':
                self.assertTrue(pushed,'card must not close until remote folder commit succeeds')
                self.assertEqual('saved',json.loads(Path('data/scenes/review/index.json').read_text())['items'][0]['folder'])
                closed.append(path);return {}
            return ISSUE
        def git(args,**kwargs):
            commands.append(args)
            if args[:3]==['git','diff','--cached']:return SimpleNamespace(returncode=1)
            if args==['git','push']:
                if push_ok:pushed.append(True)
                return SimpleNamespace(returncode=0 if push_ok else 1)
            return SimpleNamespace(returncode=0)
        before=Path.cwd()
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'GITHUB_RUN_ID':'100','GITHUB_RUN_ATTEMPT':'1'}):
            os.chdir(d);Path('data/scenes').mkdir(parents=True);Path('data/scenes/videos.json').write_text(json.dumps([VIDEO]))
            try:
                with patch.object(process,'api',side_effect=api),patch.object(process.subprocess,'run',side_effect=git):
                    if push_ok:process.main()
                    else:
                        with self.assertRaises(RuntimeError):process.main()
            finally:os.chdir(before)
        return closed,commands

    def test_folder_commit_precedes_card_close(self):
        closed,commands=self.run_worker(True)
        self.assertEqual(['/issues/6'],closed)
        self.assertEqual(1,commands.count(['git','push']))

    def test_failed_push_leaves_review_card_open(self):
        closed,commands=self.run_worker(False)
        self.assertEqual([],closed);self.assertEqual(3,commands.count(['git','push']))

if __name__=='__main__':unittest.main()
