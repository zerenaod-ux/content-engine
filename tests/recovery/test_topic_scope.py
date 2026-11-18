import unittest
from studio_lib.topic_scope import scope_error,require_supported

class ScopeTests(unittest.TestCase):
 def test_failed_daily_coating_topic_is_rejected_before_media(self):
  for text in ['Why photovoltaic cells use anti-reflective coatings','Why photovoltaic cells use anti‑reflective coatings']:
   with self.assertRaises(ValueError):require_supported(text)
 def test_supported_core_explanation_is_retained(self):
  self.assertEqual(scope_error('How a solar cell separates charge and powers a lamp'), '')
  self.assertEqual(scope_error('Why direct drive wind turbines need no gearbox'),'')
 def test_coating_claim_is_rejected_even_if_title_is_generic(self):
  self.assertTrue(scope_error('The surface coating reduces reflected light','photovoltaic_cell'))
 def test_known_other_mechanisms_are_not_substituted(self):
  for text in ['How a centrifugal pump moves water','How wind turbines change blade pitch','Why suspension bridges use cables']:
   self.assertTrue(scope_error(text))
