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

class CooldownTests(unittest.TestCase):
 def test_shared_provider_reset_is_honored_and_never_shortened(self):
  import os
  from unittest.mock import patch
  from studio_lib.service_queue import cooling_down,remember_cooldown
  state={'leases':{'voice':{'owner':'active','until':500}},'waiters':[],'cooldowns':{'provider.example':300}}
  with patch.dict(os.environ,{'CE_SHARED_SERVICES':'1'}),patch('studio_lib.service_queue.read_document',return_value=(state,'sha')),patch('studio_lib.service_queue.write_document') as write:
   self.assertTrue(cooling_down('provider.example',200));self.assertFalse(cooling_down('provider.example',400))
   remember_cooldown('provider.example',250)
  saved=write.call_args.args[1];self.assertEqual(saved['cooldowns']['provider.example'],300);self.assertEqual(saved['leases']['voice']['owner'],'active')
