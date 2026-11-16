# Automatic animation studio — current handover, 2026-11-16

## Conclusion

NOT production-ready. No new fully automatic video has matched the owner-approved drawbridge. That reference video was authored in code; it must never be presented as a topic-only automatic success. There is no pending request for user input or credentials.

## Completed

- Authored drawbridge v2: owner reviewed it positively, with a remaining request for a natural full-water setting. Road gap and ship occlusion fixed, gear reference marks and close-up added. 53 seconds, 720x1280 at 30fps, 73.006-second corrected render plus 1.853-second audio assembly. The revision reused narration and made zero generation-service calls. Thirteen local demonstration checks pass.
- Separate general `studio_lib` prototype: fresh free-model scene descriptions; bounded data-only schema; persistent objects and rigid parent transforms; mesh/gear rendering; actual-geometry framing with eased shot transitions; full ground/water background; sampled part-removal visibility and fixed-camera movement checks; measured cached narration; normalized audio; at most three automatic candidates; retained provenance and diagnostics.
- Ten local engineering tests pass, plus Python compilation and a short encoder/decoder probe. Authored test fixtures are engineering checks, not automatic-video evidence.
- Draft change: https://github.com/zerenaod-ux/content-engine/pull/32 . Test branch `studio-automatic-proof`. Production workflow and paused schedule are unchanged.

## Fresh automatic evidence

1. First trial: https://github.com/zerenaod-ux/content-engine/actions/runs/43966869289 at `c756a69cf69e6cb298270a4e995bf0892fffba80`. Bridge, solar and pump all failed. Bridge exceeded the original object-count bound; solar used an unsupported motion field and missed narration/timing bounds; pump reached sampled rendering after an automatic repair but had invisible evidence parts and insufficient actual motion. Free-provider failures also prevented repairs. Artifacts preserve unedited candidates and ledgers. No qualifying narrated MP4.
2. Second trial: https://github.com/zerenaod-ux/content-engine/actions/runs/43967854149 at `4ba7ec4f6ec7622d44769bab018930ca45b3d689`. All three topics failed. Bridge and solar failed at provider rate/payload/response errors. Pump repeatedly generated invalid motion keys beyond the beat range and also hit provider errors during critique. The entire batch is finished. No qualifying video established.

## Further changes saved after the second trial started

- Compact the automatic critique to narration, geometry bounds, hierarchy, motion and gear parameters instead of sending all decorative mesh data again.
- Reuse an unchanged structurally valid candidate when retrying its critique; do not regenerate it just because the critique service failed.
- Retain sanitized provider error details to distinguish payload limits from temporary request limits.
- Add the already-configured Gemini Flash model family as another cloud fallback. Model names are discovered; no new account/key or paid service is introduced.
- Require an explicit proof trigger so saving code/documentation does not automatically spend free quotas on another batch.

These latest changes pass ten local tests but have NOT yet completed a fresh cloud trial. They are not a verified fix for output quality.

## Blockers

1. Automatic planning still produces invalid, hidden, static or physically wrong mechanisms. A model critique plus pixel checks does not prove scientific accuracy or audience appeal.
2. Free cloud providers have finite token/request allowances and transient failures; large geometry/critique requests have also failed. Some earlier error logs omit the response detail, so not every refusal is conclusively classified.
3. No fresh automatic video has passed editorial comparison with the drawbridge. No proof across varied topics, no reliable accepted-video throughput measurement, and no audience testing.
4. The experimental workflow only saves GitHub artifacts. It does not create Studio review cards or display generation progress in the phone app. Nothing new from these trials should be expected there.

## Next necessary verification

Run a bounded explicit trial of the latest source when useful quota is available; let the system repair its own generated scenes. Inspect the actual visuals and narration, keep failures, and only claim topic-only success if there were no manual generated-scene edits. Generalize with varied topics before proposing production rollout. Do not merge, re-enable the schedule, publish, alter other channels, create monitors/reminders, or silently substitute a manual sample for a failed automatic result. No trial is currently running, and no background retry or notification monitor has been scheduled.

All production work remains on GitHub/integrated cloud tools. The user's laptop is not part of production. No unlimited free cloud replacement has been verified. A local model would change that operating model and has not been installed or selected.

## Continued session: explicit third trial and motion-check refinement

Trial https://github.com/zerenaod-ux/content-engine/actions/runs/43973200928 was explicitly launched at source 26513de43f485919ccd2632a3992e053c4678912 after the owner asked to continue. It is running; no success is established. The compact critique, valid-stage reuse and Gemini fallback are included in that tested source. A subsequent local change samples several moments within a beat so a mechanism returning to its start is not falsely rejected as static. Eleven local tests pass. This last motion-check refinement is not included in the third trial's original source and still needs cloud verification. No manual generated scene edits have been made. The test remains outside Studio and production.

## 2026-11-16 — tested-component architecture after nine rejected trials (append-only)

The third raw-geometry batch 43973200928 is complete: bridge, solar and pump all failed. Nine topic trials across three batches produced no qualifying automatic video. Solar critique caught invented mechanical behavior in a photovoltaic explanation, showing a substantive planning failure beyond quotas. Provider limits/unavailable models also prevented repairs; one free provider reported its daily allowance exhausted. No paid credits were purchased.

The replacement pilot restricts the model to supported mechanism selection, fresh narration, hook and bounded camera preferences. A procedural bascule bridge component owns geometry, rigid coupling, gears, safety action order, continuous roadway and the full water setting; it reuses reviewed engine code, not a generated scene edited by hand. This first component supports bascule bridges only; arbitrary-topic support is explicitly false. It saves integrity-checked automatic director plans, measured narration and hashed rendered video for reuse after interruption. Unavailable models are skipped and Gemini catalog prefixes normalized. The pilot workflow tests a fresh run, then a zero-model-credential reuse run. Nineteen local engineering tests pass. Cloud execution and owner judgment of a newly generated component video remain pending. This is not a proven permanent fix or production rollout. Existing main workflow, paused schedule, publishing and Studio remain unchanged.

The next explicit trial is the tested-component pilot. Previous general-geometry trials are finished. There is no pending owner input. No automatic overnight scheduler has been enabled; saved stages resume on a subsequent pilot invocation/rerun. This remains an experimental branch.
