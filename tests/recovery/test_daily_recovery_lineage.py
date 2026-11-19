import base64,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib import durable_topics as durable,novelty
class RecoveryLineageTests(unittest.TestCase):
 def test_failed_continuation_is_verified_without_allowing_completed_media(self):
  old=Path.cwd();topic='How a float valve controls a tank'
  history=[{'topic':topic,'failed':True,'record_run':'202'}]
  ledger=[{'topic':topic,'owner':'101','mechanism':'float_valve'}]
  def rows(path,*a,**k):return (ledger if path==durable.LEDGER else history),'sha'
  def github(path,*a,**k):
   if path.startswith('actions/runs/'):
    return {'head_branch':'main','name':'scene-factory','conclusion':'failure','head_sha':'child-sha'}
   return {'content':base64.b64encode(b'resume 101\n').decode()}
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_RUN_ID':'303'}),patch.object(durable,'rows',side_effect=rows),patch.object(durable,'github',side_effect=github):
   try:
    os.chdir(d);self.assertEqual(durable.resume_topic('101'),(topic,'101'))
    self.assertTrue(novelty.pending_owner(history[0],'101'))
    completed=dict(history[0],state='created',media_sha256='encoded')
    self.assertFalse(novelty.pending_owner(completed,'101'))
    self.assertFalse(novelty.pending_owner(dict(history[0],topic='Different project'),'101'))
   finally:os.chdir(old)
 def test_an_unrelated_failed_run_does_not_get_a_recovery_exception(self):
  old=Path.cwd();topic='How a float valve controls a tank'
  def rows(path,*a,**k):return ([{'topic':topic,'owner':'101'}] if path==durable.LEDGER else [{'topic':topic,'failed':True,'record_run':'202'}]),'sha'
  def github(path,*a,**k):
   if path.startswith('actions/runs/'):return {'head_branch':'main','name':'scene-factory','conclusion':'failure','head_sha':'child'}
   return {'content':base64.b64encode(b'auto\n').decode()}
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_RUN_ID':'303'}),patch.object(durable,'rows',side_effect=rows),patch.object(durable,'github',side_effect=github):
   try:
    os.chdir(d);durable.resume_topic('101');self.assertFalse(novelty.pending_owner({'topic':topic,'failed':True,'record_run':'202'},'101'))
   finally:os.chdir(old)
