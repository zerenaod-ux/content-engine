import unittest
from studio_lib.cinema.auto_topic import candidate_valid
class AutomaticTopicTests(unittest.TestCase):
    def test_past_component_paraphrase_and_wrong_subject_are_rejected(self):
        rows=[{'title':'Why a Seesaw Lifts With Less Force'}]
        self.assertTrue(candidate_valid({'topic':'How a lever raises loads','mechanism':'lever_balance'},rows))
        self.assertTrue(candidate_valid({'topic':'How a nuclear reactor works','mechanism':'resistive_circuit'},[]))
        self.assertEqual(candidate_valid({'topic':'How a resistor circuit carries current','mechanism':'resistive_circuit'},rows),'')
