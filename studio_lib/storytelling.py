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

STRAIGHT TO THE POINT (owner rule 2026-11-24): the speaker never greets, introduces the video, or signs off. No "okay", "so", "hey", "welcome", "today", "let's", "imagine", "have you ever" in the first beat; no "that's how", "and that's it", "now you know", "thanks", "see you" in the last beat. Never narrate the screen or the animation itself: no "the cutaway plate returns", "the explanation concludes", "this model/animation/video", "we now see". Also never say cutaway, cover, illustrated, simplified, "no part moves" or "the cover closes": say what the real parts do and why it matters (a held beat is a still fact about the object, never "nothing moves now"). Talk about the real object and what its parts do, as a person who loves the subject would tell a friend. The opening question must be about the first thing that happens, and every beat must keep answering it in order. Beat 1 starts with the concrete hook itself. The last beat ends on the real payoff fact and stops. Sound like an excited, confident expert: short, vivid, specific.

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
 if re.match(r"\s*(okay|ok|so|hey|hi|well|welcome|today|let'?s|imagine|have you ever|did you know)\b",str(lines[0]),re.I):result.append('beat 0: no greeting or warm-up; start straight with the concrete hook')
 if re.search(r"(that'?s (how|it|all|why)|now you know|thanks|thank you|see you|in (summary|conclusion)|so there you have)",str(lines[-1]),re.I):result.append('last beat: no sign-off; end on the real payoff fact')
 for i,line in enumerate(lines):   # fragments like "Of interlock." are not sentences (owner review 2026-11-24)
  t=str(line).strip()
  if len(t.split())<6 or not t[:1].isupper() or t[-1:] not in '.?!' or re.match(r'(of|and|but|or|to|with|from|by|in|on|at|as|for)\b',t,re.I):result.append('beat %d: must be a complete sentence of at least 6 words, not a fragment'%i)
 if any(re.search(r'(plate returns|explanation (concludes|ends)|this (animation|video|model|demo)|as the explanation|returns as the)',str(line),re.I) for line in lines):result.append('Do not narrate the screen or animation (plate returns, explanation concludes, this model); describe the real object and its parts')
 if any(re.search(r'\b(cutaway|illustrated|simplified|no part moves|nothing moves|(the )?cover (lifts|closes|opens)|sealing the system)\b',str(line),re.I) for line in lines):result.append('Do not narrate the screen (cutaway, cover, illustrated, simplified, nothing moves); say what the real parts do')
 if any(re.search(r'\b(recognizable|authored engineering fixture|this controlled test)\b',str(line),re.I) for line in lines):result.append('Use audience-facing explanation, not fixture or production descriptions')
 links=sum(bool(re.search(r'\b(so|because|as|when|until|if|while|therefore|instead|once|allows?|prevents?|means|lets|keeps|causes?|makes|releases?|controls?|lifts?|raises?|lowers?|pushes|pulls?|drives?|turns?|rotates?|reduces?|blocks?|stops?|opens?|closes?|connects?|aligns?|forces?|passes|reopening|pivoting|raising|turning|guiding|shrinking|reducing|lifting|lowering|rotating|pushing|pulling|closing|opening|blocking|freeing|letting|allowing|keeping)\b',str(line),re.I)) for line in lines[1:])
 if links<3:result.append('Explain at least three visible cause-and-effect links; do not list parts')
 normalized=[re.sub(r'\W+',' ',str(line).lower()).strip() for line in lines]
 if len(set(normalized))!=len(normalized):result.append('Repeated narration does not advance the explanation')
 result.extend(narration_errors(plan))
 return result
