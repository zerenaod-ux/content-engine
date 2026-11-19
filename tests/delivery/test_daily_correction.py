import unittest
from deliver_daily_correction import guard,updated_rows
class CorrectionTests(unittest.TestCase):
 def test_owner_choices_and_closed_cards_block_replacement(self):
  for state,labels in [('closed',[]),('open',[{'name':'ce-approve'}]),('open',[{'name':'ce-skip'}])]:
   with self.assertRaises(ValueError):guard({'state':state,'labels':labels,'body':'ce-20261119-0327'},'ce-20261119-0327')
  guard({'state':'open','labels':[],'body':'ce-20261119-0327'},'ce-20261119-0327')
 def test_same_entry_keeps_original_and_other_videos(self):
  rows=[{'tag':'target','video':'old'},{'tag':'other','video':'untouched'}]
  result=updated_rows(rows,'target','new',123)
  self.assertEqual(len(result),2);self.assertEqual(result[0]['previous_versions'],['old'])
  self.assertEqual(result[1],rows[1]);self.assertEqual(rows[0]['video'],'old')
  self.assertEqual(updated_rows(result,'target','new',123),result)
 def test_ambiguous_or_missing_entry_cannot_be_invented(self):
  for rows in [[],[{'tag':'target'},{'tag':'target'}]]:
   with self.assertRaises(ValueError):updated_rows(rows,'target','new',123)
if __name__=='__main__':unittest.main()
