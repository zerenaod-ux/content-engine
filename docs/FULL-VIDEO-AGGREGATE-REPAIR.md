# Full-video correction in progress — November 18, 2026

Priority: finish the original full-video pipeline before starting unrelated improvements.

Root cause verified: when every narration chapter satisfied its individual length rule but the aggregate script was below 430 words or above 650, targeted repair selected no chapters and repeatedly returned the unchanged draft. The repair now asks the model to expand the four shortest chapters or shorten the four longest, preserving the others. No generated script is edited by hand. Eighteen full-format tests pass, including the aggregate-only regression.

Current proof: https://github.com/zerenaod-ux/content-engine/actions/runs/44262874938 — automatic selection, writing, narration and rendering started. Do not interpret submission or tests as completion. Required evidence: measured 120–300 seconds, native landscape, one topic, visible connected motion, matching narration, audio/media checks, technical evidence seal and Studio delivery. Owner quality approval remains separate.

Fallbacks: AI-writing router uses configured provider fallbacks, availability checks, shared cooldowns and bounded recovery. Voice currently uses retries and retained lines, not a second provider. The script-length failure was not caused by lack of API capacity.

Unfinished work must stay recorded until its evidence is verified; switching to UI or documentation is not completion. Latest thermal correction was owner-approved; it does not prove original full-video completion or arbitrary-topic support. Auto-approval remains off.
