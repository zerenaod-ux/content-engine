import unittest
from review_lib.decisions import tag_from_url,video_for,file_decision
class CinematicTags(unittest.TestCase):
    def test_approved_cinematic_card_can_be_filed(self):
        tag='ce-20261117-0857-cinema-44051234755'
        url='https://cdn.jsdelivr.net/gh/zerenaod-ux/content-engine@'+'a'*40+'/videos/'+tag+'.mp4'
        card={'number':42,'title':'How It Ticks: Why Direct-Drive Needs No Gearbox','body':'Watch: '+url,'html_url':'https://github.com/zerenaod-ux/content-engine/issues/42'}
        video={'tag':tag,'video':url,'title':'Why Direct-Drive Needs No Gearbox'}
        self.assertEqual(video_for(card,[video]),video)
        index,event=file_decision({'items':[]},card,video,'saved','123-1')
        self.assertEqual(index['items'][0]['folder'],'saved')
        self.assertEqual(event['tag'],tag)
    def test_mismatched_foreign_or_malformed_urls_still_fail(self):
        for url in ('https://evil.example/videos/ce-20261117-0857-cinema-44051234755.mp4','https://cdn.jsdelivr.net/gh/other/repo@gh-pages/videos/ce-20261117-0857.mp4','https://cdn.jsdelivr.net/gh/zerenaod-ux/content-engine@gh-pages/videos/ce-20261117-0857-cinema-bad.mp4'):
            self.assertIsNone(tag_from_url(url))
    def test_ordinary_video_names_remain_supported(self):
        self.assertEqual(tag_from_url('https://cdn.jsdelivr.net/gh/zerenaod-ux/content-engine@gh-pages/videos/ce-20261113-2105.mp4'),'ce-20261113-2105')
