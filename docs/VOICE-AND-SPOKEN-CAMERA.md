# Clean narration and spoken-detail camera — November 19 feedback

Owner reports a distracting voice bed, rushed/unnatural English delivery and insufficient close-ups in the latest relay film. These changes affect future production only; existing videos, review decisions, originality history, schedules and publishing settings are preserved.

- Keep the fixed stock speaker am_fenrir; version the policy so cached older pacing cannot be silently reused.
- Reduce role speeds from +10–22% to +2–6%. Measured duration fitting still applies, with existing bounds; this does not promise human performance or solve every synthesis artifact.
- Remove generated background tones and switch effects from both daily/full and cinematic speech mixes. Silence in the source remains silence in the master. No new denoising/pitch manipulation is applied to speech.
- For component-based daily shorts, move smoothly into the tested part-specific shot, use 25% closer bounded mechanism framing, settle around the existing independent measured action cue, hold the explanation still and pull out for the whole-object payoff. Remove the unconditional push and side-to-side wobble. Cutaway and whole-object frames retain existing scale. Extremely early cues still require a minimum smooth transition; this is not guaranteed word-perfect noun tracking.
- Existing physical motion windows, narrative words and geometry remain unchanged. Other format camera paths are unchanged; this change does not claim universal object detection or multi-part within-sentence tracking.

Validation includes regression checks for no injected soundtrack, fixed identity/moderate rates, camera continuity, held framing, and wider context endpoints. A contact sheet is an engineering fixture, not a new topic/video or production proof. Cloud audio-only audition and shared checks should pass before rollout. Owner listening remains the final voice preference check. No existing film is regenerated to obtain proof.

## Measured branch evidence

262 local checks passed: 140 studio, 44 recovery, 55 cinematic and 23 original full-format. The relay engineering contact sheet was rendered and visually inspected: closer internals, held detail views and wider context endpoints. This is fixture evidence, not a recreated channel video or universal framing proof.

The free cloud audio-only audition [44664075274](https://github.com/zerenaod-ux/content-engine/actions/runs/44664075274) passed. Its 16.459-second WAV uses the same am_fenrir narrator and v3-clean policy for all four roles. The fixture created no topic, video or review card. Direct listening preference is still for the owner; no human-naturalness pass is claimed. Shared cloud regression run: [44664072216](https://github.com/zerenaod-ux/content-engine/actions/runs/44664072216). Production remains unchanged pending rollout of PR 63.

Owner requested alternative clearer, energetic speakers. A separate bounded audio-only fixture compares Michael, Adam and Heart with identical English text, speed, loudness and no background bed. This audition does not change the production narrator or create a channel video. Voice preference needs listening, not a numerical quality claim. The narrator-check workflow offers an explicit voice_options audition input; its default remains the fixed-narrator verification.
