import unittest
from studio_lib.cinema.topic_memory import prompt_history
class TopicMemoryTests(unittest.TestCase):
 def test_all_topics_are_retained_without_raw_evidence_or_links(self):
  rows=[{'topic':'Topic '+str(i),'title':'Title '+str(i),'video':'https://example.test/'+('x'*1000),'attempts':['y'*10000]} for i in range(500)]
  result=prompt_history(rows+rows)
  self.assertEqual(len(result),1000);self.assertIn('Topic 499',result);self.assertIn('Title 0',result)
  self.assertNotIn('https://',str(result))
