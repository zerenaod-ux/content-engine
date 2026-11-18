import unittest
from unittest.mock import Mock
from studio_lib.review_cards import find_by_marker
class RetainedReviewTests(unittest.TestCase):
 def test_existing_closed_card_beyond_first_page_is_found(self):
  card={'number':2,'state':'closed','body':'source-run: 123'}
  api=Mock(side_effect=[[{'body':'other'}]*100,[card]])
  self.assertEqual(find_by_marker(api,'review','source-run: 123'),card);self.assertEqual(api.call_count,2)
 def test_incomplete_or_overlarge_lookup_cannot_claim_no_card(self):
  with self.assertRaises(ValueError):find_by_marker(Mock(return_value={}), 'review','marker')
  with self.assertRaises(ValueError):find_by_marker(Mock(return_value=[{'body':''}]*100),'review','marker')
