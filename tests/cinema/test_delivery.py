"""Review delivery retries preserve history and never create approval decisions."""
import base64,io,json,os,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('GITHUB_REPOSITORY','example/repo')
os.environ.setdefault('GH_TOKEN','test-placeholder')
os.environ.setdefault('SOURCE_RUN','123')
from studio_lib.cinema import deliver
class DeliveryTests(unittest.TestCase):
    def test_index_conflict_rereads_and_keeps_other_entries(self):
        one={'sha':'a','content':base64.b64encode(b'[{"tag":"one"}]').decode()}
        two={'sha':'b','content':base64.b64encode(b'[{"tag":"one"},{"tag":"concurrent"}]').decode()}
        conflict=urllib.error.HTTPError('https://example.invalid',409,'conflict',{},io.BytesIO())
        with patch.object(deliver,'get',side_effect=[one,two]),patch.object(deliver,'api',side_effect=[conflict,{'ok':True}]) as api,patch.object(deliver.time,'sleep'):
            deliver.put_file('index',b'','main',lambda prior:prior+[{'tag':'new'}])
        body=api.call_args.args[2]
        self.assertEqual(body['sha'],'b')
        self.assertEqual([x['tag'] for x in json.loads(base64.b64decode(body['content']))],['one','concurrent','new'])
    def test_untrusted_or_failed_source_is_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as d:
            old=Path.cwd();os.chdir(d)
            try:
                p=Path('incoming');p.mkdir()
                (p/'result.json').write_text(json.dumps({'manual_script_or_video_edits':False,'owner_approved':False}))
                (p/'plan.json').write_text(json.dumps({'mechanism':'wind_turbine','title':'How This Turbine Generates Useful Electrical Power'}))
                (p/'video.mp4').write_bytes(b'x'*100001)
                run={'conclusion':'failure','head_branch':'studio-cinematic-proof','head_repository':{'full_name':deliver.REPO}}
                with patch.object(deliver,'api',return_value=run),patch.object(deliver,'put_file') as write:
                    with self.assertRaises(ValueError):deliver.main()
                    write.assert_not_called()
            finally:os.chdir(old)
if __name__=='__main__':unittest.main()
