"""Shared generation policy for original causal visual explanations.

This is an authoring contract, not evidence that finished pixels were inspected.
"""
POLICY_VERSION = 'causal-visible-explanation-v2'
WRITING_RULES = """
EXPLANATION STYLE: Build one connected causal story, not a parts catalogue.
The first spoken beat must be one concrete problem or useful question ending with a question mark. Do not open by saying an object sits on a table. Explain at least three distinct causal links using natural varied language, rather than listing components. Show what
prevents the result, introduce the supported mechanism that addresses it, explain
its visible action and consequence, then connect the next supported step to a
clear final payoff. Make each step answer why the previous step matters.
Use problem -> solution -> consequence where the actual topic supports it;
do not invent a new problem, extra machine or historical sequence to fit a formula.
Use original everyday language, short energetic clauses and varied transitions.
Do not copy the reference's wording, catchphrase, numbers or repeated address.
Keep the engine's exact action order, safety constraints and measured duration.

VISIBLE CAUSE AND EFFECT: Every narrated physical action must name the actual
part, material or process in that beat's supplied action facts. Its matching
movement or change must be visible during the corresponding spoken clause:
the part turns, material flows, a connection closes, or an illustrated transfer
advances. A moving camera, caption, static label or unexplained glow is not
evidence of mechanism action. State what moves, what drives it and what changes.
Introduce the whole supported object before its internals when the contract
provides those views; never claim an opening, cutaway or hidden part the renderer
does not actually expose. A genuinely static identification beat can explain a
fixed part without inventing movement. Clearly distinguish schematic invisible
effects from visible physical objects. Preserve factual limits and no-free-energy
rules. Prefer a concise supported explanation over narration padded to fill time.
Do not promise that these writing instructions alone verify rendered motion.
""".strip()

# This is a bounded authoring gate; component kinematics and pixel checks remain
# independent evidence, rather than treating these writing checks as a render.
def errors(plan):
 import re
 from studio_lib.action_contracts import narration_errors
 result=[];beats=plan.get('beats',[])
 if len(beats)!=8:return ['A causal short needs its eight supported actions']
 lines=[b.get('say','') for b in beats]
 if not isinstance(lines[0],str) or not lines[0].strip().endswith('?'):result.append('beat 0: open with one concrete problem or useful question ending with ?')
 if any(re.search(r'\b(recognizable|authored engineering fixture|this controlled test)\b',str(line),re.I) for line in lines):result.append('Use audience-facing explanation, not fixture or production descriptions')
 links=sum(bool(re.search(r'\b(so|because|as|when|until|if|while|therefore|instead|once|allows?|prevents?|means|lets|keeps|causes?|makes|releases?|controls?)\b',str(line),re.I)) for line in lines[1:])
 if links<3:result.append('Explain at least three visible cause-and-effect links; do not list parts')
 normalized=[re.sub(r'\W+',' ',str(line).lower()).strip() for line in lines]
 if len(set(normalized))!=len(normalized):result.append('Repeated narration does not advance the explanation')
 result.extend(narration_errors(plan))
 return result
