# Accepted full-plan recovery

The engagement rerun exposed a recovery defect: a formerly accepted plan invalidated by one new check was discarded in favor of an older draft, and a valid draft was sent back through whole-script generation. That needlessly rewrote valid chapters and created a new length failure.

The accepted matching plan is now the repair seed even when one chapter needs correction. A valid matching draft goes directly to audit instead of regeneration. Semantic review is requested with zero-based section indices so only faulty sections are repaired. Two regression tests verify preservation of every unaffected accepted section and audit-only use of a valid draft. Twenty-eight full-format checks pass locally. The original source topic, voice cache and geometry correction are retained; actual corrected render remains pending.
