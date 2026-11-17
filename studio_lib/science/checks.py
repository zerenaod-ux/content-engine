"""Concrete narration/pose mismatches observed in generated component outputs."""
import re

def lever_narration_errors(plan):
    errors=[]
    for beat in plan.get('beats',[]):
        text=beat.get('say','').lower();action=beat.get('action')
        if re.search(r'\barrows?\b.{0,30}\b(push|pushes|press|presses|applies|apply)\b',text):
            errors.append('The input weight applies force; arrows only illustrate its direction, never physically push.')
        if re.search(r'\b(swap|swaps|swapping|exchange|exchanging) positions\b|\bswitch sides\b',text):
            errors.append('Lever ends remain on their original sides; do not say they swap positions.')
        if action in ('transfer','result','limits','payoff') and re.search(r'\b(lifts|rises|moves upward|is rising|is lifting)\b',text):
            errors.append('After the change beat the lever holds still: say the load has risen or is raised, not that it is currently lifting.')
    return errors
