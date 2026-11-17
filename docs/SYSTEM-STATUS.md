# How It Ticks — current verified status
Updated November 17, 2026 (America/Chicago). This page supersedes older dated status claims; historical README entries are retained.

## Live system
- The tested-component pipeline is deployed on main. Four supported mechanism families: bascule bridge, photovoltaic cell/panel, single-acting piston water pump, direct-drive wind turbine. Arbitrary-topic animation is not supported.
- Seven new-style shorts and one long compilation were identified in release/review records. The index lists 35 short-video entries across old and new systems; it omits the newest long compilation. These counts are observations, not promises of future totals.
- Daily short generation is scheduled at 3:05 AM Chicago. A separate long-video workflow uses a day-of-month cron intended for alternating days; it joins existing shorts into a branded 16:9 compilation, rather than independently writing a long explanation.
- Automatic approval is OFF, explicitly requested and verified November 17. Existing already-approved videos are not revoked. New decisions require owner review.
- Publishing is ON for approved/Saved items. The latest inspected publisher run scheduled zero items; the inspected state contains no successful YouTube posting record for today. The YouTube channel itself was not directly verified.

## Verified playback and defects
- Latest short: “Why Direct-Drive Turbines Skip Gearboxes Efficiently,” approximately 48 seconds, 720x1280. Its direct video opened and playback advanced without a reported media error. This was sampled playback, not a complete scientific/narration/audio review.
- Latest long: “How Machines Work From the Inside,” approximately 3 minutes 19 seconds, 1920x1080. Its direct Pages link opened and played.
- Long generation run [completed with a hidden index-save failure](https://github.com/zerenaod-ux/content-engine/actions/runs/44008595270): release, phone copy and review card exist, but concurrent history/index changes caused a rebase conflict. The retry shell loop did not propagate that failure, so GitHub incorrectly marked the whole job successful. The long index entry and reuse bookkeeping need reconciliation, and save failures must fail visibly. No repair has been made in this documentation update.
- README opening sections and older histories describe earlier architectures/settings. Consult this page and actual workflow/configuration files for current state.

## Current cinematic upgrade — NOT deployed
The owner requested improvements after inspecting Zack D. Films reference Shorts. Two sampled references were [cup drop](https://www.youtube.com/shorts/quePIIHPDeY) and [Oreo twisting machine](https://www.youtube.com/shorts/QJqqRN6dssk). Visible observations: detailed 3D objects, tight framing, mechanism close-ups, short changing captions. Exact production software, staffing, full sound design and acoustic speaker characteristics were not established.

Implementation is in the draft [automatic cinematic wind-turbine comparison](https://github.com/zerenaod-ux/content-engine/pull/41), branch `studio-cinematic-proof`, source `3c7a1bc342cbf4a6ab5a647068e5a3a33b988053`. The [first cloud comparison](https://github.com/zerenaod-ux/content-engine/actions/runs/44051234755) is in progress at this update. No upgraded video has passed inspection yet.

| Item | Implemented system change | Evidence/status |
|---|---|---|
| 1. Story | Topic-driven original model script, direct opening, concrete actions and causal explanation, bounded validation and factual critique | Code submitted; generated story not yet inspected |
| 2. Visuals | Reusable Blender turbine with thick blades, bearings, brake, magnets, copper windings, tower/environment, studio lighting, shadows and cavity shading | Code submitted; first cloud render pending. Workbench is a fast illustrative renderer, not a photorealism claim |
| 3. Camera | Full-frame overview, rotor/shaft/generator/coil/load views, eased transitions and small push-ins driven by the measured narration timeline | Code submitted; actual framing pending inspection |
| 4. Speech | Original Andrew TTS voice, conversational script instructions, per-beat rate variation, measured durations and short pauses | Code submitted; reference audio was not acoustically matched or voice-cloned; generated delivery pending review |
| 5. Captions and sound | Up to three words per caption using actual synthesis WordBoundary metadata, escaped subtitle control text, ducked music/swishes and a switch click aligned to action | Three local tests pass for grouping, timestamp formatting and text handling; full audiovisual synchronization pending |
| 6. Automatic proof | GitHub generates script, voice, animation, captions, mix and final MP4 from a topic; retains raw scripts, measured timeline, diagnostic frames, Blender scene and provenance | Cloud run active. No manual script/video edits; no finished quality pass yet |

Five items are implemented in code; zero of six are fully verified in the upgraded finished video as of this update. Unit tests are not a visual, factual or audio-quality pass.

## Review checklist when output finishes
Inspect all eight action beats; verify that the spoken part is in view, rotor/shaft/magnets stay coupled, coils remain stationary, the opening is direct, the lamp switch and payoff match narration, and no critical object clips or disappears. Check word-caption timing, readability and safe margins; speech intelligibility, pauses, bed ducking and transient levels; full MP4 decoding and duration. Record measured build time, provider use, observed flaws and final source. If a flaw is found, change system code and rerun; never hand-edit the generated comparison to manufacture a pass.

The comparison workflow has read-only repository permissions and cannot publish, change owner review decisions, or turn approval on. Production renderer, generation schedule, other channels and posting settings are not changed by this experiment. Free cloud quotas remain finite.

## Next actions
1. Finish and inspect the automatic comparison; report each of the six items against actual evidence.
2. Correct any observed defects in the system, rerun boundedly, and preserve rejected outputs.
3. Show the finished comparison before applying the renderer broadly.
4. Separately repair the known long-video index/save failure. This remains outstanding.


## November 17 — Studio review delivery added during the comparison run
The owner clarified that every completed comparison must appear in Studio Review. A separate delivery workflow is now deployed on main: it listens for successful cinematic-comparison runs, validates their source/provenance, preserves the mobile MP4 in gh-pages and a release, merges the current video index with collision retries, and opens an idempotent checks-warn review card only after those saves succeed. It does not approve or publish. Automatic approval remains off. This is delivery integration, not deployment of the new renderer as the daily production default. Five local tests now pass: the three caption tests plus preserving concurrent index entries on retry and rejecting failed/untrusted source runs before writes. Delivery is not yet verified end to end because the first render is still running. No independent wake-up/failure-notification monitor is configured; status is being checked during the active task.


## 2026-11-17 — corrected hand-generator comparison delivered (append-only)

The system generated a fresh topic, “How a hand-cranked generator turns effort into light,” without manual generated-script or video edits. Earlier output 44066025188 passed audio tests but was rejected on inspection for stationary-core/cover narration errors; its Studio card is explicitly marked as needing correction. A subsequent script-only attempt 44068378801 was rejected before rendering. The writer now preserves valid lines during bounded repairs, allows stationary supporting bearings, and rejects offset-shaft, stationary-core torque, cover-direction, lamp-closes-circuit and pre-switch current claims.

Final cloud run 44068968307 completed successfully and produced 38.376 seconds in 579.878 seconds (about 9.7 minutes for the build). Script, encoded-frame samples across the sequence, caption intervals and independent audio transcript were inspected. The corrected explanation describes induced voltage with the switch open, then current through the lamp after closure. Forty-one caption groups have zero overlaps and do not cross beat boundaries. Speech is modestly faster (+26/+32 percent TTS settings, about 183 words/minute overall); coupled rotor/crank motion is about 15 percent faster than the previous cinematic version.

Encoded audio: -16.28 LUFS integrated loudness, -1.23 dB true peak, 2.56 percent independent ASR word error rate; full media decode passed. This is automated audio verification and transcript review, NOT a claim of human listening or subjective aesthetic approval. Eleven local tests pass. The cloud run passed its applicable tests and audio gate.

Delivery run 44070603413 succeeded. Studio card: https://github.com/zerenaod-ux/content-engine/issues/45 . Title: “How Turning a Handle Lights a Lamp 💡”. Its index entry exists and the immutable mobile MP4 returned HTTP 200 with video/mp4 and byte-range support. Original and rejected samples remain separate. Automatic approval is verified OFF. No approval or publishing action was taken. The cinematic renderer remains a tested comparison workflow on its branch, not the daily production default; owner review is still required before a broad rollout. The older long-video index defect remains separate and unresolved.
