from studio_lib import storytelling as S
def plan(first,last):
    b=[{'say':'Why does a zipper stay shut?'}]+[{'say':'Step %d because the slider pulls teeth so they lock.'%i} for i in range(6)]+[{'say':last}]
    b[0]['say']=first;return {'mechanism':'x','beats':b}
def test_greeting_rejected():
    assert any('no greeting' in e for e in S.errors(plan('Okay, so why does a zipper stay shut?','The teeth lock tight.')))
def test_signoff_rejected():
    assert any('no sign-off' in e for e in S.errors(plan('Why does a zipper stay shut?',"And that's how a zipper works.")))
def test_direct_passes_these_checks():
    e=S.errors(plan('Why does a zipper stay shut?','Interlocked teeth hold the cloth together.'))
    assert not any('greeting' in x or 'sign-off' in x for x in e)

def test_screen_narration_rejected():
    p=plan('Why does a zipper stay shut?','Interlocked teeth hold the cloth together.')
    p['beats'][3]['say']='A simplified cutaway lifts the slider plate because the teeth lock so it holds.'
    assert any('Do not narrate the screen' in e for e in S.errors(p))
    p['beats'][7]['say']='The cutaway plate returns as the explanation concludes.'
    assert any('Do not narrate the screen' in e for e in S.errors(p))
