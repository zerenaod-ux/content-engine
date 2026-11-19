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
