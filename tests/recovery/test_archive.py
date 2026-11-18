import io,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import Mock
from studio_lib.delivery_archive import release_or_record
class ArchiveTests(unittest.TestCase):
 def test_existing_archive_is_not_recreated(self):
  api=Mock();self.assertEqual(release_or_record(api,Mock(return_value={'id':1}),'path',{}),{'id':1});api.assert_not_called()
 def test_permission_failure_is_explicit_and_not_a_claimed_release(self):
  error=urllib.error.HTTPError('https://example.test',403,'refused',{},io.BytesIO())
  with tempfile.TemporaryDirectory() as d:
   report=Path(d)/'archive.json';self.assertIsNone(release_or_record(Mock(side_effect=error),Mock(return_value=None),'path',{},report));self.assertIn('unavailable',report.read_text())
 def test_other_failures_still_stop(self):
  error=urllib.error.HTTPError('https://example.test',500,'server',{},io.BytesIO())
  with self.assertRaises(urllib.error.HTTPError):release_or_record(Mock(side_effect=error),Mock(return_value=None),'path',{})
