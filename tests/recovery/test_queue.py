import unittest
from studio_lib.service_queue import transition
class QueueTests(unittest.TestCase):
 def test_active_lease_excludes_other_worker(self):
  state,ok=transition({},'voice','full',1,100);self.assertTrue(ok)
  other,ok=transition(state,'voice','short',0,101);self.assertFalse(ok);self.assertEqual(other['leases']['voice']['owner'],'full')
 def test_expired_lease_recovers_and_waiting_short_has_priority(self):
  state={'leases':{'ai':{'owner':'dead','until':10}},'waiters':[{'service':'ai','owner':'short','priority':0,'seen':20}]}
  state,ok=transition(state,'ai','full',1,21);self.assertFalse(ok)
  state,ok=transition(state,'ai','short',0,22);self.assertTrue(ok);self.assertEqual(state['leases']['ai']['owner'],'short')
 def test_render_and_other_services_are_not_globally_serialized(self):
  state,_=transition({},'voice','full',1,100)
  state,ok=transition(state,'ai','short',0,101);self.assertTrue(ok)
 def test_polling_preserves_original_arrival_order(self):
  state={'leases':{'ai':{'owner':'active','until':15}},'waiters':[]}
  state,_=transition(state,'ai','first',1,1)
  state,_=transition(state,'ai','second',1,2)
  state,ok=transition(state,'ai','first',1,16)
  self.assertTrue(ok);self.assertEqual(state['leases']['ai']['owner'],'first')
