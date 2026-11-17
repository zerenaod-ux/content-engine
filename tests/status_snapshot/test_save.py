import base64,importlib.util,io,json,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('snapshot',Path('publish/save_status_snapshot.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def item(at,sha):return {'sha':sha,'content':base64.b64encode(json.dumps({'checked_at':at}).encode()).decode()}
class SnapshotTests(unittest.TestCase):
 def test_conflict_rereads_sha_and_only_updates_status_path(self):
  calls=[];gets=[item('2026-11-17T10:00:00+00:00','a'),item('2026-11-17T11:00:00+00:00','b')]
  def request(method,path,data=None):
   calls.append((method,path,data))
   if method=='GET':return gets.pop(0)
   if len(calls)==2:raise urllib.error.HTTPError('https://example.invalid',409,'conflict',{},io.BytesIO())
   return {'ok':True}
  with patch.object(module.time,'sleep'):self.assertTrue(module.save({'checked_at':'2026-11-17T12:00:00+00:00','read_only':True},request))
  self.assertEqual(calls[-1][2]['sha'],'b');self.assertTrue(all(x[1].startswith(module.PATH) for x in calls))
 def test_old_snapshot_never_replaces_newer_data(self):
  calls=[]
  def request(method,path,data=None):calls.append(method);return item('2026-11-17T13:00:00+00:00','new')
  self.assertFalse(module.save({'checked_at':'2026-11-17T12:00:00+00:00','read_only':True},request));self.assertEqual(calls,['GET'])
