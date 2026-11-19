import datetime,unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from studio_lib import visual_quality as q,electric_relay as relay,snap_thermostat as thermostat,clothespin as peg,factory_slots as slots

class VisualFinish(unittest.TestCase):
 def test_native_detail_required(self):
  with self.assertRaises(ValueError):q.finish(Image.new('RGB',(720,1280)))
  self.assertEqual(q.finish(Image.new('RGB',(1440,2560))).size,(1080,1920))
 def test_lighting_preserves_legibility(self):
  face=[(0,0,0),(1,0,0),(1,1,0)]
  lit=q.lit_color(face,(180,120,70),(0,-10,10))
  self.assertTrue(all(0<=x<=255 for x in lit));self.assertGreater(min(lit),45)
 def test_relay_contacts_touch_without_overlap(self):
  self.assertAlmostEqual(np.linalg.norm(np.array(relay.physical(relay.CLOSED,1)['moving'])-relay.FIXED),.2,places=8)
  self.assertEqual(relay.physical(0,0)['powered'],0)
 def test_thermostat_pin_tracks_rigid_contact_strip(self):
  tl={'beats':[{'start':i*6,'end':(i+1)*6} for i in range(8)]}
  for t in np.linspace(0,47.99,100):
   p=thermostat.state(t,tl);a=p['angle']
   self.assertAlmostEqual(2.5+1.1*np.tan(a)-.065/np.cos(a),p['pin_top'],places=7)
   self.assertGreaterEqual(p['gap'],-1e-8)
 def test_peg_stops_at_fabric_and_keeps_preload(self):
  self.assertAlmostEqual(peg.inner_gap(peg.STOP),peg.THICKNESS,places=10)
  self.assertGreater(peg.STOP,0);self.assertLess(peg.STOP,peg.OPEN)
  pts=np.array([[-2,0,.3],[1,0,.2]])
  for a in (0,peg.OPEN,peg.STOP):
   transformed=peg.transform(pts,1,a)
   self.assertAlmostEqual(np.linalg.norm(transformed[0]-transformed[1]),np.linalg.norm(pts[0]-pts[1]))

class DailySlots(unittest.TestCase):
 def at(self,text):return datetime.datetime.fromisoformat(text)
 def test_slot_boundaries(self):
  for clock,due in [('03:04',0),('03:05',1),('11:05',2),('19:05',3)]:
   d=slots.decision(self.at('2026-11-20T'+clock+':00-06:00'),[],['fresh']);self.assertEqual(d['due_slots'],due)
 def test_counts_deliveries_on_chicago_day(self):
  rows=[{'tag':'ce-20261120-0200'},{'tag':'ce-20261120-0800'},{'tag':'ce-20261120-0800'},{'tag':'ce-full-20261120-0900'}]
  self.assertEqual(slots.decision(self.at('2026-11-20T12:00:00-06:00'),rows,['fresh'])['ready_today'],1)
 def test_no_pool_or_active_never_dispatches(self):
  now=self.at('2026-11-20T20:00:00-06:00')
  self.assertFalse(slots.decision(now,[],[])['should_build'])
  self.assertFalse(slots.decision(now,[],['fresh'],True)['should_build'])
 def test_dst_keeps_local_generation_slots(self):
  self.assertEqual(slots.decision(self.at('2026-07-20T08:05:00+00:00'),[],['fresh'])['due_slots'],1)
 def test_staged_policy_never_calls_dispatch(self):
  with patch.object(slots,'read_document',return_value=({'enabled':False},None)),patch.object(slots,'github') as gh:
   self.assertFalse(slots.watch()['enabled']);gh.assert_not_called()
 def test_catchup_waits_for_recovery_and_never_publishes(self):
  result=dict(business_day='2026-11-20',should_build=True,reason='due')
  def read(path,default):
   if path=='publish/factory-policy.json':return {'enabled':True},None
   if path==slots.STATE:return {},None
   return {'jobs':{'daily-short':{'state':'waiting_to_resume','retryable':True}}},None
  with patch.object(slots,'read_document',side_effect=read),patch.object(slots,'snapshot',return_value=result),patch.object(slots,'write_document'),patch.object(slots,'github') as gh:
   self.assertFalse(slots.watch()['should_build']);gh.assert_not_called()
 def test_catchup_reserves_before_request_and_caps_attempts(self):
  result=dict(business_day='2026-11-20',should_build=True,reason='due')
  events=[]
  def read(path,default):return ({'enabled':True} if path=='publish/factory-policy.json' else {},None)
  with patch.object(slots,'read_document',side_effect=read),patch.object(slots,'snapshot',return_value=result),patch.object(slots,'write_document',side_effect=lambda *a:events.append('reserve')),patch.object(slots,'github',side_effect=lambda *a:events.append(a)):
   slots.watch();self.assertEqual(events[0],'reserve');self.assertEqual(events[1][0],'actions/workflows/content-engine.yml/dispatches');self.assertEqual(events[1][2]['inputs'],{'topic':'auto','automatic_slot':'true'})
