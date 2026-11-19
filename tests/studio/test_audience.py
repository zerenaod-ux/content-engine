import unittest
from unittest.mock import patch
from studio_lib import audience
class Audience(unittest.TestCase):
 def test_missing_connection_never_fakes_retention(self):
  with patch.dict('os.environ',{},clear=True),patch.object(audience,'request') as api:
   r=audience.collect();self.assertFalse(r['available']);self.assertIsNone(r['average_view_percentage']);api.assert_not_called()
 def test_foreign_channel_is_rejected_before_analytics(self):
  with patch.dict('os.environ',dict(YT_CLIENT_ID='fixture',YT_CLIENT_SECRET='fixture',YT_REFRESH_TOKEN_HOWITTICKS='fixture')),patch.object(audience,'request',side_effect=[{'access_token':'fixture'},{'items':[{'id':'correct'}]},{'items':[{'id':'other'}]}]) as api:
   r=audience.collect();self.assertFalse(r['available']);self.assertEqual(r['state'],'identity_or_report_error');self.assertEqual(api.call_count,3)
 def test_omitted_metrics_are_not_zero(self):
  with self.assertRaises(ValueError):audience.rows({'columnHeaders':[{'name':'views'}],'rows':[[100]]})
 def sample(self):
  import datetime
  from studio_lib.audience import CHANNEL_ID,HANDLE
  return {'available':True,'channel_id':CHANNEL_ID,'handle':HANDLE,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'videos':[{'video':'a','views':1217,'averageViewDuration':22,'averageViewPercentage':47.74},{'video':'b','views':1082,'averageViewDuration':17,'averageViewPercentage':45.28}]}
 def test_verified_retention_is_evidence_not_generated_content(self):
  r=audience.guidance(self.sample());self.assertEqual(r['qualified_videos'],2);self.assertAlmostEqual(r['median_average_view_percentage'],46.51)
  self.assertIn('no-repeat',r['writing_instruction']);self.assertNotIn('topic',r)
 def test_foreign_stale_and_tiny_samples_cannot_steer_writing(self):
  import datetime
  for mode in ('foreign','stale','tiny'):
   r=self.sample()
   if mode=='foreign':r['channel_id']='another-channel'
   elif mode=='stale':r['checked_at']=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=3)).isoformat()
   else:r['videos'][1]['views']=3
   self.assertIsNone(audience.guidance(r))
 def test_owner_connected_snapshot_is_usable_without_exporting_credentials(self):
  with patch.dict('os.environ',{'GH_TOKEN':'fixture'},clear=True),patch.object(audience,'read_document',return_value=(self.sample(),None)),patch.object(audience,'request') as api:
   report=audience.collect();self.assertTrue(report['available']);self.assertEqual(report['state'],'available_snapshot');self.assertFalse(report['automatic_refresh']);api.assert_not_called()
