import unittest
from studio_lib.recovery import classify_failure
class RetryTests(unittest.TestCase):
 def test_temporary_failures_get_a_wait_and_bounded_resume(self):
  for message in ('NoAudioReceived','ServiceUnavailable HTTP 429','ServiceBusy'):
   r=classify_failure(message,1);self.assertTrue(r['retryable']);self.assertIsNotNone(r['next_retry_at'])
   self.assertFalse(classify_failure(message,4)['retryable'])
 def test_invalid_content_and_oversized_requests_are_not_blindly_retried(self):
  for message in ('ServiceUnavailable HTTP 413 request too large','unsupported topic','script failed bounded validation'):
   self.assertFalse(classify_failure(message,1)['retryable'])
 def test_no_repeat_hold_is_not_retried_as_a_service_outage(self):
  result=classify_failure('Permanent no-repeat policy: visual setup already used; HTTP 429 earlier in the log',1)
  self.assertFalse(result['retryable']);self.assertEqual(result['state'],'held_for_novelty')

class WatcherTests(unittest.TestCase):
 def test_only_due_failed_authorized_jobs_are_resumed(self):
  import time
  from unittest.mock import patch
  from studio_lib.recovery import watch
  record={'retryable':True,'next_retry_at':time.time()-1,'run_id':'123','kind':'short'}
  for branch,name,status,result,expected in [('studio-cinematic-proof','Cinematic system comparison (not posted)','completed','failure',False),('main','scene-factory','completed','failure',True),('main','how-it-ticks-publisher','completed','failure',False),('main','scene-factory','completed','success',False),('unknown','scene-factory','completed','failure',False)]:
   calls=[]
   def api(path,method='GET',body=None):
    calls.append((path,method))
    if path.startswith('contents/studio_lib/novelty.py'):return {'sha':'policy'}
    if path.startswith('contents/'):return [{'type':'file','path':'data/operations/jobs/123.json'}]
    if method=='POST':return {}
    return {'id':123,'head_branch':branch,'name':name,'status':status,'conclusion':result,'run_attempt':1,'head_sha':'policy-source'}
   with patch('studio_lib.recovery.github',side_effect=api),patch('studio_lib.recovery.read_document',return_value=(dict(record),'sha')),patch('studio_lib.recovery.write_document'):watch()
   self.assertEqual(any(method=='POST' for _,method in calls),expected)
