import copy,json,os,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from studio_lib import durable_topics as durable

class DurableTopicTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.before=Path.cwd();os.chdir(self.tmp.name)
  self.env=patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GH_TOKEN':'test-only','GITHUB_RUN_ID':'42','GITHUB_RUN_ATTEMPT':'1'});self.env.start()
 def tearDown(self):self.env.stop();os.chdir(self.before);self.tmp.cleanup()
 def test_reservation_rereads_and_preserves_other_writers_after_conflict(self):
  original={'topic':'How a rotating screw moves its guided nut','owner':'7'}
  latest=[];writes=[]
  def read(path,default):return (copy.deepcopy(latest) if path==durable.LEDGER else []),'sha'
  def write(path,data,sha,message):
   writes.append(copy.deepcopy(data))
   if len(writes)==1:
    latest.append(original);raise urllib.error.HTTPError('url',409,'conflict',{},None)
   latest[:]=data
  Path('data/scenes').mkdir(parents=True)
  with patch.object(durable,'read_document',side_effect=read),patch.object(durable,'write_document',side_effect=write),patch.object(durable.time,'sleep'):
   durable.reserve_remote('How a pump moves water through valves','42')
  self.assertIn(original,latest);self.assertEqual(len(latest),2)
 def test_duplicate_and_changed_owner_topic_are_rejected_without_writing(self):
  for row in [{'topic':'How a pump moves water through valves','owner':'7'},{'topic':'How a screw moves its nut','owner':'42'}]:
   with patch.object(durable,'read_document',side_effect=lambda path,default:([row] if path==durable.LEDGER else [],'sha')),patch.object(durable,'write_document') as write:
    with self.assertRaises(ValueError):durable.reserve_remote('How a pump moves water through valves','42')
    write.assert_not_called()
 def test_record_delta_retains_concurrent_records_and_is_idempotent(self):
  baseline={p:[] for p in durable.PATHS};durable.BASE.write_text(json.dumps(baseline))
  for p in durable.PATHS:Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text('[]')
  Path(durable.PATHS[1]).write_text(json.dumps([{'tag':'new','topic':'new topic'},{'tag':'new','topic':'new topic'}]))
  remote={durable.PATHS[0]:[],durable.PATHS[1]:[{'tag':'other','topic':'concurrent topic'}]}
  def read(path,default):return copy.deepcopy(remote[path]),'sha'
  def write(path,data,sha,message):remote[path]=copy.deepcopy(data)
  with patch.object(durable,'read_document',side_effect=read),patch.object(durable,'write_document',side_effect=write):durable.save_records();durable.save_records()
  self.assertEqual([r['tag'] for r in remote[durable.PATHS[1]]],['other','new'])
 def test_missing_history_never_resets_the_remote_memory(self):
  with patch.object(durable,'read_document',return_value=(None,None)),patch.object(durable,'write_document') as write:
   with self.assertRaises(ValueError):durable.refresh_history()
   write.assert_not_called()
 def test_resume_requires_a_failed_trusted_job_and_one_original_reservation(self):
  source={'head_branch':'main','name':'scene-factory','conclusion':'failure'}
  with patch.object(durable,'github',return_value=source),patch.object(durable,'rows',return_value=([{'topic':'How a pump moves water','owner':'7'}],'sha')):
   topic,owner=durable.resume_topic('7')
  self.assertEqual(owner,'7');self.assertEqual(durable.reservation_owner(topic),'7')
  with patch.object(durable,'github',return_value={**source,'conclusion':'success'}):
   with self.assertRaises(ValueError):durable.resume_topic('7')
