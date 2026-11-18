# Recovery and quality handover — November 17, 2026

## Verified and deployed
- Daily short production now coordinates AI/voice access using separate expiring shared-service leases. Waiting shorts take priority; rendering holds no service lease.
- A main-branch recovery coordinator runs after relevant jobs and every 15 minutes. It resumes only eligible temporary generation failures, at most three retries after the first attempt. Publisher runs and successful runs are excluded.
- Live no-media recovery self-test intentionally failed attempt 1 and automatically passed attempt 2. This is proof of the recovery mechanism, not proof of a new video or universal reliability.
- Studio's existing Status card displays tracked production stage, attempt, report time, retry eligibility and content/configuration holds. Phone/laptop hosted layout checks passed with one How It Ticks card and no horizontal overflow.
- Studio prevents overlapping media within the page and coordinates supported other Studio tabs. No review decisions were changed.
- Legacy review-filing repair passed and five old cards closed after preserving their existing choices.

## Actual media results and failures
- Lever recovery produced 42.104 seconds and reached Studio, with 0% automated ASR word error. It remains explicitly NOT a richer-animation quality pass: simple lift and mostly static views. No human listening claim.
- Automatic topic proof selected hydraulic lift and produced 44.816 seconds with 0% automated ASR word error; delivered as Why Hydraulic Lift Raises Heavy Loads. Inspection rejected it as a new-topic proof because hydraulic lifts were already covered. The coverage parser missed the plural title. Its review card now states the failure; no owner decision was manufactured.
- Original full-video implementation is on the test branch: system-selected one-topic narration, 16 causal chapters, native 1280×720 procedural animation, 120–300 second gate and Studio delivery. It does not concatenate shorts. Initial supported geometry is rack-and-pinion and rotating lead screw only.
- Full attempt 1 stopped because the main reservation ledger had not been initialized. The missing ledger was initialized without resetting existing history or video indexes.
- A later request exceeded the free model's input limit because raw history metadata was sent. Model requests now contain every unique past topic/title, while repeat validation still checks the full records. No history is truncated.
- Another full attempt failed on a missing branch delivery dependency; that dependency was added.
- The coordinated full attempt stopped because two chapters missed 30–44 words. Inspection also found the selected question compared pinion diameters the renderer does not vary. No original full video has yet completed, passed inspection or replaced the scheduled compilation builder.

## Current corrections and proof status
- Targeted model repair now changes only invalid sections and rejects attempts to rewrite unrequested chapters. It preserves topic, title, hook, action order, cameras and valid narration.
- Unshown diameter/lead comparisons are rejected during topic selection. Supported scope explicitly uses a single fixed diameter/lead.
- Hydraulic lift/press/jack plural forms now resolve to the same component, with a regression test against the observed repeated title.
- Provider cooldowns can be shared between jobs and honor known Retry-After values, avoiding immediate quota competition. This is finite capacity, not unlimited cloud service.
- Local checks: 50 cinematic tests, 9 full-format tests, 8 recovery tests pass. Those do not replace actual video inspection.
- New system-selected short/full proofs are triggered by this commit. They still need actual output, visual/narration inspection and confirmed Studio delivery. Never call them done from unit tests or run submission alone.

## What remains
- Finish and inspect the new short proof and an original full video. Improve detail if they remain too schematic.
- Only after full proof should the legacy scheduled compilation path be replaced; old releases and decisions stay intact.
- Detailed direct YouTube analytics for How It Ticks is not integrated; Buffer metrics can lag. Publishing freshness must be read from its report time, not assumed current.
- Doodles GPU warning measures workflow elapsed time rather than actual billed GPU usage; accurate GPU accounting remains separate.
- How It Ticks automatic approval remains OFF. Publishing remains limited to owner-approved Saved items. No generated proof is auto-approved.


## Continued proof update — November 17, evening Chicago

The short narration-length repair passed script and voice generation and is rendering in the cloud; encoded inspection and delivery are pending. The expanded full run selected a lead-screw subject but stopped on title and section-length validation. A further fix preserves draft narration, repairs title/hook metadata separately and repairs invalid sections in batches of at most four. A fresh full proof is active. Latest local suites: 51 cinematic, 12 full-format and 8 recovery tests pass. No new full-video output or aesthetic pass is claimed. The system still selects its topic; no hand-picked final subject or generated-script editing. All owner decisions remain intact, automatic approval stays off, and the legacy scheduled compilation is not yet replaced.
