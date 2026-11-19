"""Shared generation policy for original causal visual explanations.

This is an authoring contract, not evidence that finished pixels were inspected.
"""
POLICY_VERSION = 'causal-visible-explanation-v1'
WRITING_RULES = """
EXPLANATION STYLE: Build one connected causal story, not a parts catalogue.
Open with a concrete problem, surprising result or useful question. Show what
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
