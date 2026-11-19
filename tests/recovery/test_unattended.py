import copy,unittest
from unittest.mock import patch
from studio_lib import unattended as u
class Unattended(unittest.TestCase):
 def fixtures(self):
  row={'tag':'ce-fixture','video':'https://example.invalid/media.mp4','generation_origin':{'event':'schedule','run_id':'123','attempt':1,'event_sha':'abc','source_ref':'main','manual_media_edits':False},'production_evidence':{'policy':'unattended-proof-v1','novelty_policy':'original-idea-and-visuals-v1','errors':[],'owner_approved':False,'width':1080,'height':1920,'duration':50,'alignment_revision':'causal-component-actions-v4','render_policy':'native-studio-1080-v1','media_sha256':'a'*64,'voice':'am_fenrir','voice_policy':'how-it-ticks-narrator-v2'}}
  run={'id':123,'event':'schedule','name':'scene-factory','head_branch':'main','head_sha':'abc','status':'completed','conclusion':'success','run_attempt':1}
  return row,run
 def test_real_completed_schedule_can_be_verified(self):
  row,run=self.fixtures();self.assertEqual(u.verify_row(row,run),[])
 def test_manual_push_or_rerun_never_proves_scheduled_generation(self):
  for mode in ('manual','rerun','unfinished','stale-code'):
   row,run=self.fixtures()
   if mode=='manual':run['event']='push';row['generation_origin']['event']='push'
   elif mode=='rerun':run['run_attempt']=2
   elif mode=='unfinished':run['status']='in_progress'
   else:row['production_evidence']['alignment_revision']='old'
   self.assertTrue(u.verify_row(row,run))
 def test_catchup_requires_bot_dispatch_and_producer_flag(self):
  row,run=self.fixtures();run['event']='workflow_dispatch';row['generation_origin'].update(event='workflow_dispatch',automatic_slot=True)
  run['actor']={'login':'owner'};self.assertTrue(u.verify_row(row,run))
  run['actor']={'login':'github-actions[bot]'};self.assertEqual(u.verify_row(row,run),[])
 def test_review_lookup_checks_all_pages_including_closed_cards(self):
  row,run=self.fixtures();card={'number':456,'state':'closed','body':row['tag']+' '+row['video']}
  def api(path):
   if path.startswith('actions/runs/'):return run
   if path.endswith('page=1'):return [{'number':i,'body':'unrelated'} for i in range(100)]
   return [card]
  with patch.object(u,'read_document',side_effect=[([row],None),({},None)]),patch.object(u,'github',side_effect=api),patch.object(u,'write_document'):
   self.assertEqual(u.observe()['studio_issue'],456)

 def test_completed_daily_quota_defers_real_proof_to_next_day(self):
  import datetime
  now=datetime.datetime.fromisoformat('2026-11-19T17:30:00-06:00')
  self.assertEqual(u.expected_start({'business_day':'2026-11-19','ready_today':5,'daily_target':3},now),'2026-11-20T03:05:00-06:00')
