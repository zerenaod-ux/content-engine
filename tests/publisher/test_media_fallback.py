import unittest
from unittest.mock import patch,MagicMock
import ce_publisher as p
class PublisherMediaTests(unittest.TestCase):
 def test_explicit_rejection_switches_only_uncreated_post(self):
  inp={'assets':[{'video':{'url':'https://cdn.jsdelivr.net/gh/zerenaod-ux/content-engine@abc/videos/ce-20261118-1607.mp4'}}]}
  rejected={'data':{'createPost':{'message':'Invalid post: Video could not be read from its URL.'}}}
  success={'data':{'createPost':{'post':{'id':'created'}}}}
  with patch.object(p,'api',side_effect=[rejected,success]) as api,patch.object(p,'readable_pages_alternative',return_value='https://zerenaod-ux.github.io/content-engine/videos/ce-20261118-1607.mp4'),patch.object(p.time,'sleep'):
   self.assertEqual(p.create_approved_post(inp),success)
   self.assertIn('github.io',api.call_args.args[1]['input']['assets'][0]['video']['url'])
   self.assertIn('jsdelivr',inp['assets'][0]['video']['url'])
 def test_ambiguous_failure_and_success_are_never_retried(self):
  for result in [{'errors':[{'message':'unknown timeout'}]},{'data':{'createPost':{'post':{'id':'existing'}}}}]:
   with patch.object(p,'api',return_value=result) as api:
    self.assertEqual(p.create_approved_post({}),result);self.assertEqual(api.call_count,1)
 def test_alternative_requires_owned_media_and_video_response(self):
  self.assertIsNone(p.readable_pages_alternative('https://example.com/file.mp4'))
  response=MagicMock();response.__enter__.return_value=response;response.status=200;response.headers={'Content-Type':'text/html'}
  with patch.object(p.urllib.request,'urlopen',return_value=response):
   self.assertIsNone(p.readable_pages_alternative('https://cdn.jsdelivr.net/gh/zerenaod-ux/content-engine@abc/videos/ce-20261118-1607.mp4'))
if __name__=='__main__':unittest.main()
