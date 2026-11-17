# Current state — three supported mechanisms, 2026-11-16

Three automatic component videos and their cached reuses completed on GitHub. They remain editorially unapproved. Their observed narration/visual mismatches have been corrected in system code; a fresh proof of the corrected source is being submitted. Thirty-one local tests pass. A draft adapter is ready for the existing Studio review/release path, with checks-warn requiring owner review. Main is not merged or deployed, generation remains paused, posting remains off, and arbitrary-topic support is not claimed. No owner input or credentials are currently required.

# Latest state — three-mechanism library, 2026-11-16

First limited component pipeline produced a bridge video on GitHub and proved fast cached reuse. It is not editorially approved: narration timing/production-language defects were found and documented, and the original was shown unchanged. The latest director contract fixes those classes of defect. The library now contains bridge, photovoltaic cell and piston pump components, with 25 local engineering tests passing. A three-topic cloud proof is being submitted; output quality remains pending. Arbitrary topics are not supported, production remains unchanged, and no owner input is pending.

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

## 2026-11-16 — first component result and three-mechanism library (append-only)

The first tested-component pilot completed successfully on GitHub: run 43975740383 at 2b5bb03e7c7c798b6babfd756062bb4ffd03344b produced a 48.028-second bridge video in 161.815 seconds total. Its model ledger recorded four HTTP requests, four responses, zero failures, 8.137 seconds service time and 5,470 reported tokens. The same generated plan/narration/render was reused with no model credentials in 3.421 seconds. This is a limited component-pipeline result, not arbitrary-topic proof or editorial acceptance. Inspection found spoken camera instructions and a claim that bridge motion began during a static pivot beat; these defects were reported to the owner. The original result was shown unchanged and retained. The system contract now prohibits production/camera narration and binds the pivot beat to its static state; no generated plan was manually edited.

At the owner's request, the procedural library now also contains a photovoltaic cell/panel with a closed DC circuit and load, and a single-acting piston pump with coupled chamber volume and check valves. A registry gives each component its factual/action contract and primary reference. The automatic director selects the supported mechanism from a topic and generates narration/hook/bounded camera preferences; it rejects unsupported topics. Solar cell behavior is an explicitly enlarged illustrative cutaway; the lamp is a DC load, not an inverter model. The pump is not a full fluid simulation. Twenty-five local tests pass, including valve exclusivity, intake/delivery volume direction, load timing and rendered evidence visibility. Local preview sheets were inspected and framing was enlarged before cloud trials.

A new explicit three-topic proof workflow will test bridge, solar and pump and a credential-free reuse for each. Those new library videos have not yet been produced or editorially accepted. Production, paused schedule, review decisions and publishing remain unchanged. Resumable checkpoints survive reruns; no overnight retry scheduler has been enabled.

## 2026-11-16 — solar automatic result and targeted provider repair (append-only)

Three-mechanism run 43978789117 at 5498117df70bb091ddafae6c76f9a1c5d754454d selected the photovoltaic component and completed a 48.062-second solar video in 123.633 seconds; saved-stage reuse without model credentials took 2.077 seconds. This is a technical result pending visual/narration review, not owner approval. Pump is still running at this entry. Bridge's revised run retained its generated director plan but stopped when the provider refused JSON validation and fallbacks were unavailable/limited.

The provider adapter now makes one bounded plain-response retry for the observed JSON-mode refusal, uses documented low reasoning effort for GPT-OSS, and gives the compact narration critique sufficient response room. Twenty-six local tests pass, including the exact observed JSON-refusal recovery. A targeted bridge retry restores the existing library checkpoints instead of discarding valid generated work. No generated scene/plan is hand-edited. Production and Studio remain unchanged.

## 2026-11-16 — targeted pump recovery (append-only)

The three-topic batch completed: solar technically succeeded and passed credential-free cached reuse; bridge and pump stopped at the same provider JSON-mode refusal followed by unavailable/limited fallbacks. Their valid generated plans remain checkpointed. The bridge recovery run 43979521549 is active with the bounded provider fix. The single-component proof workflow now accepts an explicit supported topic; its next queued run resumes the pump checkpoint using that same fix. The solar output is retained for review. No generated plans are manually edited and no production behavior changes.

## 2026-11-16 — three component outputs, editorial corrections and review adapter (append-only)

All three supported mechanisms have now produced automatic cloud videos using engine-owned geometry/action order and model-written plans/narration, without manual generated-plan edits. Solar run 43978789117: 48.062 s output, 123.633 s build, 2.077 s cached reuse. Bridge recovery 43979521549: 48 s output, 153.438 s resumed build, 2.920 s cached reuse. Pump recovery 43979740298: 48 s output, 77.257 s resumed build, 1.945 s cached reuse. These are technical results, not editorial approvals or arbitrary-topic proof. Original artifacts and plans are preserved. Solar was shown to the owner unchanged.

Inspection found remaining spoken/visual mismatches: solar claimed visible wiring was absent; the bridge announced a static close-up; the pump described a filling reservoir whose level was fixed. The system now rejects camera/close-up production narration and false wiring-absence claims, enforces a How/Why title, and couples source/receiver levels to intake/delivery with a normalized volume balance. This is an illustrative hydraulic diagram, not a calibrated fluid simulation. Checkpoints now use per-component contract versions and migrate valid prior plans, avoiding unrelated cache invalidation. No generated plan/video is manually patched. Thirty-one local tests pass, including release/review adapter behavior and preserving existing outputs. A fresh three-topic proof of this exact source remains necessary.

The draft production adapter uses the existing release, videos index and Studio review-card path and emits checks-warn for owner review, never automatic approval. The draft scene-factory workflow uses CPU component generation and removes unused generative GPU/browser dependencies; its schedule remains commented/paused. Main is NOT merged/deployed. No existing Studio cards, review decisions, accounts, platform publishing or other systems are changed. New app progress UI and automatic overnight retries are not implemented. Unsupported topics fail explicitly rather than receiving unrelated footage.
