import unittest
from studio_lib import storytelling as S

def plan(first,last,mid=None):
    b=[{'say':'Why does a zipper stay shut?'}]+[{'say':'Step %d because the slider pulls teeth so they lock.'%i} for i in range(6)]+[{'say':last}]
    b[0]['say']=first
    if mid:b[3]['say']=mid
    return {'mechanism':'x','beats':b}

class StraightToPointTests(unittest.TestCase):
    def test_greeting_rejected(self):
        self.assertTrue(any('no greeting' in e for e in S.errors(plan('Okay, so why does a zipper stay shut?','The teeth lock tight.'))))
    def test_signoff_rejected(self):
        self.assertTrue(any('no sign-off' in e for e in S.errors(plan('Why does a zipper stay shut?',"And that's how a zipper works."))))
    def test_direct_passes_these_checks(self):
        e=S.errors(plan('Why does a zipper stay shut?','Interlocked teeth hold the cloth together.'))
        self.assertFalse(any('greeting' in x or 'sign-off' in x or 'narrate the screen' in x for x in e))
    def test_screen_narration_rejected(self):
        e=S.errors(plan('Why does a zipper stay shut?','The cutaway plate returns as the explanation concludes.'))
        self.assertTrue(any('narrate the screen' in x for x in e))
if __name__=='__main__':unittest.main()
